"""Minimal in-process queue state for speech requests."""

from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from uuid import uuid4


@dataclass
class VoiceQueue:
    items: list[str] = field(default_factory=list)
    interrupted: bool = False
    current_id: str = field(default_factory=lambda: uuid4().hex)
    _lock: Lock = field(default_factory=Lock)

    def enqueue(self, text: str) -> str:
        with self._lock:
            cleaned = text.strip()
            if cleaned:
                self.items.append(cleaned)
            return self.current_id

    def stop(self) -> str:
        with self._lock:
            self.items.clear()
            self.interrupted = True
            self.current_id = uuid4().hex
            return self.current_id

    def clear(self) -> None:
        with self._lock:
            self.items.clear()
            self.interrupted = False

    def is_speaking(self) -> bool:
        with self._lock:
            return bool(self.items) and not self.interrupted
