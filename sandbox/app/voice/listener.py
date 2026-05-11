"""Listener modular de voz usado pelo modo operacional."""

from __future__ import annotations

from app.settings_manager import load as load_settings
from app.voice_input import ouvir_microfone


class VoiceListener:
    def __init__(self, settings: dict | None = None, logger=None):
        self.settings = settings or load_settings()
        self.logger = logger

    def listen_once(self) -> str:
        backend = self.settings.get("voice_backend", "auto") if isinstance(self.settings, dict) else "auto"
        return ouvir_microfone(settings=self.settings if isinstance(self.settings, dict) else None, backend=backend)
