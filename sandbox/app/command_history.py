"""Historico de comandos com navegacao por seta."""

from __future__ import annotations

import json
from app.config import DATA_DIR

HISTORY_FILE = DATA_DIR / "command_history.json"


class CommandHistory:
    def __init__(self, max_items: int = 80):
        self.max_items = max_items
        self.items: list[str] = []
        self.index: int | None = None
        self.draft = ""
        self._load()

    def _load(self):
        try:
            data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                self.items = [str(x) for x in data[-self.max_items:] if str(x).strip()]
        except Exception:
            self.items = []

    def _save(self):
        try:
            DATA_DIR.mkdir(exist_ok=True)
            HISTORY_FILE.write_text(
                json.dumps(self.items[-self.max_items:], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass

    def add(self, text: str):
        text = (text or "").strip()
        if not text:
            return
        if text in self.items:
            self.items.remove(text)
        self.items.append(text)
        self.items = self.items[-self.max_items:]
        self.index = None
        self.draft = ""
        self._save()

    def up(self, current: str = "") -> str | None:
        if not self.items:
            return None
        if self.index is None:
            self.draft = current
            self.index = len(self.items) - 1
        else:
            self.index = max(0, self.index - 1)
        return self.items[self.index]

    def down(self) -> str | None:
        if self.index is None:
            return None
        self.index += 1
        if self.index >= len(self.items):
            self.index = None
            return self.draft
        return self.items[self.index]


history = CommandHistory()

