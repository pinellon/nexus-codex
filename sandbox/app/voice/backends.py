"""Backends de reconhecimento de voz para o NEXUS."""

from __future__ import annotations

from dataclasses import dataclass
import json


@dataclass
class VoiceResult:
    text: str
    backend: str
    confidence: float | None = None


class VoiceBackend:
    name = "base"

    def listen_once(self, timeout: int = 5, phrase_time_limit: int = 10, language: str = "pt-BR") -> VoiceResult:
        raise NotImplementedError


class GoogleSpeechBackend(VoiceBackend):
    name = "google"

    def listen_once(self, timeout: int = 5, phrase_time_limit: int = 10, language: str = "pt-BR") -> VoiceResult:
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
        text = recognizer.recognize_google(audio, language=language)
        return VoiceResult(text=text, backend=self.name)


class SoundDeviceGoogleBackend(VoiceBackend):
    name = "sounddevice-google"

    def __init__(self, device: int | None = None):
        self.device = device

    def listen_once(self, timeout: int = 5, phrase_time_limit: int = 10, language: str = "pt-BR") -> VoiceResult:
        import numpy as np
        import sounddevice as sd
        import speech_recognition as sr

        duration = max(1, min(int(phrase_time_limit or timeout or 5), 20))
        try:
            device = self.device if self.device is not None else sd.default.device[0]
            info = sd.query_devices(device, "input")
        except Exception:
            device = self.device
            info = sd.query_devices(kind="input")

        sample_rate = int(info.get("default_samplerate") or 16000)
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="int16",
            device=device,
        )
        sd.wait()

        samples = np.asarray(recording, dtype=np.int16).reshape(-1).astype(np.float32)
        samples -= float(np.mean(samples))
        peak = float(np.max(np.abs(samples))) if samples.size else 0.0
        rms = float(np.sqrt(np.mean(samples * samples))) if samples.size else 0.0
        if peak < 80 or rms < 12:
            return VoiceResult(text="", backend=self.name, confidence=0.0)

        gain = min(12.0, 26000.0 / peak)
        samples = np.clip(samples * gain, -32768, 32767).astype(np.int16)
        audio_bytes = samples.tobytes()
        if not audio_bytes.strip(b"\x00"):
            return VoiceResult(text="", backend=self.name, confidence=0.0)

        audio = sr.AudioData(audio_bytes, sample_rate, 2)
        try:
            text = sr.Recognizer().recognize_google(audio, language=language)
        except sr.UnknownValueError:
            return VoiceResult(text="", backend=self.name, confidence=0.0)
        return VoiceResult(text=text, backend=self.name)


class VoskBackend(VoiceBackend):
    name = "vosk"

    def listen_once(self, timeout: int = 5, phrase_time_limit: int = 10, language: str = "pt") -> VoiceResult:
        import speech_recognition as sr

        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

        raw = recognizer.recognize_vosk(audio, language=language)
        if isinstance(raw, str):
            try:
                parsed = json.loads(raw)
                text = parsed.get("text", "")
            except json.JSONDecodeError:
                text = raw
        else:
            text = str(raw)
        return VoiceResult(text=text, backend=self.name)
