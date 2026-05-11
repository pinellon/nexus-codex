"""Launcher de aplicativos com registro local e descoberta básica no Windows."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import difflib
import json
import os
import re
import shlex
import subprocess
import sys
import unicodedata
import webbrowser


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
REGISTRY_PATH = DATA_DIR / "apps_registry.json"


@dataclass
class LaunchResult:
    success: bool
    message: str
    app_name: str = ""
    target: str = ""

    def __str__(self) -> str:
        return self.message


@dataclass
class AppEntry:
    alias: str
    target: str
    source: str


def _normalize(text: str) -> str:
    base = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in base if not unicodedata.combining(ch)).lower()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _registry_file() -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    return REGISTRY_PATH


def _load_user_registry() -> dict[str, str]:
    path = _registry_file()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {str(k): str(v) for k, v in data.items()}
    except Exception:
        return {}
    return {}


def _save_user_registry(data: dict[str, str]) -> None:
    path = _registry_file()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


_DEFAULT_APPS = {
    "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "vscode": r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
    "vs code": r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe",
    "bloco de notas": "notepad.exe",
    "notepad": "notepad.exe",
    "calculadora": "calc.exe",
    "spotify": r"%APPDATA%\Spotify\Spotify.exe",
    "discord": r"%LOCALAPPDATA%\Discord\Update.exe --processStart Discord.exe",
    "explorer": "explorer.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "terminal": "wt.exe",
    "windows terminal": "wt.exe",
}


def _expand_target(target: str) -> str:
    return os.path.expandvars(os.path.expanduser(target or ""))


def _iter_windows_shortcuts() -> list[AppEntry]:
    if os.name != "nt":
        return []
    locations = [
        os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%ProgramData%\Microsoft\Windows\Start Menu\Programs"),
        os.path.expandvars(r"%USERPROFILE%\Desktop"),
        os.path.expandvars(r"%PUBLIC%\Desktop"),
    ]
    items: list[AppEntry] = []
    exts = {".lnk", ".url", ".exe", ".bat", ".cmd"}
    for location in locations:
        root = Path(location)
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.suffix.lower() not in exts:
                continue
            alias = path.stem.replace("-", " ").replace("_", " ").strip()
            if alias:
                items.append(AppEntry(alias=alias, target=str(path), source="system-scan"))
    return items


def _catalog() -> dict[str, AppEntry]:
    catalog: dict[str, AppEntry] = {}
    for alias, target in _DEFAULT_APPS.items():
        catalog[_normalize(alias)] = AppEntry(alias=alias, target=target, source="builtin")
    for alias, target in _load_user_registry().items():
        catalog[_normalize(alias)] = AppEntry(alias=alias, target=target, source="user")
    for item in _iter_windows_shortcuts():
        catalog.setdefault(_normalize(item.alias), item)
    return catalog


def listar_apps(limit: int = 40) -> str:
    catalog = _catalog()
    if not catalog:
        return "Nenhum app disponível no catálogo."
    lines = ["Apps disponíveis:"]
    for key in sorted(catalog)[:limit]:
        item = catalog[key]
        lines.append(f"- {item.alias} [{item.source}]")
    if len(catalog) > limit:
        lines.append(f"... e mais {len(catalog) - limit} apps")
    return "\n".join(lines)


def registrar_app(alias: str, target: str) -> LaunchResult:
    alias = (alias or "").strip()
    target = _expand_target(target)
    if not alias or not target:
        return LaunchResult(False, "Informe alias e caminho do aplicativo.")
    data = _load_user_registry()
    data[alias] = target
    _save_user_registry(data)
    return LaunchResult(True, f"App '{alias}' registrado com sucesso.", alias, target)


def _resolve_app(name: str) -> AppEntry | None:
    catalog = _catalog()
    key = _normalize(name)
    if key in catalog:
        return catalog[key]
    matches = difflib.get_close_matches(key, list(catalog.keys()), n=1, cutoff=0.72)
    if matches:
        return catalog[matches[0]]
    for alias, item in catalog.items():
        if key and key in alias:
            return item
    return None


def _start_path(target: str) -> None:
    expanded = _expand_target(target)
    if expanded.startswith(("http://", "https://")):
        webbrowser.open(expanded)
        return

    if os.name == "nt":
        if Path(expanded).exists() or expanded.lower().endswith((".lnk", ".url")):
            os.startfile(expanded)  # type: ignore[attr-defined]
            return
        argv = shlex.split(expanded, posix=False)
        subprocess.Popen(argv, shell=False)
        return

    path = Path(expanded)
    if path.exists():
        opener = "open" if sys.platform == "darwin" else "xdg-open"
        subprocess.Popen([opener, str(path)], shell=False)
        return
    argv = shlex.split(expanded)
    subprocess.Popen(argv, shell=False)


def abrir_app(name: str) -> LaunchResult:
    item = _resolve_app(name)
    if not item:
        return LaunchResult(False, f"App '{name}' não encontrado. Use 'listar apps' ou registre manualmente.")
    try:
        _start_path(item.target)
        return LaunchResult(True, f"Abrindo {item.alias}...", item.alias, item.target)
    except FileNotFoundError:
        return LaunchResult(False, f"Não encontrei o executável de {item.alias}.", item.alias, item.target)
    except Exception as error:
        return LaunchResult(False, f"Falha ao abrir {item.alias}: {error}", item.alias, item.target)
