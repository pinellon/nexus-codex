"""Sugestao de comandos quando o NEXUS nao entende algo.

Esse modulo ajuda o assistente a responder melhor em vez de apenas dizer
"nao entendi". Ele retorna comandos proximos e tambem exemplos prontos.
"""

from __future__ import annotations

from difflib import get_close_matches

KNOWN_COMMANDS = [
    "abrir chrome",
    "abrir spotify",
    "abrir vscode",
    "abrir calculadora",
    "abrir bloco de notas",
    "abrir youtube",
    "pesquisar no google",
    "status do pc",
    "aumentar volume",
    "diminuir volume",
    "mutar",
    "tirar print",
    "modo foco",
    "modo aula",
    "modo apresentacao",
    "diagnostico rapido",
    "rode esse codigo",
    "explique esse codigo",
    "corrija esse codigo",
    "documente esse codigo",
    "salve esse arquivo",
    "crie um arquivo chamado main.py",
    "limpe o terminal",
    "parar",
    "acordar",
]


def suggest_commands(text: str, limit: int = 5) -> list[str]:
    text = (text or "").strip().lower()
    matches = get_close_matches(text, KNOWN_COMMANDS, n=limit, cutoff=0.25)
    if matches:
        return matches
    return KNOWN_COMMANDS[:limit]


def format_suggestions(text: str, limit: int = 5) -> str:
    suggestions = suggest_commands(text, limit=limit)
    joined = "\n".join(f"- Nexus, {item}" for item in suggestions)
    return f"Nao entendi esse comando. Tente um destes:\n{joined}"
