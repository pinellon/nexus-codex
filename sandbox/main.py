# main.py

"Launcher principal do NEXUS."

from __future__ import annotations

import argparse
from app.config import load_settings
from app.logs.nexus_logger import build_logger
from app.voice.listener import VoiceListener
from app.voice.speaker import VoiceSpeaker
from app.core.command_router import CommandRouter
from theme import main as ui_main

VOICE_DEMO_MESSAGE = "NEXUS online. Modo demo de voz."
EXIT_COMMANDS = {"sleep", "parar", "sair"}


def run_voice_demo(settings, logger):
    listener = VoiceListener(settings=settings, logger=logger)
    speaker = VoiceSpeaker(settings=settings, logger=logger)
    router = CommandRouter(settings=settings, logger=logger)

    speaker.speak(VOICE_DEMO_MESSAGE)
    try:
        while True:
            text = listener.listen_once()
            if text:
                command = router.route(text)
                print(f"OUVI: {text}")
                print(f"ENTENDI: {command.label} {command.args}")
                if command.intent in EXIT_COMMANDS:
                    break
    finally:
        logger.close()


def parse_arguments():
    parser = argparse.ArgumentParser(prog="nexus")
    parser.add_argument("--voice-demo", action="store_true", help="roda loop de voz no terminal")
    return parser.parse_args()


def setup_environment():
    settings = load_settings()
    logger = build_logger(settings.log_file)
    return settings, logger


def main():
    args = parse_arguments()
    settings, logger = setup_environment()

    if args.voice_demo:
        run_voice_demo(settings, logger)
    else:
        ui_main()


if __name__ == "__main__":
    main()
