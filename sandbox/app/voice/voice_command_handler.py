# voice_command_handler.py

from app.voice.listener import VoiceListener
from app.voice.speaker import VoiceSpeaker
from app.core.command_router import CommandRouter
from app.chat.chat_engine import ChatEngine

class VoiceCommandHandler:

    def __init__(self, listener: VoiceListener, speaker: VoiceSpeaker, router: CommandRouter):
        self.listener = listener
        self.speaker = speaker
        self.router = router

    def handle_voice_commands(self):
        """Handles voice commands continuously."""
        while True:
            text = self.listener.listen_once()
            if text:
                command = self.router.route(text)
                print(f"OUVI: {text}")
                print(f"ENTENDI: {command.label} {command.args}")
                if ChatEngine.is_exit_request(text, command, router=self.router):
                    break
