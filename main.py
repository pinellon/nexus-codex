from __future__ import annotations
import argparse
from theme import main as ui_main
from app.config import load_settings
from app.logs.nexus_logger import build_logger
from app.voice.listener import VoiceListener
from app.voice.speaker import VoiceSpeaker
from app.core.command_router import CommandRouter


def create_logger(settings):
    return build_logger(settings.log_file)


def create_voice_listener(settings, logger):
    return VoiceListener(settings=settings, logger=logger)


def create_voice_speaker(settings, logger):
    return VoiceSpeaker(settings=settings, logger=logger)


def create_command_router(settings, logger):
    return CommandRouter(settings=settings, logger=logger)


def create_voice_components(settings):
    logger = create_logger(settings)
    listener = create_voice_listener(settings, logger)
    speaker = create_voice_speaker(settings, logger)
    router = create_command_router(settings, logger)
    return listener, speaker, router


def execute_voice_loop(listener, speaker, router):
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


def init_voice_mode(settings):
    listener, speaker, router = create_voice_components(settings)
    execute_voice_loop(listener, speaker, router)


def parse_arguments():
    parser = argparse.ArgumentParser(prog="nexus")
    parser.add_argument("--voice-demo", action="store_true", help="roda loop de voz no terminal")
    args = parser.parse_args()
    return args


def main():
    args = parse_arguments()
    settings = load_settings()
    if args.voice_demo:
        init_voice_mode(settings)
    else:
        ui_main()


if __name__ == "__main__":
    main()