"""Templates de comandos legais para o NEXUS.

A ideia e transformar comandos complexos em rotinas simples de voz/botao.
Exemplo: "Nexus, modo foco" pode virar fechar distrações, abrir VS Code,
abrir projeto e iniciar musica.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CommandTemplate:
    name: str
    description: str
    steps: list[dict[str, Any]] = field(default_factory=list)
    requires_confirmation: bool = False


TEMPLATES: dict[str, CommandTemplate] = {
    "modo_foco": CommandTemplate(
        name="modo_foco",
        description="Prepara o PC para codar sem distracao.",
        steps=[
            {"intent": "open_app", "args": {"app_id": "vscode"}},
            {"intent": "open_youtube", "args": {"query": "lofi coding focus"}},
            {"intent": "pc_status", "args": {}},
        ],
    ),
    "modo_aula": CommandTemplate(
        name="modo_aula",
        description="Abre ambiente rapido para estudar e anotar.",
        steps=[
            {"intent": "open_app", "args": {"app_id": "chrome"}},
            {"intent": "open_app", "args": {"app_id": "notepad"}},
        ],
    ),
    "modo_apresentacao": CommandTemplate(
        name="modo_apresentacao",
        description="Prepara o computador para demonstrar o NEXUS.",
        steps=[
            {"intent": "mute_volume", "args": {}},
            {"intent": "pc_status", "args": {}},
        ],
    ),
    "diagnostico_rapido": CommandTemplate(
        name="diagnostico_rapido",
        description="Coleta status basico do PC para debug.",
        steps=[
            {"intent": "pc_status", "args": {}},
            {"intent": "screenshot", "args": {}},
        ],
    ),
}


def list_templates() -> list[CommandTemplate]:
    return list(TEMPLATES.values())


def get_template(name: str) -> CommandTemplate | None:
    key = (name or "").strip().lower().replace(" ", "_").replace("-", "_")
    return TEMPLATES.get(key)


def describe_templates() -> str:
    if not TEMPLATES:
        return "Nenhum template cadastrado."
    lines = ["Templates de comando disponíveis:"]
    for template in list_templates():
        lines.append(f"- {template.name}: {template.description}")
    return "\n".join(lines)
