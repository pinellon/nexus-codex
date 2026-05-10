# voice_demo.py

"""
Este módulo contém a lógica do loop da demonstração de voz.
"""

from app.voice.listener import VoiceListener
from app.voice.speaker import VoiceSpeaker
from app.core.command_router import CommandRouter

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
