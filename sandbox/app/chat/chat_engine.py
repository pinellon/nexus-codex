# chat_engine.py

from app.core.command_router import CommandRouter
from app.voice.speaker import VoiceSpeaker

class ChatEngine:
    def __init__(self, settings, logger):
        self.settings = settings
        self.logger = logger
        self.router = CommandRouter(settings=settings, logger=logger)
        self.speaker = VoiceSpeaker(settings=settings, logger=logger)

    def process_input(self, text: str):
        command = self.router.route(text)
        response = self._generate_response(command)
        self.speaker.speak(response)
        return {
            "command": command,
            "response": response
        }

    def _generate_response(self, command):
        # Placeholder for more complex response logic
        return f"Processing command: {command.label}"
