from __future__ import annotations

import logging
from collections.abc import Callable

from app.core.command_router import Command


class ChatHandler:
    """Executes chat requests through the main NEXUS command pipeline."""

    def __init__(
        self,
        settings=None,
        logger: logging.Logger | None = None,
        command_executor: Callable[[str, object | None], str] | None = None,
    ):
        self.settings = settings
        self.logger = logger or logging.getLogger(__name__)
        self._command_executor = command_executor

    def handle_message(
        self,
        user_message: str,
        command: Command | None = None,
        confirm_callback=None,
    ) -> str:
        text = (user_message or "").strip()
        if not text:
            return "Digite algo para eu processar."

        if command and command.intent in {"sair", "parar", "sleep", "exit", "quit"}:
            return "Encerrando chat."

        try:
            executor = self._resolve_executor()
            if executor is None:
                return self.render_command(command)
            return executor(text, confirm_callback)
        except Exception as error:
            self.logger.error("Erro ao processar a mensagem de chat: %s", error)
            return self.render_command(command, fallback=True)

    def render_command(self, command: Command | None, fallback: bool = False) -> str:
        if command is None:
            return "Nao consegui entender o pedido."

        if command.domain == "system" and command.intent == "help":
            return "Peca um comando ou uma pergunta. Eu passo isso para o pipeline principal do NEXUS."

        if command.domain == "assistant":
            if fallback:
                return "O pipeline principal nao respondeu. Tente novamente em instantes."
            return f"Encaminhando para IA: {command.args.get('text', '')}".strip()

        label = command.label
        if command.args:
            return f"Entendi {label} com argumentos {command.args}."
        return f"Entendi {label}."

    def _resolve_executor(self) -> Callable[[str, object | None], str] | None:
        if self._command_executor is not None:
            return self._command_executor

        try:
            from theme import processar_comando
        except Exception as error:
            self.logger.warning("Pipeline principal de chat indisponivel: %s", error)
            return None

        self._command_executor = processar_comando
        return self._command_executor
