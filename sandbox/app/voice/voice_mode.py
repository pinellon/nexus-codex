from __future__ import annotations
import signal
from app.voice.listener import VoiceListener
from app.voice.speaker import VoiceSpeaker
from app.core.command_router import CommandRouter
from app.logs.nexus_logger import build_logger

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

def handle_exit(signum, frame):
    print('Exiting gracefully...')
    exit(0)

def process_command(text, router, speaker, logger):
    command = router.route(text)
    print(f"OUVI: {text}")
    print(f"ENTENDI: {command.label} {command.args}")
    if command.intent in {"sleep", "parar", "sair"}:
        print('Exiting voice loop...')
        return False
    return True

def execute_voice_loop(listener, speaker, router, logger):
    signal.signal(signal.SIGINT, handle_exit)
    speaker.speak("NEXUS online. Modo demo de voz.")
    try:
        while True:
            text = listener.listen_once()
            if not text:
                continue
            if not process_command(text, router, speaker, logger):
                break
    except Exception as e:
        logger.error(f"Erro no loop de voz: {e}")
    finally:
        listener.cleanup()
        speaker.cleanup()

def init_voice_mode(settings):
    listener, speaker, router = create_voice_components(settings)
    logger = create_logger(settings)
    execute_voice_loop(listener, speaker, router, logger)
