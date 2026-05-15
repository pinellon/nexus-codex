"""Detector dedicado para intents de apps e launcher."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class AppIntent:
    name: str
    params: dict


_ARTICLES_RE = re.compile(r"^(o|a|os|as|um|uma|app|aplicativo|programa)\s+", re.IGNORECASE)
_WEB_DESTINATIONS = {"youtube"}


def _clean_app_name(value: str) -> str:
    text = (value or "").strip().strip('"\'')
    text = _ARTICLES_RE.sub("", text)
    return text.strip()


def detectar_intent_apps(texto: str) -> AppIntent | None:
    t = (texto or "").strip()
    low = t.lower()

    if re.search(r"\b(?:quais|lista|listar|mostra|mostrar|exibe|exibir)\b.*\b(?:apps|aplicativos|programas)\b", low):
        return AppIntent("listar_apps", {})

    m = re.search(
        r"\b(?:registra|registrar|cadastra|cadastrar|salva|salvar)\s+(?:o\s+)?(?:app|aplicativo|programa)\s+(.+?)\s+(?:em|no\s+caminho)\s+(.+)$",
        t,
        re.IGNORECASE,
    )
    if m:
        return AppIntent("registrar_app", {"alias": _clean_app_name(m.group(1)), "target": m.group(2).strip().strip('"')})

    m = re.search(r"\b(?:abre|abrir|inicia|iniciar|executa|executar|roda|rodar)\s+(?:o\s+)?(?:app|aplicativo|programa)?\s*(.+)$", t, re.IGNORECASE)
    if m:
        app = _clean_app_name(m.group(1))
        if app:
            if app.lower() in _WEB_DESTINATIONS:
                return None
            return AppIntent("abrir_app", {"app": app})

    return None
