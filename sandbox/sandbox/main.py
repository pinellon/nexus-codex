# main.py

"""Launcher principal do NEXUS.

Por padrão, abre a interface visual. Use `python main.py --voice-demo` para
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


def parse_arguments():
    """Parses command line arguments."""
    parser = argparse.ArgumentParser(prog="nexus")
    parser.add_argument(
        "--voice-demo",
        action="store_true",
        help="Executa loop de voz no terminal",
    )
    return parser.parse_args()


def initialize_components(settings, logger):
    """Initialize voice components and command router"""
    listener = VoiceListener(settings=settings, logger=logger)
    speaker = VoiceSpeaker(settings=settings, logger=logger)
    router = CommandRouter(settings=settings, logger=logger)
    return listener, speaker, router


def run_voice_demo():
    """Runs the voice demo mode."""
    settings = load_settings()
    logger = build_logger(settings.log_file)
    listener, speaker, router = initialize_components(settings, logger)

    speaker.speak("NEXUS online. Modo demo de voz.")
    while True:
        text = listener.listen_once()
        if not text:
            continue
        command = router.route(text)
        print(f"OUVI: {text}")
        print(f"ENTENDI: {command.label} {command.args}")
        if command.intent in {"sleep", "parar", "sair"}:
            break


def main():
    args = parse_arguments()
    if args.voice_demo:
        run_voice_demo()
    else:
        ui_main()


if __name__ == "__main__":
    main()