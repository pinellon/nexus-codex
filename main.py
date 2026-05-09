from __future__ import annotations
import argparse
import signal
from theme import main as ui_main
from app.config import load_settings
from app.logs.nexus_logger import build_logger
from app.voice.listener import VoiceListener
from app.voice.speaker import VoiceSpeaker
from app.core.command_router import CommandRouter


def create_logger(settings):
    """Create a logger with provided settings."""
    return build_logger(settings.log_file)


def create_voice_listener(settings):
    """Initialize a voice listener component."""
    return VoiceListener(settings=settings, logger=create_logger(settings))


def create_voice_speaker(settings):
    """Initialize a voice speaker component."""
    return VoiceSpeaker(settings=settings, logger=create_logger(settings))


def create_command_router(settings):
    """Setup the command router to handle voice input."""
    return CommandRouter(settings=settings, logger=create_logger(settings))


class VoiceComponents:
    def __init__(self, settings):
        self.logger = create_logger(settings)
        self.listener = create_voice_listener(settings)
        self.speaker = create_voice_speaker(settings)
        self.router = create_command_router(settings)


def handle_exit(signum, frame):
    """Handle clean exit on receiving a system interrupt."""
    print('Exiting gracefully...')
    exit(0)


def process_command(text, components):
    """Process voice command via router and execute its action if valid."""
    command = components.router.route(text)
    print(f"OUVI: {text}")
    print(f"ENTENDI: {command.label} {command.args}")
    if command.intent in {"sleep", "parar", "sair"}:
        print('Exiting voice loop...')
        return False
    return True


def execute_voice_loop(components):
    """Run the interactive voice loop interfacing all components."""
    signal.signal(signal.SIGINT, handle_exit)
    components.speaker.speak("NEXUS online. Modo demo de voz.")
    try:
        while True:
            text = components.listener.listen_once()
            if not text:
                continue
            if not process_command(text, components):
                break
    except Exception as e:
        components.logger.error(f"Erro no loop de voz: {e}")
    finally:
        components.listener.cleanup()
        components.speaker.cleanup()


def init_voice_mode(settings):
    """Initialize and commence voice interaction mode."""
    components = VoiceComponents(settings)
    execute_voice_loop(components)


def parse_arguments():
    """Parse command line arguments for Nexus setup."""
    parser = argparse.ArgumentParser(prog="nexus")
    parser.add_argument("--voice-demo", action="store_true", help="roda loop de voz no terminal")
    args = parser.parse_args()
    return args


def main():
    """Main function to start the Nexus application with appropriate mode."""
    args = parse_arguments()
    settings = load_settings()
    if args.voice_demo:
        init_voice_mode(settings)
    else:
        ui_main()