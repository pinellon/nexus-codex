"""Entrada de voz opcional por microfone, agora com backends plugáveis."""

from __future__ import annotations

from app.settings_manager import load as load_settings
from app.voice.manager import listen_text


def ouvir_microfone(
    settings: dict | None = None,
    backend: str | None = None,
    timeout: int = 5,
    phrase_time_limit: int = 10,
) -> str:
    try:
        cfg = settings or load_settings()
        return listen_text(settings=cfg, backend=backend, timeout=timeout, phrase_time_limit=phrase_time_limit)
    except Exception as error:
        raise RuntimeError(f"Não consegui ouvir o microfone: {error}") from error
