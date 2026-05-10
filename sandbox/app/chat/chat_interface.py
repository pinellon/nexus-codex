# chat_interface.py

from app.core.command_router import CommandRouter

class ChatInterface:
    def __init__(self, settings, logger):
        self.router = CommandRouter(settings=settings, logger=logger)
        self.logger = logger

    def start_chat(self):
        print("NEXUS online. Modo chat ativado.")
        while True:
            try:
                user_input = input("Você: ")
                if not user_input:
                    continue
                command = self.router.route(user_input)
                print(f"ENTENDI: {command.label} {command.args}")
                if command.intent in {"sleep", "parar", "sair"}:
                    print("Encerrando o chat...")
                    break
            except Exception as e:
                self.logger.error(f"Erro durante a execução do chat: {str(e)}")