import argparse
from app.config import load_settings
from app.logs.nexus_logger import build_logger
from app.voice.listener import VoiceListener
from app.voice.speaker import VoiceSpeaker
from app.core.command_router import CommandRouter
from app.chat.chat_engine import ChatEngine
import theme

# Constante de inicialização da aplicação.
VOICE_DEMO_MESSAGE = "NEXUS online. Modo demo de voz."


def handle_voice_commands(listener: VoiceListener, speaker: VoiceSpeaker, router: CommandRouter):
    """Handles voice commands in a loop."""
    while True:
        text = listener.listen_once()
        if text:
            command = router.route(text)
            print(f"OUVI: {text}")
            print(f"ENTENDI: {command.label} {command.args}")
            if ChatEngine.is_exit_request(text, command, router=router):
                break


def run_voice_demo(settings, logger):
    """Execução do modo demo de voz, inicializa os componentes principais do sistema de voz."""
    listener = VoiceListener(settings=settings, logger=logger)
    speaker = VoiceSpeaker(settings=settings, logger=logger)
    router = CommandRouter(settings=settings, logger=logger)

    speaker.speak(VOICE_DEMO_MESSAGE)
    try:
        handle_voice_commands(listener, speaker, router)
    finally:
        logger.close()


def parse_arguments() -> argparse.Namespace:
    """Análise dos argumentos CLI fornecidos na execução do script."""
    parser = argparse.ArgumentParser(prog="nexus")
    parser.add_argument("--voice-demo", action="store_true", help="roda loop de voz no terminal")
    return parser.parse_args()


def setup_environment() -> tuple:
    """Carrega as configurações e inicia o subsistema de logging."""
    settings = load_settings()
    logger = build_logger(settings.log_file)
    return settings, logger


def execute_mode(args: argparse.Namespace, settings, logger):
    """Seleciona e executa o modo de operação com base nos argumentos fornecidos."""
    if args.voice_demo:
        run_voice_demo(settings, logger)
    else:
        theme.main()


def main():
    """Ponto de entrada principal do script."""
    args = parse_arguments()
    settings, logger = setup_environment()
    execute_mode(args, settings, logger)


if __name__ == "__main__":
    main()
