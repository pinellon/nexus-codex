"""Small disk cache for generated speech audio."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

from app.config import DATA_DIR

CACHE_DIR = DATA_DIR / "audio_cache"
DEFAULT_MAX_FILES = 200


@dataclass(frozen=True)
class AudioCacheItem:
    key: str
    path: Path
    content_type: str


def cache_key(text: str, provider: str, voice: str, profile: str = "") -> str:
    payload = "\n".join([provider.strip().lower(), voice.strip().lower(), profile.strip().lower(), text.strip()])
    return sha256(payload.encode("utf-8")).hexdigest()


class AudioCache:
    def __init__(self, base_dir: Path | None = None, max_files: int = DEFAULT_MAX_FILES):
        self.base_dir = base_dir or CACHE_DIR
        self.max_files = max_files

    def path_for(self, key: str, extension: str) -> Path:
        suffix = extension if extension.startswith(".") else f".{extension}"
        return self.base_dir / f"{key}{suffix}"

    def get(self, key: str) -> AudioCacheItem | None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        for extension, content_type in ((".mp3", "audio/mpeg"), (".wav", "audio/wav")):
            path = self.path_for(key, extension)
            if path.exists() and path.is_file():
                try:
                    path.touch()
                except Exception:
                    pass
                return AudioCacheItem(key=key, path=path, content_type=content_type)
        return None

    def put(self, key: str, audio: bytes, extension: str = ".mp3") -> AudioCacheItem:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        path = self.path_for(key, extension)
        path.write_bytes(audio)
        self.cleanup()
        return AudioCacheItem(
            key=key,
            path=path,
            content_type="audio/wav" if path.suffix.lower() == ".wav" else "audio/mpeg",
        )

    def cleanup(self) -> None:
        if self.max_files <= 0 or not self.base_dir.exists():
            return
        files = [item for item in self.base_dir.iterdir() if item.is_file() and item.suffix.lower() in {".mp3", ".wav"}]
        if len(files) <= self.max_files:
            return
        files.sort(key=lambda path: path.stat().st_mtime)
        for path in files[: max(0, len(files) - self.max_files)]:
            try:
                path.unlink()
            except Exception:
                pass
