"""Roteador operacional: mostra o que o NEXUS entendeu antes de executar."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.text_utils import normalize_text, remove_wake_word


@dataclass(frozen=True)
class Command:
    intent: str
    domain: str
    args: dict[str, Any] = field(default_factory=dict)
    raw: str = ""
    normalized: str = ""

    @property
    def label(self) -> str:
        return f"{self.domain}:{self.intent}"


class CommandRouter:
    """Classifica comandos em portugues usando os roteadores existentes do NEXUS."""

    def __init__(self, wake_word: str = "nexus", logger=None, settings=None):
        if settings is None and hasattr(wake_word, "wake_word"):
            settings = wake_word
        self.wake_word = getattr(settings, "wake_word", wake_word) if settings else wake_word
        self.logger = logger

    def route(self, text: str) -> Command:
        raw = text or ""
        normalized = normalize_text(raw)
        command_text = remove_wake_word(normalized, self.wake_word) or normalized
        if self.logger:
            try:
                self.logger.info("Roteando comando: raw=%s | command=%s", raw, command_text)
            except Exception:
                pass

        if not command_text:
            return Command("empty", "system", raw=raw, normalized=normalized)

        try:
            from app.intent_desktop_actions import detect_desktop_intent
            intent = detect_desktop_intent(command_text)
            if intent:
                return Command(intent.name, "desktop", intent.params, raw, normalized)
        except Exception:
            pass

        try:
            from coding.intent_coding import detectar_intent_coding
            intent = detectar_intent_coding(command_text)
            if intent:
                return Command(intent.name, "coder", intent.params, raw, normalized)
        except Exception:
            pass

        try:
            from app.intent_apps import detectar_intent_apps
            intent = detectar_intent_apps(command_text)
            if intent:
                return Command(intent.name, "apps", intent.params, raw, normalized)
        except Exception:
            pass

        try:
            from app.intent_router import detectar_intent
            intent = detectar_intent(command_text)
            if intent:
                return Command(intent.name, "pc", intent.params, raw, normalized)
        except Exception:
            pass

        if "obsidian" in command_text or "vault" in command_text:
            return Command("obsidian", "memory", {"text": command_text}, raw, normalized)

        return Command("ask_ai", "assistant", {"text": command_text}, raw, normalized)

    def describe(self, text: str) -> str:
        command = self.route(text)
        args = f" {command.args}" if command.args else ""
        return f"{command.label}{args}"
