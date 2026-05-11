from __future__ import annotations

from app.core.command_router import Command, CommandRouter as BaseCommandRouter
from app.core.text_utils import normalize_text, remove_wake_word


class ChatCommandRouter(BaseCommandRouter):
    """Thin chat wrapper around the central CommandRouter."""

    EXIT_WORDS = frozenset({"sair", "parar", "sleep", "exit", "quit"})

    def is_exit_command(self, text: str, command: Command | None = None) -> bool:
        normalized = normalize_text(text)
        if command and command.intent in self.EXIT_WORDS:
            return True

        stripped = remove_wake_word(normalized, self.wake_word) or normalized
        return stripped in self.EXIT_WORDS
