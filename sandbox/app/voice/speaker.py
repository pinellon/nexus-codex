"""Speaker modular de voz usado pelo modo operacional."""

from __future__ import annotations

from app.settings_manager import load as load_settings
from app.voice_output import falar


class VoiceSpeaker:
    def __init__(self, settings: dict | None = None, logger=None):
        self.settings = settings or load_settings()
        self.logger = logger

    def speak(self, text: str):
        if isinstance(self.settings, dict):
            engine = self.settings.get("voice_engine", "pyttsx3")
            cfg = self.settings
        else:
            engine = getattr(self.settings, "voice_engine", "pyttsx3")
            cfg = None
        falar(text, engine=engine, settings=cfg)
