"""Automacao de navegador."""

import urllib.parse
import webbrowser
from app.logger import log_action


def abrir_site(url: str) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    webbrowser.open(url)
    log_action(f"Site aberto: {url}")
    return "Site aberto."


def abrir_youtube() -> str:
    return abrir_site("https://www.youtube.com")


def pesquisar_google(termo: str) -> str:
    webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote(termo))
    log_action(f"Google: {termo}")
    return f"Pesquisando '{termo}'."


def pesquisar_youtube(termo: str) -> str:
    webbrowser.open("https://www.youtube.com/results?search_query=" + urllib.parse.quote(termo))
    log_action(f"YouTube: {termo}")
    return f"Buscando '{termo}' no YouTube."

