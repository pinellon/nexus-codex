"""Roteador operacional: mostra o que o NEXUS entendeu antes de executar."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.core.text_utils import normalize_text, remove_wake_word
from app.agent.agent_commands import extract_task, is_agent_command
from app.vision.vision_commands import detect_intent as detect_vision_intent
from app.vision.vision_commands import is_vision_command
from app.home.home_commands import detect_home_intent, is_home_command


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

        if command_text in {"parar agente", "cancelar pesquisa", "cancelar agente"}:
            return Command("stop_agent", "agent", {}, raw, normalized)

        if is_agent_command(command_text):
            return Command("agent_task", "agent", {"task": extract_task(command_text)}, raw, normalized)

        if is_vision_command(command_text):
            intent, question = detect_vision_intent(command_text)
            return Command("vision", "vision", {"intent": intent, "question": question}, raw, normalized)

        if is_home_command(command_text):
            intent, _params = detect_home_intent(command_text)
            return Command("home", "home", {"intent": intent}, raw, normalized)

        if command_text in {"ajuda", "comandos", "o que voce faz", "o que vc faz"}:
            return Command("help", "system", {"text": command_text}, raw, normalized)

        if "modo foco" in command_text or "foco" == command_text:
            return Command("run_template", "automation", {"template": "modo_foco"}, raw, normalized)

        if "modo aula" in command_text or "modo estudo" in command_text:
            return Command("run_template", "automation", {"template": "modo_aula"}, raw, normalized)

        if "modo apresentacao" in command_text or "modo apresentacao" in command_text:
            return Command("run_template", "automation", {"template": "modo_apresentacao"}, raw, normalized)

        if "diagnostico rapido" in command_text:
            return Command("run_template", "automation", {"template": "diagnostico_rapido"}, raw, normalized)

        if "diagnostico do projeto" in command_text or "saude do projeto" in command_text:
            return Command("project_health", "diagnostics", {}, raw, normalized)

        if "ultimos eventos" in command_text or "historico da sessao" in command_text:
            return Command("session_summary", "diagnostics", {}, raw, normalized)

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
