import argparse
from app.voice_demo import run_voice_demo
import theme

def parse_arguments() -> argparse.Namespace:
    """Análise dos argumentos CLI fornecidos na execução do script."""
    parser = argparse.ArgumentParser(prog="nexus")
    parser.add_argument("--voice-demo", action="store_true", help="roda loop de voz no terminal")
    return parser.parse_args()


def execute_mode(args: argparse.Namespace, settings, logger):
    """Seleciona e executa o modo de operação com base nos argumentos fornecidos."""
    if args.voice_demo:
        run_voice_demo(settings, logger)
    else:
        theme.main()