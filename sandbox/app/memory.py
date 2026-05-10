"""Memoria local basica do chat."""

import json
from datetime import datetime
from app.config import MEMORY_FILE, DATA_DIR


def save_message(role: str, content: str):
    DATA_DIR.mkdir(exist_ok=True)
    data = []
    try:
        if MEMORY_FILE.exists():
            data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        data = []
    data.append({"role": role, "content": content, "time": datetime.now().isoformat()})
    MEMORY_FILE.write_text(json.dumps(data[-100:], ensure_ascii=False, indent=2), encoding="utf-8")


def clear_memory():
    MEMORY_FILE.write_text("[]", encoding="utf-8")


def get_recent_history(n: int = 8) -> list[dict[str, str]]:
    """Retorna as ultimas mensagens no formato aceito pela OpenAI."""
    try:
        if not MEMORY_FILE.exists():
            return []
        data = json.loads(MEMORY_FILE.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            return []
        history = []
        for item in data[-n:]:
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant", "system"} and content:
                history.append({"role": role, "content": content})
        return history
    except Exception:
        return []
