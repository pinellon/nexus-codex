# main.py

"""Launcher principal do NEXUS.

Por padrao abre a interface visual. Use `python main.py --voice-demo` para
testar o modo de voz em terminal.
"""

from __future__ import annotations

import argparse
from app.config import load_settings
from app.logs.nexus_logger import build_logger
from app.voice.listener import VoiceListener
from app.voice.speaker import VoiceSpeaker
from app.core.command_router import CommandRouter
from theme import main as ui_main


def run_voice_demo(settings, logger):
    listener = VoiceListener(settings=settings, logger=logger)
    speaker = VoiceSpeaker(settings=settings, logger=logger)
    router = CommandRouter(settings=settings, logger=logger)

    speaker.speak("NEXUS online. Modo demo de voz.")
    while True:
        try:
            text = listener.listen_once()
            if not text:
                continue
            command = router.route(text)
            print(f"OUVI: {text}")
            print(f"ENTENDI: {command.label} {command.args}")
            if command.intent in {"sleep", "parar", "sair"}:
                break
        except Exception as e:
            logger.error(f"Erro durante a execução do loop de voz: {str(e)}")


def main():
    parser = argparse.ArgumentParser(prog="nexus")
    parser.add_argument("--voice-demo", action="store_true", help="roda loop de voz no terminal")
    args = parser.parse_args()

    settings = load_settings()
    logger = build_logger(settings.log_file)

    if args.voice_demo:
        run_voice_demo(settings, logger)
    else:
        ui_main()


if __name__ == "__main__":
    main()
