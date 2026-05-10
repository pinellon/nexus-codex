import signal


def handle_exit(signum, frame):
    print('Exiting gracefully...')
    exit(0)


def execute_voice_loop(listener, speaker, router):
    signal.signal(signal.SIGINT, handle_exit)
    speaker.speak('NEXUS online. Modo demo de voz.')
    try:
        while True:
            text = listener.listen_once()
            if not text:
                continue
            command = router.route(text)
            print(f'OUVI: {text}')
            print(f'ENTENDI: {command.label} {command.args}')
            if command.intent in {'sleep', 'parar', 'sair'}:
                print('Exiting voice loop...')
                break
    except Exception as e:
        logger.error(f'Erro no loop de voz: {e}')
    finally:
        listener.cleanup()
        speaker.cleanup()


# Use essa função para inicializar o modo de voz a partir de main.py
# def init_voice_mode(settings):
#     listener, speaker, router = create_voice_components(settings)
#     execute_voice_loop(listener, speaker, router)
