from __future__ import annotations

import re

from app.obsidian_memory import normalize

_INTENT_RULES: list[tuple[str, tuple[str, ...], float]] = [
    ("save_note", ("salva isso", "salva esse resumo", "salva no obsidian", "manda para o obsidian", "manda pro obsidian", "guarda isso no cerebro", "guarda isso no cérebro"), 0.98),
    ("quiz", ("me testa", "faz perguntas", "cria quiz", "faz um quiz", "quiz"), 0.92),
    ("summarize", ("faz um resumo", "resume", "me da um resumo", "me dá um resumo", "resuma"), 0.9),
    ("task_help", ("me ajuda com essa tarefa", "me ajuda com esse trabalho", "me ajuda a fazer", "me ajuda com o trabalho"), 0.87),
    ("code_help", ("explica esse codigo", "explica esse código", "me ajuda no codigo", "me ajuda com codigo", "me ajuda com código", "me ajuda em codigo", "me ajuda em código"), 0.9),
    ("simplify", ("explica mais simples", "mais simples", "simplifica", "simplifique"), 0.88),
    ("deepen", ("explica mais tecnico", "explica mais técnico", "mais tecnico", "mais técnico", "aprofunda", "aprofunde"), 0.88),
    ("continue_topic", ("continua", "continue", "segue", "prossegue"), 0.84),
    ("explain", ("me explica", "explica", "me ensina", "ensina", "me ajuda a estudar", "quero estudar"), 0.86),
]

_TOPIC_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"(?:me ajuda a estudar|quero estudar)\s+(.+)", re.IGNORECASE),
    re.compile(r"(?:me explica|explica|me ensina|ensina)\s+(.+)", re.IGNORECASE),
    re.compile(r"(?:faz um resumo|resume|resuma)\s+(?:sobre\s+)?(.+)", re.IGNORECASE),
    re.compile(r"(?:cria quiz|faz perguntas|me testa)\s+(?:sobre\s+)?(.+)", re.IGNORECASE),
    re.compile(r"(?:me ajuda com essa tarefa|me ajuda com esse trabalho|me ajuda a fazer)\s+(.+)", re.IGNORECASE),
    re.compile(r"(?:explica esse codigo|explica esse código|me ajuda com codigo|me ajuda com código)\s+(.+)", re.IGNORECASE),
]


def extract_topic(text: str) -> str:
    raw = (text or "").strip()
    if not raw:
        return ""
    for pattern in _TOPIC_PATTERNS:
        match = pattern.search(raw)
        if match:
            topic = _cleanup_topic(match.group(1))
            if topic:
                return topic
    return ""


def detect_study_intent(text: str) -> dict[str, object]:
    raw = (text or "").strip()
    normalized = normalize(raw)
    if not normalized:
        return {"intent": "general_chat", "topic": "", "confidence": 0.0}

    for intent_name, triggers, confidence in _INTENT_RULES:
        if any(trigger in normalized for trigger in triggers):
            return {
                "intent": intent_name,
                "topic": extract_topic(raw),
                "confidence": confidence,
            }

    if any(keyword in normalized for keyword in ("estudar", "prova", "trabalho", "materia", "matéria", "explica", "resumo", "quiz")):
        return {
            "intent": "explain",
            "topic": extract_topic(raw),
            "confidence": 0.62,
        }

    return {"intent": "general_chat", "topic": extract_topic(raw), "confidence": 0.35}


def _cleanup_topic(value: str) -> str:
    cleaned = re.sub(r"^(?:sobre|de|do|da|essa|esse|isso)\s+", "", value.strip(), flags=re.IGNORECASE)
    cleaned = cleaned.strip(" .,!?:;")
    return cleaned
