"""Compatibilidade com chamadas antigas de fala do NEXUS."""

import threading


_voice = None


def falar(texto: str, use_edge: bool = False, engine: str | None = None, settings: dict | None = None):
    if not texto or texto.strip() == ".":
        return
    threading.Thread(target=_speak, args=(texto,), daemon=True).start()


def _speak(texto: str):
    global _voice
    from app.voice import VoiceEngine

    if _voice is None:
        _voice = VoiceEngine()
    _voice.speak(texto)
