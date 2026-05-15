"""Roteador simples de intencoes por texto."""

from dataclasses import dataclass
import re
from app.settings_manager import get


@dataclass
class Intent:
    name: str
    params: dict


def detectar_intent(texto: str) -> Intent | None:
    t = texto.lower().strip()

    patterns = [
        (r"\b(chrome)\b", "abrir_chrome", {}),
        (r"\b(edge)\b", "abrir_edge", {}),
        (r"\b(spotify)\b.*\b(abr|inici)|\b(abr|inici).*\b(spotify)\b", "abrir_spotify", {}),
        (r"\b(youtube)\b.*\b(abr|inici)|\b(abr|inici).*\b(youtube)\b", "abrir_youtube", {}),
        (r"\bdownloads?\b", "abrir_downloads", {}),
        (r"\b(area de trabalho|área de trabalho|desktop)\b", "abrir_desktop", {}),
        (r"\b(bloco de notas|notepad)\b", "abrir_bloco_de_notas", {}),
        (r"\bcalculadora\b", "abrir_calculadora", {}),
        (r"\b(status|cpu|ram|disco)\b.*\b(pc|sistema|computador)?\b", "status_pc", {}),
        (r"\b(print|screenshot|captura)\b", "tirar_print", {}),
        (r"\b(data|hora|que horas)\b", "mostrar_data_hora", {}),
        (r"\b(aumenta|aumentar|subir).*\bvolume\b", "aumentar_volume", {}),
        (r"\b(diminui|diminuir|baixar).*\bvolume\b", "diminuir_volume", {}),
        (r"\b(muta|mutar|silenciar|sem som)\b", "mutar_volume", {}),
        (r"\bbloquear\b.*\btela\b|\btela\b.*\bbloquear\b", "bloquear_tela", {}),
        (r"\breiniciar\b.*\b(pc|computador|sistema)\b", "reiniciar_pc", {}),
        (r"\bdesligar\b.*\b(pc|computador|sistema)\b", "desligar_pc", {}),
        (r"\blimpar\b.*\bmem[oó]ria\b", "limpar_memoria", {}),
    ]
    for pattern, name, params in patterns:
        if re.search(pattern, t):
            return Intent(name, params)

    if m := re.search(r"pesquis(?:a|ar)\s+(.+?)\s+(?:no\s+)?google", t):
        return Intent("pesquisar_google", {"termo": m.group(1)})
    if m := re.search(r"pesquis(?:a|ar)\s+(.+?)\s+(?:no\s+)?youtube", t):
        return Intent("pesquisar_youtube", {"termo": m.group(1)})
    if m := re.search(r"(?:toca|tocar|play|reproduz)\s+(.+?)\s+no\s+spotify", t):
        return Intent("tocar_spotify", {"musica": m.group(1)})
    if m := re.search(r"(?:toca|tocar|play|reproduz)\s+(.+?)\s+no\s+youtube", t):
        return Intent("tocar_youtube", {"musica": m.group(1)})
    # "quero ouvir X", "coloca X", "ouvir X" — usa handler inteligente de musica
    if m := re.search(r"(?:quero\s+ouvir|ouvir|coloca|toca|tocar|play|reproduz)\s+(.+)", t):
        return Intent("tocar_musica_smart", {"texto": m.group(0)})
    if m := re.search(r"\babr(?:e|ir)\s+(.+\.(?:com|net|org|br|io).*)", t):
        return Intent("abrir_site", {"url": m.group(1)})

    return None

