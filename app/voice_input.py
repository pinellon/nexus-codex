"""Entrada de voz opcional por microfone."""


def ouvir_microfone() -> str:
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
        return recognizer.recognize_google(audio, language="pt-BR")
    except Exception as error:
        raise RuntimeError(f"Não consegui ouvir o microfone: {error}") from error

