"""
app/voice.py
Voz do Nexus com ElevenLabs + fallback para voz do sistema.
"""

from __future__ import annotations

import os
import tempfile
import time

import pyttsx3
import requests
from dotenv import load_dotenv

from app.config import config
from app.logger import logger
from app.settings_manager import load as load_settings

load_dotenv()


class VoiceEngine:
    def __init__(self):
        self.enabled = bool(config.get("voice.enabled", True))
        self.provider = config.get("voice.provider", "system")
        self.system_engine = None
        self.pygame_ready = False

        if self.provider == "system":
            self.init_system_voice()

        if self.provider == "elevenlabs":
            self.init_audio_player()

    def init_audio_player(self):
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.pygame_ready = True
        except Exception as error:
            logger.exception(f"PYGAME_AUDIO_INIT_ERROR | error={error}")
            self.pygame_ready = False

    def init_system_voice(self):
        try:
            self.system_engine = pyttsx3.init()
            self.system_engine.setProperty("rate", int(config.get("voice.rate", 180)))
            self.system_engine.setProperty("volume", float(config.get("voice.volume", 1.0)))
        except Exception as error:
            logger.exception(f"SYSTEM_VOICE_INIT_ERROR | error={error}")

    def speak(self, text: str):
        if not self.enabled or not text or text.strip() == ".":
            return

        if self.provider == "elevenlabs":
            try:
                return self.speak_elevenlabs(text)
            except Exception as error:
                logger.exception(f"ELEVENLABS_VOICE_ERROR | error={_friendly_elevenlabs_error(error)}")
                return self.speak_system(text)

        return self.speak_system(text)

    def speak_system(self, text: str):
        try:
            if self.system_engine is None:
                self.init_system_voice()
            if self.system_engine is None:
                return
            self.system_engine.say(text)
            self.system_engine.runAndWait()
        except Exception as error:
            logger.exception(f"SYSTEM_VOICE_ERROR | error={error}")

    def speak_elevenlabs(self, text: str):
        saved = load_settings()
        api_key = os.getenv("ELEVENLABS_API_KEY") or saved.get("elevenlabs_api_key", "")
        voice_id = os.getenv("ELEVENLABS_VOICE_ID") or saved.get("elevenlabs_voice_id", "")

        if not api_key:
            raise RuntimeError("ELEVENLABS_API_KEY nao encontrada no .env.")
        if not voice_id:
            raise RuntimeError("ELEVENLABS_VOICE_ID nao encontrado no .env.")

        if not self.pygame_ready:
            self.init_audio_player()
        if not self.pygame_ready:
            raise RuntimeError("Player de audio nao inicializado.")

        model_id = config.get("elevenlabs.model_id", "eleven_multilingual_v2")
        output_format = config.get("elevenlabs.output_format", "mp3_44100_128")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

        headers = {
            "xi-api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": {
                "stability": float(config.get("elevenlabs.stability", 0.45)),
                "similarity_boost": float(config.get("elevenlabs.similarity_boost", 0.75)),
                "style": float(config.get("elevenlabs.style", 0.25)),
                "use_speaker_boost": bool(config.get("elevenlabs.use_speaker_boost", True)),
            },
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            params={"output_format": output_format},
            timeout=30,
        )
        chars = response.headers.get("x-character-count")
        request_id = response.headers.get("request-id") or response.headers.get("x-trace-id")
        if chars or request_id:
            logger.info(f"ELEVENLABS_USAGE | chars={chars or '?'} request_id={request_id or '?'}")

        if response.status_code != 200:
            raise RuntimeError(f"Erro ElevenLabs {response.status_code}: {response.text}")

        audio_path = None
        try:
            import pygame
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as file:
                file.write(response.content)
                audio_path = file.name

            if self.pygame_ready:
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
            else:
                os.startfile(audio_path)
                time.sleep(1.0)
        finally:
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except Exception:
                    pass


def _friendly_elevenlabs_error(error: Exception) -> str:
    text = str(error)
    if "paid_plan_required" in text or "Free users cannot use library voices" in text:
        return "Essa voz exige plano pago para uso via API."
    if "401" in text or "Unauthorized" in text or "invalid" in text.lower():
        return "API Key invalida ou sem permissao."
    return text[:500]
