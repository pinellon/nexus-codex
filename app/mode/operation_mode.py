# app/mode/operation_mode.py

import app.config
import app.logs.nexus_logger
import app.voice.listener
import app.voice.speaker
import app.core.command_router
import theme

VOICE_DEMO_MESSAGE = 'NEXUS online. Modo demo de voz.'


def handle_voice_commands(listener: app.voice.listener.VoiceListener,
                          speaker: app.voice.speaker.VoiceSpeaker,
                          router: app.core.command_router.CommandRouter):
    """Handles voice commands in a loop."""
    while True:
        text = listener.listen_once()
        if text:
            command = router.route(text)
            print(f"OUVI: {text}")
            print(f"ENTENDI: {command.label} {command.args}")
            if app.chat.chat_engine.ChatEngine.is_exit_request(text, command, router=router):
                break


def run_voice_demo(settings: app.config.Settings, logger: app.logs.nexus_logger.Logger):
    """Execução do modo demo de voz, inicializa os componentes principais do sistema de voz."""
    listener = app.voice.listener.VoiceListener(settings=settings, logger=logger)
    speaker = app.voice.speaker.VoiceSpeaker(settings=settings, logger=logger)
    router = app.core.command_router.CommandRouter(settings=settings, logger=logger)

    speaker.speak(VOICE_DEMO_MESSAGE)
    try:
        handle_voice_commands(listener, speaker, router)
    finally:
        logger.close()


def execute_mode(args: argparse.Namespace, settings: app.config.Settings, logger: app.logs.nexus_logger.Logger):
    """Seleciona e executa o modo de operação com base nos argumentos fornecidos."""
    if args.voice_demo:
        run_voice_demo(settings, logger)
    else:
        theme.main()
