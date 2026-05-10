"""Tratamento amigavel de erros."""

from app.logger import log_error


def handle_error(error: Exception) -> str:
    try:
        msg = getattr(error, "user_message", None) or str(error) or "Erro desconhecido."
        tech = getattr(error, "technical_message", msg)
        log_error(tech)
        return msg
    except Exception:
        return "Erro ao processar a solicitacao."

