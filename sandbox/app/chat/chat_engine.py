from __future__ import annotations

from app.chat.chat_handler import ChatHandler
from app.chat.command_router import ChatCommandRouter
from app.voice.speaker import VoiceSpeaker


class ChatEngine:
    def __init__(self, settings, logger, router=None, speaker=None, handler=None):
        self.settings = settings
        self.logger = logger
        self.router = router or ChatCommandRouter(settings=settings, logger=logger)
        self.speaker = speaker or VoiceSpeaker(settings=settings, logger=logger)
        self.handler = handler or ChatHandler(settings=settings, logger=logger)
        self._speak_responses = bool(self._setting("speak_responses", True))

    def process_input(self, text: str, speak: bool | None = None, confirm_callback=None):
        raw_text = (text or "").strip()
        command = self.router.route(raw_text)
        should_exit = self.router.is_exit_command(raw_text, command)
        if should_exit:
            response = "Encerrando chat."
        else:
            response = self.handler.handle_message(
                raw_text,
                command=command,
                confirm_callback=confirm_callback,
            )
        understood = self.router.describe(raw_text)
        should_speak = self._speak_responses if speak is None else speak

        if should_speak and response and not should_exit:
            self.speaker.speak(response)

        return {
            "command": command,
            "understood": understood,
            "response": response,
            "should_exit": should_exit,
        }

    @classmethod
    def is_exit_request(cls, text: str, command=None, router=None) -> bool:
        if router is not None and hasattr(router, "is_exit_command"):
            return bool(router.is_exit_command(text, command))
        fallback_router = ChatCommandRouter()
        return fallback_router.is_exit_command(text, command)

    def _setting(self, key: str, default):
        if isinstance(self.settings, dict):
            return self.settings.get(key, default)
        return getattr(self.settings, key, default)
