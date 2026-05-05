"""Configuracoes centrais do NEXUS."""

import json
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = DATA_DIR / "logs"
MEMORY_FILE = DATA_DIR / "memory.json"
CONFIG_FILE = BASE_DIR / "config.yaml"

DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

_saved_settings = {}
try:
    _settings_path = DATA_DIR / "settings.json"
    if _settings_path.exists():
        _saved_settings = json.loads(_settings_path.read_text(encoding="utf-8"))
except Exception:
    _saved_settings = {}

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "") or _saved_settings.get("openai_api_key", "")
NEXUS_OWNER = os.getenv("NEXUS_OWNER", "") or _saved_settings.get("owner_name", "Nicolas")
NEXUS_LANGUAGE = os.getenv("NEXUS_LANGUAGE", "pt-BR")
DEFAULT_MEDIA = os.getenv("NEXUS_DEFAULT_MEDIA", "") or _saved_settings.get("default_media", "youtube")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_HISTORY = 10

SYSTEM_PROMPT = f"""Voce e o NEXUS, assistente pessoal do {NEXUS_OWNER}.
Responda sempre em portugues do Brasil.
Seja direto, objetivo e util. Nunca diga que executou algo se nao executou."""


class AppConfig:
    def __init__(self, path: Path):
        self.path = path
        self.data = self._load()

    def _load(self) -> dict:
        defaults = {
            "voice": {
                "enabled": True,
                "provider": "elevenlabs",
                "name": "default",
                "rate": 180,
                "volume": 1.0,
            },
            "elevenlabs": {
                "model_id": "eleven_multilingual_v2",
                "output_format": "mp3_44100_128",
                "stability": 0.45,
                "similarity_boost": 0.75,
                "style": 0.25,
                "use_speaker_boost": True,
            },
        }
        try:
            import yaml
            if self.path.exists():
                loaded = yaml.safe_load(self.path.read_text(encoding="utf-8")) or {}
                return _deep_merge(defaults, loaded)
        except Exception:
            pass
        return defaults

    def reload(self):
        self.data = self._load()

    def get(self, key: str, default=None):
        current = self.data
        for part in key.split("."):
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for key, value in (override or {}).items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


config = AppConfig(CONFIG_FILE)
