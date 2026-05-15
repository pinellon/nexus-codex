"""Resposta por IA com fallback offline."""

from __future__ import annotations

from typing import Any

from app.config import OPENAI_MODEL
from app.logger import log_error
from app.settings_manager import load

_client = None
_client_key = None


def _build_system_prompt(owner: str) -> str:
    return f"""Voce e o NEXUS, assistente pessoal do {owner}.
Responda sempre em portugues do Brasil.
Seja direto, objetivo e util. Nunca diga que executou algo se nao executou."""


def _get_client(api_key: str):
    global _client, _client_key
    from openai import OpenAI

    if _client is None or _client_key != api_key:
        _client = OpenAI(api_key=api_key)
        _client_key = api_key
    return _client


def conversar(
    messages: list[dict[str, Any]],
    *,
    memory_query: str = "",
    temperature: float = 0.4,
) -> tuple[str, list[Any]]:
    cfg = load()
    api_key = cfg.get("openai_api_key", "").strip()
    if not api_key:
        return "API Key nao configurada. Va em Configuracoes e salve sua chave.", []

    try:
        from app.obsidian_memory import context_for_prompt

        client = _get_client(api_key)
        memory_context, hits = context_for_prompt(memory_query) if memory_query.strip() else ("", [])

        prepared_messages = [dict(item) for item in messages]
        if memory_context:
            if prepared_messages and prepared_messages[0].get("role") == "system":
                prepared_messages[0]["content"] = f"{prepared_messages[0].get('content', '').strip()}\n\n{memory_context}".strip()
            else:
                prepared_messages.insert(0, {"role": "system", "content": memory_context})

        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=prepared_messages,
            temperature=temperature,
        )
        answer = response.choices[0].message.content or "."
        return answer, hits
    except Exception as error:
        log_error(f"OpenAI: {error}")
        return "Nao consegui falar com a IA agora.", []


def responder(texto: str) -> str:
    cfg = load()
    try:
        from app.obsidian_memory import register

        system_prompt = _build_system_prompt(cfg.get("owner_name", "Nicolas"))
        answer, hits = conversar(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": texto},
            ],
            memory_query=texto,
            temperature=0.4,
        )
        if not hits and answer.strip() != ".":
            register(texto, answer, source="nexus-ai")
        return answer
    except Exception as error:
        log_error(f"OpenAI: {error}")
        return "Nao consegui falar com a IA agora."
