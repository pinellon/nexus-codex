# chat_handler.py

"""
Módulo responsável por lidar com interações de chat textual no NEXUS.
"""

from app.core.command_router import CommandRouter

class ChatHandler:
    def __init__(self, settings, logger):
        self.logger = logger
        self.router = CommandRouter(settings=settings, logger=logger)

    def process_input(self, text: str):
        """Processa a entrada de texto do usuário e retorna uma resposta."""
        try:
            command = self.router.route(text)
            response = self.generate_response(command)
            self.logger.info(f"PROCESSADO: {command.label} {command.args}")
            return response
        except Exception as e:
            self.logger.error(f"Erro ao processar chat: {str(e)}")
            return "Ocorreu um erro. Tente novamente."

    def generate_response(self, command):
        """Gera uma resposta com base no comando interpretado."""
        # Esta função poderia ser expandida para realizar ações e gerar respostas mais dinâmicas
        return f"Comando {command.label} recebido com argumentos {command.args}."