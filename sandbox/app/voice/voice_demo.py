# app/voice/voice_demo.py

"""Módulo dedicado para a demonstração de comandos de voz do NEXUS."""

from app.voice.listener import VoiceListener
from app.voice.speaker import VoiceSpeaker
from app.core.command_router import CommandRouter
from app.logs.nexus_logger import Logger
from app.chat.chat_engine import ChatEngine

VOICE_DEMO_MESSAGE = "NEXUS online. Modo demo de voz."

def handle_voice_commands(listener: VoiceListener, 
                          speaker: VoiceSpeaker, 
                          router: CommandRouter):
    """Handles voice commands in a loop."""
    while True:
        text = listener.listen_once()
        if text:
            command = router.route(text)
            print(f"OUVI: {text}")
            print(f"ENTENDI: {command.label} {command.args}")
            if ChatEngine.is_exit_request(text, command, router=router):
                break

def run_voice_demo(settings, logger: Logger):
    listener = VoiceListener(settings=settings, logger=logger)
    speaker = VoiceSpeaker(settings=settings, logger=logger)
    router = CommandRouter(settings=settings, logger=logger)

    speaker.speak(VOICE_DEMO_MESSAGE)
    try:
        handle_voice_commands(listener, speaker, router)
    finally:
        logger.close()
