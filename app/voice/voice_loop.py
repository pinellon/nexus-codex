"""Loop de voz continuo para a interface do NEXUS."""

from __future__ import annotations

import threading
from collections.abc import Callable

from app.core.command_router import CommandRouter
from app.logger import log_action, log_command, log_error
from app.voice_input import ouvir_microfone
from app.voice_output import falar


class VoiceLoop:
    """Ouve em thread separada e envia comandos para a mesma pipeline da UI."""

    def __init__(
        self,
        command_callback: Callable[[str], None],
        event_callback: Callable[[str, str], None] | None = None,
        settings: dict | None = None,
    ):
        self.command_callback = command_callback
        self.event_callback = event_callback
        self.settings = settings or {}
        self.router = CommandRouter(self.settings.get("wake_word", "nexus"))
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return bool(self._thread and self._thread.is_alive())

    def start(self):
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self.run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop.set()

    def run(self):
        self._emit("voice", "Voz continua ativada.")
        log_action("VoiceLoop iniciado")
        if self.settings.get("voice_loop_speak_start", False):
            falar("NEXUS ouvindo.", settings=self.settings)

        while not self._stop.is_set():
            try:
                text = ouvir_microfone(settings=self.settings, backend=self.settings.get("voice_backend", "auto"))
            except Exception as error:
                log_error(f"VoiceLoop: {error}")
                self._emit("error", str(error))
                continue

            if self._stop.is_set():
                break
            if not text:
                continue

            command = self.router.route(text)
            log_command(f"VOZ: {text} -> {command.label}")
            self._emit("heard", text)
            self._emit("understood", command.label)
            self.command_callback(text)

        self._emit("voice", "Voz continua desativada.")
        log_action("VoiceLoop parado")

    def _emit(self, kind: str, message: str):
        if self.event_callback:
            self.event_callback(kind, message)
