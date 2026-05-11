"""Gravador de sessoes do NEXUS.

Registra comandos, respostas e eventos em JSONL para auditoria, debug e memoria.
Cada linha e um JSON independente, facil de ler depois.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SessionEvent:
    timestamp: str
    kind: str
    message: str
    data: dict[str, Any]


class SessionRecorder:
    def __init__(self, path: str | Path = "data/session_events.jsonl"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, kind: str, message: str, **data: Any) -> SessionEvent:
        event = SessionEvent(
            timestamp=datetime.now().isoformat(timespec="seconds"),
            kind=kind,
            message=message,
            data=data,
        )
        with self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")
        return event

    def tail(self, limit: int = 30) -> list[SessionEvent]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()[-limit:]
        events: list[SessionEvent] = []
        for line in lines:
            try:
                payload = json.loads(line)
                events.append(SessionEvent(**payload))
            except Exception:
                continue
        return events

    def summary(self, limit: int = 30) -> str:
        events = self.tail(limit=limit)
        if not events:
            return "Nenhum evento registrado ainda."
        lines = ["Ultimos eventos do NEXUS:"]
        for event in events:
            lines.append(f"[{event.timestamp}] {event.kind}: {event.message}")
        return "\n".join(lines)
