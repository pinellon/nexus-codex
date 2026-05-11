"""Camada operacional de seguranca e confirmacao."""

from __future__ import annotations

from app.core.command_router import Command


class SafetyManager:
    """Centraliza a decisao de confirmar comandos de risco."""

    def assess(self, command: Command):
        if command.domain == "desktop":
            from app.action_policy_pc import evaluate_pc_action
            return evaluate_pc_action(command.intent)

        from app.security import avaliar_intent
        return avaliar_intent(command.intent, command.args)

    def confirm_if_needed(self, command: Command, confirm_callback=None) -> str | None:
        decision = self.assess(command)
        if not decision.allowed:
            return f"Acao bloqueada: {decision.reason or 'violou a politica de seguranca.'}"
        if decision.requires_confirmation:
            question = decision.message or decision.reason or f"Confirmar {command.intent}?"
            confirmed = confirm_callback(question) if confirm_callback else False
            if not confirmed:
                return "Acao cancelada."
        return None
