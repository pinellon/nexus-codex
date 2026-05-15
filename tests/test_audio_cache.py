from app.voice.audio_cache import AudioCache, cache_key
import time


def test_audio_cache_hit_and_miss(tmp_path):
    cache = AudioCache(base_dir=tmp_path)
    key = cache_key("Pronto.", "edge", "pt-BR-AntonioNeural", "jarvis")

    assert cache.get(key) is None

    stored = cache.put(key, b"audio", ".mp3")
    loaded = cache.get(key)

    assert stored.path.exists()
    assert loaded is not None
    assert loaded.key == key
    assert loaded.path.read_bytes() == b"audio"


def test_audio_cache_cleanup_keeps_newest_files(tmp_path):
    cache = AudioCache(base_dir=tmp_path, max_files=1)
    cache.put("old", b"old", ".mp3")
    time.sleep(0.01)
    cache.put("new", b"new", ".mp3")

    assert not (tmp_path / "old.mp3").exists()
    assert (tmp_path / "new.mp3").exists()
