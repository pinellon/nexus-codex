"""Integração do ResearchAgent com o CommandRouter do NEXUS.

Como adicionar ao command_router.py existente:

    from app.agent.agent_commands import AgentCommandHandler

    # No __init__ do CommandRouter:
    self.agent_handler = AgentCommandHandler(settings, logger, ui_callback)

    # No método route(), antes do retorno padrão:
    if is_agent_command(text):
        return self.agent_handler.handle(text)

Este módulo detecta intenções de pesquisa autônoma e dispara o agente.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Callable

from .research_agent import AgentEvent, ResearchAgent

log = logging.getLogger("nexus.agent_commands")

# ---------------------------------------------------------------------------
# Padrões de detecção de intent "agente"
# ---------------------------------------------------------------------------

_RESEARCH_PATTERNS = [
    r"pesquis[ae]\s+.+\s+e\s+salv[ae]",
    r"pesquis[ae]\s+.+\s+obsidian",
    r"busca\s+.+\s+e\s+salv[ae]",
    r"encontra\s+.+\s+e\s+salv[ae]",
    r"salv[ae]\s+.+\s+obsidian",
    r"agent[e]?\s+pesquis[ae]",
    r"modo\s+agente",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _RESEARCH_PATTERNS]


def is_agent_command(text: str) -> bool:
    """Retorna True se o texto parece uma tarefa para o agente autônomo."""
    return any(p.search(text) for p in _COMPILED)


def extract_task(raw_text: str) -> str:
    """Remove wake words e prefixos antes de enviar ao agente."""
    # Remove "nexus," do início (case-insensitive)
    text = re.sub(r"^nexus[,\s]+", "", raw_text.strip(), flags=re.IGNORECASE)
    return text.strip()


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

@dataclass
class AgentResult:
    """Resultado retornado ao CommandRouter."""
    intent: str = "agent_task"
    label: str = "Agente Autônomo"
    args: dict = None

    def __post_init__(self):
        self.args = self.args or {}


class AgentCommandHandler:
    """Gerencia o ciclo de vida do ResearchAgent integrado à UI do NEXUS."""

    def __init__(
        self,
        settings,
        logger: logging.Logger | None = None,
        ui_callback: Callable[[str], None] | None = None,
    ):
        """
        Args:
            settings: Configurações do NEXUS (precisa de openai_api_key e
                      obsidian_vault_path).
            logger: Logger opcional.
            ui_callback: Função que recebe strings de status para exibir no chat
                         da UI (ex: `chat_panel.append_system_message`).
        """
        self.settings = settings
        self.log = logger or log
        self.ui_callback = ui_callback or (lambda msg: print(f"[NEXUS Agent] {msg}"))
        self._agent: ResearchAgent | None = None

    # ------------------------------------------------------------------
    # Integração com CommandRouter
    # ------------------------------------------------------------------

    def handle(self, raw_text: str) -> AgentResult:
        """Recebe o texto do usuário, dispara o agente em background e
        retorna imediatamente para não travar a UI."""
        task = extract_task(raw_text)
        self.log.info("AgentCommandHandler: despachando tarefa: %s", task)
        self._run_agent(task)
        return AgentResult(
            intent="agent_task",
            label="Agente Autônomo",
            args={"task": task},
        )

    # ------------------------------------------------------------------
    # Ciclo do agente
    # ------------------------------------------------------------------

    def _run_agent(self, task: str) -> None:
        """Inicia o agente em thread separada."""
        # Para agente anterior se ainda estiver rodando
        if self._agent:
            self._agent.stop()

        self._agent = ResearchAgent(self.settings, self.log)

        def _on_event(event: AgentEvent) -> None:
            self._dispatch_to_ui(event)

        def _on_done(result: str) -> None:
            self.ui_callback(f"\n📋 **NEXUS Agent concluído:**\n{result}")

        self._agent.run_async(task, on_event=_on_event, on_done=_on_done)

    def _dispatch_to_ui(self, event: AgentEvent) -> None:
        """Converte AgentEvent em mensagem legível para o chat do NEXUS."""
        icons = {
            "thinking":    "🤔",
            "tool_call":   "",   # já tem icon no label
            "tool_result": "",   # já tem icon no label
            "done":        "✅",
            "error":       "⚠️",
        }
        prefix = icons.get(event.kind, "")
        msg = f"{prefix} {event.message}".strip()
        self.ui_callback(msg)

    def stop(self) -> None:
        """Para o agente em execução."""
        if self._agent:
            self._agent.stop()
            self.ui_callback("⏹️ Agente parado.")
