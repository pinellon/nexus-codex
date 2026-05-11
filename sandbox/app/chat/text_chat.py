from __future__ import annotations

import logging

from app.chat.chat_engine import ChatEngine


class TextChat:
    def __init__(self, settings, logger=None, engine: ChatEngine | None = None):
        self.settings = settings
        self.logger = logger or logging.getLogger(__name__)
        self.engine = engine or ChatEngine(settings=settings, logger=self.logger)

    def handle_input(self, text, confirm_callback=None):
        try:
            self.logger.info("Recebido texto do usuario: %s", text)
            result = self.engine.process_input(
                text,
                speak=False,
                confirm_callback=confirm_callback,
            )
            return result["response"]
        except Exception as error:
            self.logger.error("Erro ao processar entrada de texto: %s", error)
            return "Desculpe, ocorreu um erro ao processar seu pedido."

    def process_command(self, command):
        return self.engine.handler.render_command(command)
