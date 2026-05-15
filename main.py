# main.py

import argparse

from app.chat.chat_engine import ChatEngine
from app.config import load_settings
from app.core.command_router import CommandRouter
from app.logs.nexus_logger import build_logger
from app.voice.listener import VoiceListener
from app.voice.speaker import VoiceSpeaker
import theme

# Constante de inicializacao da aplicacao.
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
    """Executa o modo demo de voz no terminal."""
    listener = VoiceListener(settings=settings, logger=logger)
    speaker = VoiceSpeaker(settings=settings, logger=logger)
    router = CommandRouter(settings=settings, logger=logger)

    speaker.speak(VOICE_DEMO_MESSAGE)
    try:
        handle_voice_commands(listener, speaker, router)
    finally:
        logger.close()


def parse_arguments() -> argparse.Namespace:
    """Analisa os argumentos CLI fornecidos na execucao do script."""
    parser = argparse.ArgumentParser(prog="nexus")
    parser.add_argument("--voice-demo", action="store_true", help="roda loop de voz no terminal")
    parser.add_argument("--web-api", action="store_true", help="roda a API HTTP da interface web")
    parser.add_argument("--desktop", action="store_true", help="roda a interface desktop legada em CustomTkinter")
    parser.add_argument("--host", default="127.0.0.1", help="host usado pela API web")
    parser.add_argument("--port", type=int, default=8001, help="porta usada pela API web")
    return parser.parse_args()


def setup_environment() -> tuple:
    """Carrega as configuracoes e inicia o subsistema de logging."""
    settings = load_settings()
    logger = build_logger(settings.log_file)
    return settings, logger


def execute_mode(args: argparse.Namespace, settings, logger):
    """Seleciona e executa o modo de operacao com base nos argumentos fornecidos."""
    if args.voice_demo:
        run_voice_demo(settings, logger)
    elif args.desktop:
        theme.main()
    else:
        from app.web.server import run as run_web_api

        run_web_api(host=args.host, port=args.port)


def main():
    """Ponto de entrada principal do script."""
    args = parse_arguments()
    settings, logger = setup_environment()
    execute_mode(args, settings, logger)


if __name__ == "__main__":
    main()
