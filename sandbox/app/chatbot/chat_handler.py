class ChatHandler:
    def __init__(self, settings, logger):
        self.settings = settings
        self.logger = logger

    def process_message(self, message):
        # Simulate processing a chat message and generating a response
        response = f'Processed message: {message}'
        self.logger.info(f'ChatHandler processed message: {message} -> {response}')
        return response
