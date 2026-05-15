from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any
import unicodedata


@dataclass
class DesktopIntent:
    name: str
    params: dict[str, Any]


def detect_desktop_intent(text: str) -> DesktopIntent | None:
    raw = text.strip().lower()
    t = unicodedata.normalize("NFKD", raw)
    t = "".join(ch for ch in t if not unicodedata.combining(ch))

    patterns = [
        (r"^(?:abrir|abre) janela (.+)$", "focus_window", "title"),
        (r"^(?:fechar|fecha) janela (.+)$", "close_window", "title"),
        (r"^(?:fechar|fecha|encerrar|encerra)\s+(?!janela\b|site\b|pasta\b)(.+)$", "close_window", "title"),
        (r"^(?:minimizar|minimiza) janela (.+)$", "minimize_window", "title"),
        (r"^(?:maximizar|maximiza) janela (.+)$", "maximize_window", "title"),
        (r"^(?:restaurar|restaura) janela (.+)$", "restore_window", "title"),
        (r"^(?:abrir|abre) site (.+)$", "open_url", "url"),
        (r"^(?:pesquisar|pesquisa) no google (.+)$", "google_search", "query"),
        (r"^(?:pesquisar|pesquisa) no youtube (.+)$", "youtube_search", "query"),
        (r"^(?:copiar|copia) texto (.+)$", "copy_text", "text"),
        (r"^(?:ler|mostra) clipboard$", "paste_text", None),
        (r"^(?:limpar|limpa) clipboard$", "clear_clipboard", None),
        (r"^(?:tirar|capturar) screenshot$", "capture_screen", None),
        (r"^(?:abrir|abre) pasta (desktop|downloads|documentos|documents|imagens|pictures|.+)$", "open_folder", "folder"),
        (r"^(?:criar|cria) pasta (.+)$", "create_folder", "path"),
        (r"^(?:aumentar|aumenta) volume$", "volume_up", None),
        (r"^(?:diminuir|diminui) volume$", "volume_down", None),
        (r"^(?:mutar|muta|silenciar|silencia) volume$", "volume_mute", None),
        (r"^(?:play|pause|tocar|pausar) midia$", "media_play_pause", None),
        (r"^(?:proxima) midia$", "media_next", None),
        (r"^(?:midia) anterior$", "media_previous", None),
    ]

    if re.match(r"^(?:listar|lista) janelas$", t):
        return DesktopIntent("list_windows", {})

    for pattern, intent, param_name in patterns:
        match = re.match(pattern, t)
        if match:
            params = {}
            if param_name:
                params[param_name] = match.group(1).strip()
            return DesktopIntent(intent, params)
    return None
