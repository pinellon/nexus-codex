"""Automacao de midia com suporte a artistas e musicas especificas."""

from __future__ import annotations

import re
import urllib.parse
import webbrowser

from app.logger import log_action

_ARTISTAS_BR = {
    "luan santana",
    "gusttavo lima",
    "ana castela",
    "marilia mendonca",
    "henrique e juliano",
    "jorge e mateus",
    "zeze di camargo",
    "chitaozinho e xororo",
    "maiara e maraisa",
    "simone e simaria",
    "anitta",
    "mc kekel",
    "mc g15",
    "mc livinho",
    "dennis dj",
    "ludmilla",
    "thiaguinho",
    "projota",
    "emicida",
    "djavan",
    "gilberto gil",
    "caetano veloso",
    "tim maia",
    "roberto carlos",
    "ivete sangalo",
    "claudia leitte",
    "bell marques",
    "psirico",
    "harmonia do samba",
    "turma do pagode",
    "soweto",
    "exaltasamba",
    "fundo de quintal",
    "metallica",
    "iron maiden",
    "black sabbath",
    "nirvana",
    "pink floyd",
    "the beatles",
    "rolling stones",
    "led zeppelin",
    "ac dc",
    "queen",
    "drake",
    "eminem",
    "kendrick lamar",
    "travis scott",
    "post malone",
    "taylor swift",
    "beyonce",
    "ariana grande",
    "billie eilish",
    "the weeknd",
}


def _parece_artista(texto: str) -> bool:
    """Verifica se o texto parece ser apenas um nome de artista."""
    t = (texto or "").lower().strip()
    if t in _ARTISTAS_BR:
        return True
    palavras = t.split()
    if len(palavras) <= 3 and not any(
        chave in t for chave in ("musica", "song", "ft", "feat", " - ", "ao vivo")
    ):
        return True
    return False


def _plataforma_pedida(texto: str) -> str | None:
    t = (texto or "").lower()
    if "youtube" in t:
        return "youtube"
    if "spotify" in t:
        return "spotify"
    return None


def _extrair_alvo_musical(texto: str) -> str:
    match = re.search(
        r"(?:quero\s+ouvir|coloca|toca|play|reproduz|ouvir)\s+(.+)",
        (texto or "").strip(),
        re.IGNORECASE,
    )
    alvo = match.group(1).strip() if match else (texto or "").strip()
    return re.sub(r"\s+no\s+(youtube|spotify)\s*$", "", alvo, flags=re.I).strip()


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


def tocar_artista_youtube(artista: str) -> str:
    """Busca as musicas mais famosas de um artista no YouTube."""
    query = f"{artista} musicas mais famosas"
    webbrowser.open("https://www.youtube.com/results?search_query=" + urllib.parse.quote(query))
    log_action(f"YouTube artista mais tocadas: {artista}")
    return (
        f"Abri {artista} no YouTube com as musicas mais famosas.\n"
        "Se quiser, me diga uma musica especifica ou peca outra."
    )


def escolher_plataforma_e_tocar(musica: str) -> str:
    """Detecta se e um artista ou musica e age de forma inteligente."""
    from app.settings_manager import get

    plataforma = get("default_media", "youtube")

    if _parece_artista(musica):
        if plataforma == "spotify":
            return tocar_spotify(f"{musica} top musicas")
        return tocar_artista_youtube(musica)

    if plataforma == "spotify":
        return tocar_spotify(musica)
    return tocar_youtube(musica)


def responder_musica_inteligente(texto: str) -> str:
    """
    Analisa o pedido de musica em linguagem natural e toma a melhor acao.
    Suporta: "quero ouvir Luan Santana", "toca Evidencias", etc.
    """
    alvo = _extrair_alvo_musical(texto)
    plataforma = _plataforma_pedida(texto)

    if not alvo:
        return "Me diga o nome da musica ou do artista que voce quer ouvir."

    if _parece_artista(alvo):
        if plataforma == "spotify":
            return tocar_spotify(f"{alvo} top musicas")
        return tocar_artista_youtube(alvo)

    if plataforma == "spotify":
        return tocar_spotify(alvo)
    if plataforma == "youtube":
        return tocar_youtube(alvo)
    return escolher_plataforma_e_tocar(alvo)
