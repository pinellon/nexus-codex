import argparse
from app.voice_demo import run_voice_demo
import theme

def parse_arguments() -> argparse.Namespace:
    """Análise dos argumentos CLI fornecidos na execução do script."""
    parser = argparse.ArgumentParser(prog="nexus")
    parser.add_argument("--voice-demo", action="store_true", help="roda loop de voz no terminal")
    parser.add_argument("--desktop", action="store_true", help="roda a interface desktop legada")
    parser.add_argument("--host", default="127.0.0.1", help="host usado pela API web")
    parser.add_argument("--port", type=int, default=8001, help="porta usada pela API web")
    return parser.parse_args()


def execute_mode(args: argparse.Namespace, settings, logger):
    """Seleciona e executa o modo de operação com base nos argumentos fornecidos."""
    if args.voice_demo:
        run_voice_demo(settings, logger)
    elif args.desktop:
        theme.main()
    else:
        from app.web.server import run as run_web_api

        run_web_api(host=args.host, port=args.port)
