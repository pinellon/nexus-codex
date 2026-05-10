"""Resposta por IA com fallback offline."""

from app.config import OPENAI_MODEL
from app.logger import log_error
from app.settings_manager import load

_client = None
_client_key = None


def _build_system_prompt(owner: str) -> str:
    return f"""Voce e o NEXUS, assistente pessoal do {owner}.
Responda sempre em portugues do Brasil.
Seja direto, objetivo e util. Nunca diga que executou algo se nao executou."""


def responder(texto: str) -> str:
    global _client, _client_key
    cfg = load()
    api_key = cfg.get("openai_api_key", "").strip()
    if not api_key:
        return "API Key nao configurada. Va em Configuracoes e salve sua chave."

    try:
        from app.obsidian_memory import context_for_prompt, register
        from openai import OpenAI
        if _client is None or _client_key != api_key:
            _client = OpenAI(api_key=api_key)
            _client_key = api_key
        memory_context, hits = context_for_prompt(texto)
        system_prompt = _build_system_prompt(cfg.get("owner_name", "Nicolas"))
        if memory_context:
            system_prompt += "\n\n" + memory_context
        resp = _client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": texto},
            ],
            temperature=0.4,
        )
        answer = resp.choices[0].message.content or "."
        if not hits and answer.strip() != ".":
            register(texto, answer, source="nexus-ai")
        return answer
    except Exception as error:
        log_error(f"OpenAI: {error}")
        return "Nao consegui falar com a IA agora."
