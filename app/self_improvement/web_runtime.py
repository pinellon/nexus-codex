from __future__ import annotations

import json
import threading
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import app.settings_manager as settings_manager
from app.self_improvement.file_tracker import FileTracker
from app.self_improvement.git_guard import GitGuard
from app.self_improvement.nexus_mind import NexusMind
from app.self_improvement.proof_of_work import ProofOfWork
from app.self_improvement.score_engine import ScoreEngine


class MindRestartBridge:
    def __init__(self) -> None:
        self.pending_reason: str | None = None
        self.requested_at: str | None = None

    def request_restart(self, reason: str) -> None:
        self.pending_reason = reason
        self.requested_at = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

    def clear(self) -> None:
        self.pending_reason = None
        self.requested_at = None

    def needs_restart_after(self, changed_files: list[dict[str, Any]]) -> bool:
        critical = ["main.py", "app/core/", "app/voice/", "ui/"]
        for changed in changed_files:
            path = changed.get("path", "")
            if any(marker in path for marker in critical):
                return True
        return False


class WebNexusMindRuntime:
    SETTINGS_PATH = Path("data/mind_settings.json")
    PROOF_PATH = Path("data/nexus_proof.json")

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._cycle_lock = threading.Lock()
        self._mind: NexusMind | None = None
        self._logs: list[str] = []
        self._last_error: str | None = None
        self._cycle_active = False
        self._restart_bridge = MindRestartBridge()
        self._tracker = FileTracker()
        self._guard = GitGuard()
        self._score_engine = ScoreEngine(str(Path.cwd()))
        self._settings = self._load_settings()

    def _load_settings(self) -> dict[str, Any]:
        if self.SETTINGS_PATH.exists():
            try:
                loaded = json.loads(self.SETTINGS_PATH.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    loaded["mode"] = self._normalize_mode(loaded.get("mode", "supervisionado"))
                    return loaded
            except Exception:
                pass
        return {
            "directive": "",
            "auto_restart": False,
            "active": False,
            "mode": "supervisionado",
            "interval": 5,
        }

    def _save_settings(self) -> dict[str, Any]:
        self.SETTINGS_PATH.parent.mkdir(exist_ok=True)
        self.SETTINGS_PATH.write_text(json.dumps(self._settings, ensure_ascii=False, indent=2), encoding="utf-8")
        return dict(self._settings)

    def _ensure_mind(self) -> NexusMind:
        if self._mind is None:
            api_settings = settings_manager.load()
            self._mind = NexusMind(
                api_key=str(api_settings.get("openai_api_key", "") or ""),
                auto_mode=False,
                high_improvement=False,
                restart_mgr=self._restart_bridge,
            )
            self._mind._log = self._capture_log  # type: ignore[method-assign]
            self._apply_settings_to_mind()
        return self._mind

    def _autonomy_unlocked(self) -> bool:
        return bool(settings_manager.load().get("mind_allow_autonomous", False))

    def _normalize_mode(self, value: Any) -> str:
        mode = str(value or "supervisionado").strip().lower()
        if mode == "autonomo":
            mode = "autônomo"
        if mode not in {"supervisionado", "autônomo", "agressivo"}:
            mode = "supervisionado"
        if mode != "supervisionado" and not self._autonomy_unlocked():
            self._capture_log("🔒 Modos autônomo e agressivo ficam bloqueados até liberar a permissão mind_allow_autonomous.")
            return "supervisionado"
        return mode

    def _apply_settings_to_mind(self) -> None:
        if self._mind is None:
            return
        mode = self._normalize_mode(self._settings.get("mode", "supervisionado"))
        self._settings["mode"] = mode
        self._mind.auto_mode = mode != "supervisionado"
        self._mind.high_improvement = mode == "agressivo"
        interval_minutes = int(float(self._settings.get("interval", 5) or 5))
        self._mind.cycle_interval = 60 if mode == "agressivo" else max(1, interval_minutes) * 60
        directive = str(self._settings.get("directive", "") or "").strip()
        self._mind.user_directive = directive or None

    def _capture_log(self, msg: str) -> None:
        entry = f"[{time.strftime('%H:%M:%S')}] {msg}"
        self._logs.append(entry)
        self._logs = self._logs[-250:]
        try:
            print(entry)
        except UnicodeEncodeError:
            print(entry.encode("ascii", errors="replace").decode("ascii"))

    def get_state(self) -> dict[str, Any]:
        running = bool(self._mind and self._mind.running)
        changed_files = self._tracker.get_git_changed_files()
        return {
            "settings": dict(self._settings),
            "running": running,
            "cycle_active": self._cycle_active,
            "last_error": self._last_error,
            "last_modified_path": getattr(self._mind, "last_modified_path", None) if self._mind else None,
            "logs": self._logs[-120:],
            "changed_files": changed_files,
            "history": self._tracker.history[:12],
            "score": self._score_engine.get_last_score(),
            "proof": self._read_proof(),
            "restart": {
                "pending_reason": self._restart_bridge.pending_reason,
                "requested_at": self._restart_bridge.requested_at,
            },
        }

    def _read_proof(self) -> dict[str, Any] | None:
        if not self.PROOF_PATH.exists():
            return None
        try:
            return json.loads(self.PROOF_PATH.read_text(encoding="utf-8"))
        except Exception as error:
            self._last_error = f"Falha ao ler proof-of-work: {error}"
            return None

    def update_settings(self, updates: dict[str, Any]) -> dict[str, Any]:
        allowed = {"directive", "auto_restart", "active", "mode", "interval"}
        for key, value in (updates or {}).items():
            if key not in allowed:
                continue
            if key == "mode":
                self._settings[key] = self._normalize_mode(value)
            else:
                self._settings[key] = value
        self._save_settings()
        if self._mind is not None:
            self._apply_settings_to_mind()
        return self.get_state()

    def start(self) -> dict[str, Any]:
        try:
            mind = self._ensure_mind()
            self._apply_settings_to_mind()
            if not mind.running:
                mind.start()
            self._settings["active"] = True
            self._save_settings()
        except Exception as error:
            self._last_error = str(error)
            self._capture_log(f"❌ Falha ao iniciar NexusMind: {error}")
        return self.get_state()

    def stop(self) -> dict[str, Any]:
        if self._mind and self._mind.running:
            self._mind.stop()
        self._settings["active"] = False
        self._save_settings()
        return self.get_state()

    def run_manual_cycle(self) -> dict[str, Any]:
        mind = self._ensure_mind()
        self._apply_settings_to_mind()
        if self._cycle_active:
            self._capture_log("⚠️ Já existe um ciclo NexusMind em andamento.")
            return self.get_state()

        directive = str(self._settings.get("directive", "") or "").strip() or None

        def _runner() -> None:
            with self._cycle_lock:
                self._cycle_active = True
                try:
                    mind._run_one_cycle(directive)  # noqa: SLF001 - legacy runtime reuse
                    self._last_error = None
                except Exception as error:
                    self._last_error = str(error)
                    self._capture_log(f"❌ Ciclo manual falhou: {error}")
                finally:
                    self._cycle_active = False

        threading.Thread(target=_runner, daemon=True, name="nexus-mind-manual").start()
        self._capture_log("🧪 Ciclo manual disparado pela interface web.")
        return self.get_state()

    def rollback(self) -> dict[str, Any]:
        if self._cycle_active:
            self._capture_log("⚠️ Rollback bloqueado enquanto um ciclo está em andamento.")
            return self.get_state()
        ok = self._guard.rollback()
        if ok:
            self._capture_log("⏪ Rollback executado via interface web.")
        else:
            self._capture_log("❌ Erro ao executar rollback via interface web.")
        return self.get_state()

    def refresh_proof(self) -> dict[str, Any]:
        report = ProofOfWork().save_report()
        self._capture_log(f"📋 Proof-of-work atualizado: {len(report.get('verifications', []))} verificações.")
        return self.get_state()

    def clear_restart_flag(self) -> dict[str, Any]:
        self._restart_bridge.clear()
        self._capture_log("🧹 Sinal de reinício pendente removido.")
        return self.get_state()
