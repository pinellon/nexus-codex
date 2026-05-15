import pytest

from app.voice.audio_cache import AudioCache
from app.voice.tts_service import TTSService


def test_split_sentences_and_sanitize_text(tmp_path):
    service = TTSService(settings={}, cache=AudioCache(base_dir=tmp_path))

    chunks = service.split_sentences("Claro. Veja `TCP`. Link: https://example.com R$ 35")

    assert chunks[:2] == ["Claro.", "Veja TCP."]
    assert "link" in chunks[-1]
    assert "reais" in chunks[-1]


def test_choose_provider_auto_prefers_openai(tmp_path):
    service = TTSService(settings={"openai_api_key": "test"}, cache=AudioCache(base_dir=tmp_path))

    assert service.choose_provider(requested="auto") == "openai"


def test_choose_provider_auto_uses_elevenlabs_when_configured(tmp_path):
    service = TTSService(
        settings={"elevenlabs_api_key": "test", "elevenlabs_voice_id": "voice"},
        cache=AudioCache(base_dir=tmp_path),
    )

    assert service.choose_provider(requested="auto") == "elevenlabs"


def test_choose_provider_auto_falls_back_to_edge(monkeypatch, tmp_path):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("ELEVENLABS_API_KEY", raising=False)
    monkeypatch.delenv("ELEVENLABS_VOICE_ID", raising=False)
    service = TTSService(settings={}, cache=AudioCache(base_dir=tmp_path))

    assert service.choose_provider(requested="auto") == "edge"


def test_synthesize_to_file_rejects_empty_text(tmp_path):
    service = TTSService(settings={}, cache=AudioCache(base_dir=tmp_path))

    with pytest.raises(ValueError):
        service.synthesize_to_file("   ")


def test_synthesize_to_file_uses_cache(monkeypatch, tmp_path):
    cache = AudioCache(base_dir=tmp_path)
    service = TTSService(settings={}, cache=cache)
    calls = []

    def fake_provider(text, provider, voice, profile):
        calls.append((text, provider, voice, profile.id))
        return b"audio", ".mp3"

    monkeypatch.setattr(service, "_synthesize_provider", fake_provider)

    first = service.synthesize_to_file("Pronto.", provider="edge", profile="jarvis")
    second = service.synthesize_to_file("Pronto.", provider="edge", profile="jarvis")

    assert first.path == second.path
    assert first.path.read_bytes() == b"audio"
    assert len(calls) == 1


def test_synthesize_chunks_returns_cache_urls(monkeypatch, tmp_path):
    service = TTSService(settings={}, cache=AudioCache(base_dir=tmp_path))
    monkeypatch.setattr(service, "_synthesize_provider", lambda *_args: (b"audio", ".mp3"))

    chunks = service.synthesize_chunks("Claro. Pode falar.", provider="edge", profile="jarvis")

    assert len(chunks) == 2
    assert chunks[0]["audio_url"].startswith("/api/voice/cache/")
