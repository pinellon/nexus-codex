"""Automacao de midia."""

import urllib.parse
import webbrowser
from app.logger import log_action


def abrir_spotify() -> str:
    webbrowser.open("https://open.spotify.com")
    log_action("Spotify aberto")
    return "Spotify aberto."


def tocar_spotify(musica: str) -> str:
    webbrowser.open("https://open.spotify.com/search/" + urllib.parse.quote(musica))
    log_action(f"Spotify busca: {musica}")
    return f"Buscando '{musica}' no Spotify."


def tocar_youtube(musica: str) -> str:
    webbrowser.open("https://www.youtube.com/results?search_query=" + urllib.parse.quote(musica))
    log_action(f"YouTube musica: {musica}")
    return f"Buscando '{musica}' no YouTube."


def tocar_musica_spotify(musica: str) -> str:
    return tocar_spotify(musica)


def tocar_musica_youtube(musica: str) -> str:
    return tocar_youtube(musica)


def escolher_plataforma_e_tocar(musica: str) -> str:
    from app.settings_manager import get
    if get("default_media", "youtube") == "spotify":
        return tocar_spotify(musica)
    return tocar_youtube(musica)
