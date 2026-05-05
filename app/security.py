"""Confirmacoes para comandos perigosos."""


_DANGEROUS = {"desligar_pc", "reiniciar_pc", "suspender_pc", "bloquear_tela"}


def precisa_confirmacao(intent_name: str) -> bool:
    return intent_name in _DANGEROUS


def mensagem_confirmacao(intent_name: str) -> str:
    labels = {
        "desligar_pc": "Desligar o computador agora?",
        "reiniciar_pc": "Reiniciar o computador agora?",
        "suspender_pc": "Suspender o computador agora?",
        "bloquear_tela": "Bloquear a tela agora?",
    }
    return labels.get(intent_name, "Confirmar esta acao?")

