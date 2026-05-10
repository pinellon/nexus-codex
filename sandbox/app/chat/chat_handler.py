# chat_handler.py

from transformers import pipeline
import logging

class ChatHandler:
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.chatbot = pipeline("conversational", model="facebook/blenderbot-400M-distill")

    def handle_message(self, user_message: str) -> str:
        try:
            response = self.chatbot(user_message)
            return response["generated_responses"][0]
        except Exception as e:
            self.logger.error(f"Erro ao processar a mensagem de chat: {str(e)}")
            return "Desculpe, não consegui processar sua solicitação no momento."
