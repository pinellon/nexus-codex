"""Seleção e gerenciamento de backend de voz."""

from __future__ import annotations

from app.voice.backends import GoogleSpeechBackend, SoundDeviceGoogleBackend, VoskBackend, VoiceResult


def _has_pyaudio() -> bool:
    try:
        import pyaudio  # noqa: F401
        return True
    except Exception:
        return False


def _input_device_from_settings(settings: dict | None) -> int | None:
    if not settings:
        return None
    raw = settings.get("voice_input_device")
    if raw in (None, ""):
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def _create_backend(name: str, settings: dict | None = None):
    backend = (name or "auto").lower().strip()
    if backend in {"sounddevice", "sounddevice-google", "sd"}:
        return SoundDeviceGoogleBackend(device=_input_device_from_settings(settings))
    if backend == "vosk":
        return VoskBackend()
    if backend == "google":
        if not _has_pyaudio():
            return SoundDeviceGoogleBackend()
        return GoogleSpeechBackend()
    has_pyaudio = _has_pyaudio()
    if not has_pyaudio:
        return SoundDeviceGoogleBackend(device=_input_device_from_settings(settings))
    try:
        return VoskBackend()
    except Exception:
        return GoogleSpeechBackend() if has_pyaudio else SoundDeviceGoogleBackend(device=_input_device_from_settings(settings))


def listen_once(
    settings: dict | None = None,
    backend: str | None = None,
    timeout: int = 5,
    phrase_time_limit: int = 10,
) -> VoiceResult:
    cfg = settings or {}
    chosen = backend or cfg.get("voice_backend", "auto")
    language = cfg.get("voice_language", "pt-BR")
    recognizer = _create_backend(chosen, cfg)
    try:
        vosk_language = cfg.get("voice_language_vosk", "pt")
        if recognizer.name == "vosk":
            return recognizer.listen_once(timeout=timeout, phrase_time_limit=phrase_time_limit, language=vosk_language)
        return recognizer.listen_once(timeout=timeout, phrase_time_limit=phrase_time_limit, language=language)
    except Exception as original_error:
        if recognizer.name != "sounddevice-google":
            try:
                fallback = SoundDeviceGoogleBackend(device=_input_device_from_settings(cfg))
                return fallback.listen_once(timeout=timeout, phrase_time_limit=phrase_time_limit, language=language)
            except Exception as sounddevice_error:
                original_error = sounddevice_error
                pass

        if recognizer.name != "google" and _has_pyaudio():
            fallback = GoogleSpeechBackend()
            return fallback.listen_once(timeout=timeout, phrase_time_limit=phrase_time_limit, language=language)

        detail = str(original_error).strip() or original_error.__class__.__name__
        raise RuntimeError(
            "Backend de voz sounddevice falhou. "
            f"Detalhe: {detail}. "
            "PyAudio nao esta instalado, entao o fallback antigo foi desativado."
        ) from original_error


def listen_text(
    settings: dict | None = None,
    backend: str | None = None,
    timeout: int = 5,
    phrase_time_limit: int = 10,
) -> str:
    result = listen_once(settings=settings, backend=backend, timeout=timeout, phrase_time_limit=phrase_time_limit)
    return (result.text or "").strip()
