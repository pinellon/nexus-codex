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
