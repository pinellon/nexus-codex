from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class SessionContext:
    session_id: str
    current_topic: str = ""
    current_goal: str = ""
    last_user_messages: list[str] = field(default_factory=list)
    last_assistant_messages: list[str] = field(default_factory=list)
    study_mode_enabled: bool = False
    last_summary: str = ""
    related_notes: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def add_user_message(self, text: str) -> None:
        self._push_message(self.last_user_messages, text)

    def add_assistant_message(self, text: str) -> None:
        self._push_message(self.last_assistant_messages, text)

    def set_topic(self, topic: str) -> None:
        self.current_topic = (topic or "").strip()
        self._touch()

    def set_goal(self, goal: str) -> None:
        self.current_goal = (goal or "").strip()
        self._touch()

    def get_context_text(self) -> str:
        sections: list[str] = []
        if self.current_topic:
            sections.append(f"Topico atual: {self.current_topic}")
        if self.current_goal:
            sections.append(f"Objetivo atual: {self.current_goal}")
        if self.study_mode_enabled:
            sections.append("Modo estudo: ativo")
        if self.related_notes:
            sections.append("Notas relacionadas: " + ", ".join(self.related_notes[:5]))
        if self.last_summary:
            sections.append(f"Ultimo resumo: {self.last_summary[:500]}")
        if self.last_user_messages:
            sections.append("Ultimas mensagens do usuario:\n- " + "\n- ".join(self.last_user_messages[-4:]))
        if self.last_assistant_messages:
            sections.append("Ultimas respostas do Nexus:\n- " + "\n- ".join(self.last_assistant_messages[-4:]))
        return "\n\n".join(section for section in sections if section.strip())

    def reset(self) -> None:
        self.current_topic = ""
        self.current_goal = ""
        self.last_user_messages.clear()
        self.last_assistant_messages.clear()
        self.study_mode_enabled = False
        self.last_summary = ""
        self.related_notes.clear()
        self._touch()

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def _push_message(self, bucket: list[str], text: str) -> None:
        cleaned = (text or "").strip()
        if not cleaned:
            return
        bucket.append(cleaned)
        del bucket[:-6]
        self._touch()

    def _touch(self) -> None:
        self.updated_at = _now_iso()
