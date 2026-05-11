"""Configuracoes centrais do NEXUS."""

import json
import os
from dataclasses import dataclass
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


@dataclass(frozen=True)
class Settings:
    wake_word: str
    language: str
    voice_engine: str
    continuous_mode: bool
    workspace: Path
    log_file: Path
    elevenlabs_api_key: str
    elevenlabs_voice_id: str
    listen_timeout: int = 5
    phrase_time_limit: int = 8
    voice_rate: int = 180
    voice_volume: float = 1.0
    command_timeout_seconds: int = 20


def _as_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "sim", "on"}


def load_settings() -> Settings:
    """Compatibilidade com o launcher Voice Coder v3."""
    try:
        import app.settings_manager as persisted
        saved = persisted.load()
    except Exception:
        saved = {}

    workspace = Path(os.getenv("NEXUS_WORKSPACE", saved.get("workspace", "workspace"))).resolve()
    workspace.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    return Settings(
        wake_word=os.getenv("NEXUS_WAKE_WORD", saved.get("wake_word", "nexus")).strip().lower(),
        language=os.getenv("NEXUS_LANGUAGE", saved.get("voice_language", "pt-BR")).strip(),
        voice_engine=os.getenv("NEXUS_VOICE_ENGINE", saved.get("voice_engine", "pyttsx3")).strip().lower(),
        continuous_mode=_as_bool(os.getenv("NEXUS_CONTINUOUS_MODE", saved.get("continuous_mode", False))),
        workspace=workspace,
        log_file=LOGS_DIR / "nexus.log",
        elevenlabs_api_key=os.getenv("ELEVENLABS_API_KEY", saved.get("elevenlabs_api_key", "")).strip(),
        elevenlabs_voice_id=os.getenv("ELEVENLABS_VOICE_ID", saved.get("elevenlabs_voice_id", "")).strip(),
    )


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
