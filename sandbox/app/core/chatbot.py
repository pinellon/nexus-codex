# app/core/chatbot.py

class ChatBot:
    def __init__(self, settings, logger):
        self.settings = settings
        self.logger = logger

    def process_input(self, text):
        # Log the received input
        self.logger.info(f'Received input: {text}')
        
        # Basic response logic, can be expanded with NLP techniques
        if 'hello' in text.lower():
            return 'Hello! How can I assist you today?'
        elif 'how are you' in text.lower():
            return 'I am just a bunch of code, but thanks for asking!'
        elif 'bye' in text.lower():
            return 'Goodbye! Have a great day!'
        else:
            return "I'm sorry, I didn't quite catch that. Could you repeat?"
