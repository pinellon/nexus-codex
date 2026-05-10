class ChatInterface:
    def __init__(self, settings, logger, command_router):
        self.settings = settings
        self.logger = logger
        self.router = command_router

    def start_chat(self):
        print("\n--- BEM-VINDO AO CHAT DO NEXUS ---\n")
        while True:
            user_input = input("Você: ")
            if not user_input.strip():
                continue
            command = self.router.route(user_input)
            response = self._generate_response(command)
            print(f"NEXUS: {response}")
            if command.intent in {"sleep", "parar", "sair"}:
                print("Encerrando chat...")
                break

    def _generate_response(self, command):
        # Lógica simples de resposta
        return f"Processado comando: {command.label} {command.args}"
