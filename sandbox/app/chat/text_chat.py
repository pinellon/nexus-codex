import logging

class TextChat:
    def __init__(self, settings, logger=None):
        self.settings = settings
        self.logger = logger or logging.getLogger(__name__)
        self.command_router = CommandRouter(settings=settings, logger=logger)

    def handle_input(self, text):
        try:
            self.logger.info(f'Recebido texto do usuário: {text}')
            command = self.command_router.route(text)
            response = self.process_command(command)
            return response
        except Exception as e:
            self.logger.error(f'Erro ao processar entrada de texto: {str(e)}')
            return 'Desculpe, ocorreu um erro ao processar seu pedido.'

    def process_command(self, command):
        return f'Comando processado: {command.label} com argumentos {command.args}'