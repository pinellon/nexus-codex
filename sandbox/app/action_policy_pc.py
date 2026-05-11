"""Politica central para acoes desktop do NEXUS."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    requires_confirmation: bool
    reason: str = ""


CONFIRM_ACTIONS = {
    "close_window",
    "create_folder",
    "copy_text",
}

HIGH_RISK_CONFIRM_ACTIONS = {
    "trash_path",
    "move_path",
    "open_url",
}

BLOCKED_ACTIONS = {
    "type_text_globally",
    "click_screen_position",
    "kill_process_by_pid",
}


def evaluate_pc_action(action_name: str) -> PolicyDecision:
    if action_name in BLOCKED_ACTIONS:
        return PolicyDecision(False, False, "Acao bloqueada por seguranca.")
    if action_name in HIGH_RISK_CONFIRM_ACTIONS:
        return PolicyDecision(True, True, "Confirmacao obrigatoria para evitar acao errada.")
    if action_name in CONFIRM_ACTIONS:
        return PolicyDecision(True, True, "Confirmacao recomendada.")
    return PolicyDecision(True, False, "")
