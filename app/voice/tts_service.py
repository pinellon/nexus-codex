"""Professional text-to-speech service for Nexus web voice."""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import requests

from app.settings_manager import load as load_settings
from app.voice.audio_cache import AudioCache, AudioCacheItem, cache_key
from app.voice.voice_profiles import VoiceProfile, get_profile

COMMON_PHRASES = {
    "Feito.",
    "Pronto.",
    "Estou ouvindo.",
    "Comando cancelado.",
    "Nao consegui concluir.",
    "Pode falar.",
}


class TTSService:
    def __init__(self, settings: dict[str, Any] | None = None, cache: AudioCache | None = None):
        self.settings = settings if settings is not None else load_settings()
        self.cache = cache or AudioCache()

    def choose_provider(self, settings: dict[str, Any] | None = None, requested: str = "auto") -> str:
        cfg = settings or self.settings
        provider = (requested or "auto").strip().lower().replace("_", "-")
        aliases = {
            "openai-tts": "openai",
            "edge-tts": "edge",
            "browser": "browser_fallback",
            "browser-fallback": "browser_fallback",
            "pytts": "pyttsx3",
            "system": "pyttsx3",
        }
        provider = aliases.get(provider, provider)
        if provider != "auto":
            return provider

        if str(os.getenv("OPENAI_API_KEY") or cfg.get("openai_api_key", "") or "").strip():
            return "openai"
        if str(os.getenv("ELEVENLABS_API_KEY") or cfg.get("elevenlabs_api_key", "") or "").strip() and str(
            os.getenv("ELEVENLABS_VOICE_ID") or cfg.get("elevenlabs_voice_id", "") or ""
        ).strip():
            return "elevenlabs"
        return "edge"

    def sanitize_text_for_speech(self, text: str) -> str:
        cleaned = (text or "").strip()
        cleaned = re.sub(r"```.*?```", " codigo omitido ", cleaned, flags=re.DOTALL)
        cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
        cleaned = re.sub(r"!\[[^\]]*\]\([^)]+\)", " imagem ", cleaned)
        cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
        cleaned = re.sub(r"https?://\S+", "link", cleaned)
        cleaned = cleaned.replace("R$", " reais ")
        cleaned = re.sub(r"[*_#>|~]+", " ", cleaned)
        cleaned = re.sub(r"[\U00010000-\U0010ffff]", "", cleaned)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned[:2200]

    def split_sentences(self, text: str) -> list[str]:
        cleaned = self.sanitize_text_for_speech(text)
        if not cleaned:
            return []
        parts = re.split(r"(?<=[.!?])\s+", cleaned)
        chunks: list[str] = []
        for part in parts:
            current = part.strip()
            if not current:
                continue
            while len(current) > 260:
                cut = current.rfind(" ", 0, 240)
                if cut < 80:
                    cut = 240
                chunks.append(current[:cut].strip())
                current = current[cut:].strip()
            if current:
                chunks.append(current)
        return chunks

    def synthesize(self, text: str, provider: str = "auto", voice: str = "default", profile: str = "jarvis") -> bytes:
        item = self.synthesize_to_file(text, provider=provider, voice=voice, profile=profile)
        return item.path.read_bytes()

    def synthesize_to_file(
        self,
        text: str,
        provider: str = "auto",
        voice: str = "default",
        profile: str = "jarvis",
    ) -> AudioCacheItem:
        cleaned = self.sanitize_text_for_speech(text)
        if not cleaned:
            raise ValueError("Texto vazio para TTS.")

        voice_profile = get_profile(profile)
        chosen_provider = self.choose_provider(self.settings, provider if provider != "auto" else voice_profile.provider)
        resolved_voice = self._resolve_voice(chosen_provider, voice, voice_profile)
        key = cache_key(cleaned, chosen_provider, resolved_voice, voice_profile.id)
        cached = self.cache.get(key)
        if cached:
            return cached

        try:
            audio, extension = self._synthesize_provider(cleaned, chosen_provider, resolved_voice, voice_profile)
        except Exception:
            if chosen_provider != "edge":
                audio, extension = self._synthesize_provider(cleaned, "edge", self._resolve_voice("edge", "default", voice_profile), voice_profile)
                chosen_provider = "edge"
                resolved_voice = self._resolve_voice("edge", "default", voice_profile)
                key = cache_key(cleaned, chosen_provider, resolved_voice, voice_profile.id)
            else:
                raise
        return self.cache.put(key, audio, extension)

    def synthesize_chunks(self, text: str, provider: str = "auto", profile: str = "jarvis") -> list[dict[str, str]]:
        chunks = self.split_sentences(text)
        items: list[dict[str, str]] = []
        for index, chunk in enumerate(chunks, 1):
            item = self.synthesize_to_file(chunk, provider=provider, profile=profile)
            items.append(
                {
                    "id": item.key,
                    "text": chunk,
                    "audio_url": f"/api/voice/cache/{item.path.name}",
                    "content_type": item.content_type,
                    "order": str(index),
                }
            )
        return items

    def _resolve_voice(self, provider: str, voice: str, profile: VoiceProfile) -> str:
        if voice and voice != "default":
            return voice
        if provider == "openai":
            return profile.voice
        if provider == "elevenlabs":
            return str(os.getenv("ELEVENLABS_VOICE_ID") or self.settings.get("elevenlabs_voice_id", "") or "")
        if provider == "edge":
            return str(self.settings.get("edge_tts_voice", "") or "pt-BR-AntonioNeural")
        return "default"

    def _synthesize_provider(self, text: str, provider: str, voice: str, profile: VoiceProfile) -> tuple[bytes, str]:
        if provider == "openai":
            return self._synthesize_openai(text, voice, profile), ".mp3"
        if provider == "elevenlabs":
            return self._synthesize_elevenlabs(text, voice), ".mp3"
        if provider == "edge":
            return self._synthesize_edge(text, voice, profile), ".mp3"
        if provider == "pyttsx3":
            return self._synthesize_pyttsx3(text), ".wav"
        if provider == "browser_fallback":
            raise RuntimeError("browser_fallback deve ser tocado no frontend.")
        raise RuntimeError(f"Provider de voz nao suportado: {provider}")

    def _synthesize_openai(self, text: str, voice: str, profile: VoiceProfile) -> bytes:
        from openai import OpenAI

        api_key = str(os.getenv("OPENAI_API_KEY") or self.settings.get("openai_api_key", "") or "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY nao configurada.")
        model = str(self.settings.get("openai_tts_model", "") or "gpt-4o-mini-tts")
        response = OpenAI(api_key=api_key).audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            instructions=profile.instructions,
            response_format="mp3",
            speed=max(0.25, min(4.0, float(profile.speed))),
        )
        return bytes(response.content)

    def _synthesize_elevenlabs(self, text: str, voice_id: str) -> bytes:
        api_key = str(os.getenv("ELEVENLABS_API_KEY") or self.settings.get("elevenlabs_api_key", "") or "").strip()
        voice = voice_id or str(os.getenv("ELEVENLABS_VOICE_ID") or self.settings.get("elevenlabs_voice_id", "") or "").strip()
        if not api_key or not voice:
            raise RuntimeError("ElevenLabs API key ou Voice ID nao configurados.")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
        response = requests.post(
            url,
            headers={"xi-api-key": api_key, "Accept": "audio/mpeg", "Content-Type": "application/json"},
            json={
                "text": text,
                "model_id": str(self.settings.get("elevenlabs_model_id", "") or "eleven_multilingual_v2"),
                "voice_settings": {"stability": 0.48, "similarity_boost": 0.76, "style": 0.18, "use_speaker_boost": True},
            },
            timeout=30,
        )
        if response.status_code != 200:
            raise RuntimeError(f"Erro ElevenLabs {response.status_code}: {response.text[:300]}")
        return response.content

    def _synthesize_edge(self, text: str, voice: str, profile: VoiceProfile) -> bytes:
        import edge_tts

        async def _generate(path: str) -> None:
            communicate = edge_tts.Communicate(text, voice=voice, rate=self._edge_rate(profile.speed), pitch=profile.pitch)
            await communicate.save(path)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
            temp_path = temp_file.name
        try:
            asyncio.run(_generate(temp_path))
            return Path(temp_path).read_bytes()
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def _synthesize_pyttsx3(self, text: str) -> bytes:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
            temp_path = temp_file.name
        try:
            script = (
                "import pyttsx3, sys\n"
                "engine = pyttsx3.init()\n"
                "engine.setProperty('rate', 178)\n"
                "engine.save_to_file(sys.argv[1], sys.argv[2])\n"
                "engine.runAndWait()\n"
            )
            subprocess.run(["python", "-c", script, text, temp_path], check=True, timeout=25, capture_output=True)
            return Path(temp_path).read_bytes()
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def _edge_rate(self, speed: float) -> str:
        percent = int(round((float(speed) - 1.0) * 100))
        if percent == 0:
            return "+0%"
        sign = "+" if percent > 0 else ""
        return f"{sign}{percent}%"
