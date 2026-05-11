from __future__ import annotations

from app.chat.chat_engine import ChatEngine
from app.chat.chat_interface import ChatInterface


class ChatModule:
    def __init__(self, settings, logger, engine: ChatEngine | None = None):
        self.settings = settings
        self.logger = logger
        self.engine = engine or ChatEngine(settings=settings, logger=logger)

    def start_chat_session(self):
        self.logger.info("Chat session started.")
        ChatInterface(
            settings=self.settings,
            logger=self.logger,
            engine=self.engine,
        ).start_chat()

    def generate_response(self, user_input, confirm_callback=None):
        result = self.engine.process_input(
            user_input,
            speak=False,
            confirm_callback=confirm_callback,
        )
        return result["response"]
