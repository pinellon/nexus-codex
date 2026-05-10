# chat_interface.py

from app.config import load_settings
from app.logs.nexus_logger import build_logger
from app.core.command_router import CommandRouter


class ChatInterface:
    def __init__(self, settings, logger):
        self.settings = settings
        self.logger = logger
        self.router = CommandRouter(settings=settings, logger=logger)

    def start_chat(self):
        print("NEXUS online. Modo de chat.")
        while True:
            try:
                text = input("You: ")
                if not text:
                    continue
                command = self.router.route(text)
                print(f"NEXUS: {command.label} {command.args}")
                if command.intent in {"sleep", "parar", "sair"}:
                    break
            except Exception as e:
                self.logger.error(f"Erro durante a execução do chat: {str(e)}")


def main():
    settings = load_settings()
    logger = build_logger(settings.log_file)
    chat_interface = ChatInterface(settings=settings, logger=logger)
    chat_interface.start_chat()


if __name__ == "__main__":
    main()
