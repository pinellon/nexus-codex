from app.config import load_settings
from app.logs.nexus_logger import build_logger
from app.voice.listener import VoiceListener
from app.voice.speaker import VoiceSpeaker
from app.core.command_router import CommandRouter

def run_voice_demo():
    settings = load_settings()
    logger = build_logger(settings.log_file)
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
            logger.error(f"Erro no loop de voz: {e}")
            speaker.speak("Desculpe, ocorreu um erro. Por favor, tente novamente.")