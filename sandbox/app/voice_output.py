"""Compatibilidade com chamadas antigas de fala do NEXUS."""

import threading


def falar(texto: str, use_edge: bool = False, engine: str | None = None, settings: dict | None = None):
    if not texto or texto.strip() == ".":
        return
    chosen_engine = engine or ("edge-tts" if use_edge else None)
    threading.Thread(target=_speak, args=(texto, chosen_engine, settings), daemon=True).start()


def _speak(texto: str, engine: str | None = None, settings: dict | None = None):
    from app.voice import VoiceEngine

    _voice = VoiceEngine(engine=engine, settings=settings)
    _voice.speak(texto)
