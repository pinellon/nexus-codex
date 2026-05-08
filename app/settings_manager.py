"""Configuracoes persistentes em JSON, aplicadas sem reiniciar."""

import json
import os
from app.config import DATA_DIR

SETTINGS_FILE = DATA_DIR / "settings.json"

_DEFAULTS = {
    "openai_api_key": "",
    "owner_name": "Nicolas",
    "speak_responses": True,
    "voice_backend": "auto",
    "voice_input_device": "",
    "wake_word": "nexus",
    "voice_require_wake_word": True,
    "voice_confirm_commands": True,
    "voice_loop_speak_start": False,
    "voice_listen_timeout": 5,
    "voice_phrase_time_limit": 10,
    "voice_language": "pt-BR",
    "voice_language_vosk": "pt",
    "voice_engine": "pyttsx3",
    "edge_tts_voice": "pt-BR-AntonioNeural",
    "elevenlabs_api_key": "",
    "elevenlabs_voice_id": "",
    "default_media": "youtube",
    "always_on_top": False,
    "compact_mode": False,
    "show_timestamps": True,
    "ui_sounds": True,
    "ui_animations": True,
    "obsidian_enabled": True,
    "obsidian_vault_path": "",
    "obsidian_memory_folder": "NEXUS/Memory Inbox",
    "obsidian_auto_register": True,
    "obsidian_max_results": 5,
    "monitor_interval_ms": 2000,
}


def load() -> dict:
    data = dict(_DEFAULTS)
    try:
        if SETTINGS_FILE.exists():
            saved = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                data.update(saved)
    except Exception:
        pass
    if not data.get("openai_api_key"):
        data["openai_api_key"] = os.getenv("OPENAI_API_KEY", "")
    return data


def save(settings: dict) -> dict:
    data = dict(_DEFAULTS)
    data.update(settings or {})
    DATA_DIR.mkdir(exist_ok=True)
    SETTINGS_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    if data.get("openai_api_key"):
        os.environ["OPENAI_API_KEY"] = data["openai_api_key"]
    _sync_env(data)
    return data


def get(key: str, fallback=None):
    return load().get(key, fallback if fallback is not None else _DEFAULTS.get(key))


def set_value(key: str, value):
    cfg = load()
    cfg[key] = value
    return save(cfg)


def _sync_env(data: dict):
    api_key = data.get("elevenlabs_api_key", "")
    voice_id = data.get("elevenlabs_voice_id", "")
    if not api_key and not voice_id:
        return
    env_path = DATA_DIR.parent / ".env"
    env_path.write_text(
        f"ELEVENLABS_API_KEY={api_key}\nELEVENLABS_VOICE_ID={voice_id}\n",
        encoding="utf-8",
    )
    if api_key:
        os.environ["ELEVENLABS_API_KEY"] = api_key
    if voice_id:
        os.environ["ELEVENLABS_VOICE_ID"] = voice_id
