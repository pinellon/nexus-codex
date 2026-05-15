class FeedbackLoop:
    def __init__(self, router, listener, speaker, logger):
        self.router = router
        self.listener = listener
        self.speaker = speaker
        self.logger = logger

    def start(self):
        self.speaker.speak("Entrando no modo de aprendizado continuo. Forneca feedback apos cada comando.")
        while True:
            text = self.listener.listen_once()
            if not text:
                continue
            command = self.router.route(text)
            print(f"OUVI: {text}")
            print(f"ENTENDI: {command.label} {command.args}")
            self.speaker.speak(f"Voce quis dizer: {command.label}? Responda 'sim' ou 'nao'.")
            feedback = self.listener.listen_once().lower()
            if feedback in {"sim", "yes"}:
                self.logger.info(f"Feedback positivo para comando: {command}")
            else:
                self.speaker.speak("Por favor, diga novamente o comando correto.")
                corrected_text = self.listener.listen_once()
                if corrected_text:
                    corrected_command = self.router.route(corrected_text)
                    self.logger.info(f"Correcao recebida: {corrected_command}")
            if command.intent in {"sleep", "parar", "sair"}:
                break
