"""Controle de navegador para a expansao desktop do NEXUS."""

from __future__ import annotations

import urllib.parse
import webbrowser


class BrowserController:
    def open_url(self, url: str) -> str:
        if not url:
            return "URL vazia."
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        webbrowser.open(url)
        return f"Site aberto: {url}"

    def google_search(self, query: str) -> str:
        webbrowser.open("https://www.google.com/search?q=" + urllib.parse.quote(query or ""))
        return f"Pesquisando no Google: {query}"

    def youtube_search(self, query: str) -> str:
        webbrowser.open("https://www.youtube.com/results?search_query=" + urllib.parse.quote(query or ""))
        return f"Pesquisando no YouTube: {query}"
