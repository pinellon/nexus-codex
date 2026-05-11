"""Entrada de voz opcional por microfone, agora com backends plugáveis."""

from __future__ import annotations

from app.settings_manager import load as load_settings
from app.voice.manager import listen_text


def _as_int(value, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def ouvir_microfone(
    settings: dict | None = None,
    backend: str | None = None,
    timeout: int | None = None,
    phrase_time_limit: int | None = None,
) -> str:
    try:
        cfg = settings or load_settings()
        effective_timeout = _as_int(timeout if timeout is not None else cfg.get("voice_listen_timeout"), 5)
        effective_phrase_limit = _as_int(
            phrase_time_limit if phrase_time_limit is not None else cfg.get("voice_phrase_time_limit"),
            10,
        )
        return listen_text(
            settings=cfg,
            backend=backend,
            timeout=effective_timeout,
            phrase_time_limit=effective_phrase_limit,
        )
    except Exception as error:
        raise RuntimeError(f"Não consegui ouvir o microfone: {error}") from error
