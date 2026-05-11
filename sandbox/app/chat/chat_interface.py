from __future__ import annotations

from app.chat.chat_engine import ChatEngine
from app.config import load_settings
from app.logs.nexus_logger import build_logger


class ChatInterface:
    def __init__(self, settings, logger, engine: ChatEngine | None = None):
        self.settings = settings
        self.logger = logger
        self.engine = engine or ChatEngine(settings=settings, logger=logger)

    def start_chat(self):
        self._print_banner()
        while True:
            try:
                text = input("Voce> ").strip()
                if not text:
                    continue

                result = self.engine.process_input(text, speak=False)
                print(f"Entendi> {result['understood']}")
                print(f"NEXUS> {result['response']}\n")

                if result["should_exit"]:
                    break
            except KeyboardInterrupt:
                print("\nNEXUS> Encerrando chat.\n")
                break
            except Exception as error:
                self.logger.error("Erro durante a execucao do chat: %s", error)
                print("NEXUS> Ocorreu um erro ao processar sua mensagem.\n")

    @staticmethod
    def _print_banner():
        print("NEXUS online. Modo de chat.")
        print("Digite comandos, perguntas ou automacoes.")
        print("Use 'sair' para encerrar.\n")


def main():
    settings = load_settings()
    logger = build_logger(settings.log_file)
    chat_interface = ChatInterface(settings=settings, logger=logger)
    chat_interface.start_chat()


if __name__ == "__main__":
    main()
