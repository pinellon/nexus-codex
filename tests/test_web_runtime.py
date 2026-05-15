from __future__ import annotations

from pathlib import Path

from app.self_improvement.web_runtime import WebNexusMindRuntime


def test_web_runtime_forces_supervised_mode_when_autonomy_is_locked(monkeypatch, tmp_path):
    monkeypatch.setattr(WebNexusMindRuntime, "SETTINGS_PATH", Path(tmp_path / "mind_settings.json"))
    monkeypatch.setattr(WebNexusMindRuntime, "PROOF_PATH", Path(tmp_path / "nexus_proof.json"))
    monkeypatch.setattr("app.self_improvement.web_runtime.settings_manager.load", lambda: {"mind_allow_autonomous": False})

    runtime = WebNexusMindRuntime()
    state = runtime.update_settings({"mode": "autônomo"})

    assert state["settings"]["mode"] == "supervisionado"


def test_web_runtime_allows_autonomous_mode_when_permission_is_enabled(monkeypatch, tmp_path):
    monkeypatch.setattr(WebNexusMindRuntime, "SETTINGS_PATH", Path(tmp_path / "mind_settings.json"))
    monkeypatch.setattr(WebNexusMindRuntime, "PROOF_PATH", Path(tmp_path / "nexus_proof.json"))
    monkeypatch.setattr("app.self_improvement.web_runtime.settings_manager.load", lambda: {"mind_allow_autonomous": True})

    runtime = WebNexusMindRuntime()
    state = runtime.update_settings({"mode": "autônomo"})

    assert state["settings"]["mode"] == "autônomo"
