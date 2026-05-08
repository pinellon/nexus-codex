"""Camada de compatibilidade para confirmações e bloqueios."""

from __future__ import annotations

from app.action_policy import PolicyDecision, assess_intent


def avaliar_intent(intent_name: str, params: dict | None = None) -> PolicyDecision:
    return assess_intent(intent_name, params)


def precisa_confirmacao(intent_name: str, params: dict | None = None) -> bool:
    return assess_intent(intent_name, params).requires_confirmation


def mensagem_confirmacao(intent_name: str, params: dict | None = None) -> str:
    decision = assess_intent(intent_name, params)
    return decision.message or "Confirmar esta ação?"


def acao_bloqueada(intent_name: str, params: dict | None = None) -> bool:
    return not assess_intent(intent_name, params).allowed


def motivo_bloqueio(intent_name: str, params: dict | None = None) -> str:
    return assess_intent(intent_name, params).reason
