"""Operacoes de pasta para a expansao desktop do NEXUS."""

from __future__ import annotations

import os
from pathlib import Path
import unicodedata


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.lower().strip()


class FileManager:
    def __init__(self) -> None:
        home = Path.home()
        self._known = {
            "desktop": home / "Desktop",
            "area de trabalho": home / "Desktop",
            "area de trabalho": home / "Desktop",
            "downloads": home / "Downloads",
            "documentos": home / "Documents",
            "documents": home / "Documents",
            "imagens": home / "Pictures",
            "pictures": home / "Pictures",
            "fotos": home / "Pictures",
            "music": home / "Music",
            "musicas": home / "Music",
            "videos": home / "Videos",
            "videos": home / "Videos",
        }

    def _resolve(self, folder: str) -> Path:
        raw = (folder or "").strip().strip('"')
        key = _normalize(raw)
        if key in self._known:
            return self._known[key]
        return Path(raw).expanduser()

    def open_folder(self, folder: str) -> str:
        path = self._resolve(folder)
        if not path.exists():
            return f"Pasta nao encontrada: {path}"
        os.startfile(str(path))  # type: ignore[attr-defined]
        return f"Pasta aberta: {path}"

    def create_folder(self, path: str) -> str:
        target = Path(path).expanduser()
        target.mkdir(parents=True, exist_ok=True)
        return f"Pasta criada: {target}"
