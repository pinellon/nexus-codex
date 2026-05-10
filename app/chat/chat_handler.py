
class ChatHandler:
    def __init__(self, settings, logger, command_router):
        self.settings = settings
        self.logger = logger
        self.command_router = command_router

    def handle_message(self, message):
        try:
            command = self.command_router.route(message)
            response = self.process_command(command)
            return response
        except Exception as e:
            self.logger.error(f"Erro ao processar mensagem: {str(e)}")
            return "Houve um erro ao processar sua mensagem."

    def process_command(self, command):
        # Adiciona lógica específica de comando. No momento, retornará o rótulo do comando e os argumentos.
        return f"Comando: {command.label}, Args: {command.args}"
