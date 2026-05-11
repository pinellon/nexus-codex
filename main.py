# main.py

"Launcher principal do NEXUS."

from __future__ import annotations

import argparse
import app.config
import app.logs.nexus_logger
import app.voice.listener
import app.voice.speaker
import app.core.command_router
from app.chat.chat_engine import ChatEngine
import theme

VOICE_DEMO_MESSAGE = "NEXUS online. Modo demo de voz."


def handle_voice_commands(listener: app.voice.listener.VoiceListener, 
                          speaker: app.voice.speaker.VoiceSpeaker, 
                          router: app.core.command_router.CommandRouter):
    """Handles voice commands in a loop."""
    while True:
        text = listener.listen_once()
        if text:
            command = router.route(text)
            print(f"OUVI: {text}")
            print(f"ENTENDI: {command.label} {command.args}")
            if ChatEngine.is_exit_request(text, command, router=router):
                break


def run_voice_demo(settings: app.config.Settings, logger: app.logs.nexus_logger.Logger):
    listener = app.voice.listener.VoiceListener(settings=settings, logger=logger)
    speaker = app.voice.speaker.VoiceSpeaker(settings=settings, logger=logger)
    router = app.core.command_router.CommandRouter(settings=settings, logger=logger)

    speaker.speak(VOICE_DEMO_MESSAGE)
    try:
        handle_voice_commands(listener, speaker, router)
    finally:
        logger.close()


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="nexus")
    parser.add_argument("--voice-demo", action="store_true", help="roda loop de voz no terminal")
    return parser.parse_args()


def setup_environment() -> tuple[app.config.Settings, app.logs.nexus_logger.Logger]:
    settings = app.config.load_settings()
    logger = app.logs.nexus_logger.build_logger(settings.log_file)
    return settings, logger


def execute_mode(args: argparse.Namespace, settings: app.config.Settings, logger: app.logs.nexus_logger.Logger):
    if args.voice_demo:
        run_voice_demo(settings, logger)
    else:
        theme.main()


def main():
    args = parse_arguments()
    settings, logger = setup_environment()
    execute_mode(args, settings, logger)


if __name__ == "__main__":
    main()
