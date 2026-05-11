# ./app/voice/voice_components.py

from app.logs.nexus_logger import build_logger
from app.voice.listener import VoiceListener
from app.voice.speaker import VoiceSpeaker
from app.core.command_router import CommandRouter

def create_logger(settings):
    """Create a logger with provided settings."""
    return build_logger(settings.log_file)


def create_voice_listener(settings, logger):
    """Initialize a voice listener component."""
    return VoiceListener(settings=settings, logger=logger)


def create_voice_speaker(settings, logger):
    """Initialize a voice speaker component."""
    return VoiceSpeaker(settings=settings, logger=logger)


def create_command_router(settings, logger):
    """Setup the command router to handle voice input."""
    return CommandRouter(settings=settings, logger=logger)


def create_voice_components(settings):
    """Aggregate creation of voice components with logging."""
    logger = create_logger(settings)
    return {
        "listener": create_voice_listener(settings, logger),
        "speaker": create_voice_speaker(settings, logger),
        "router": create_command_router(settings, logger),
        "logger": logger
    }
