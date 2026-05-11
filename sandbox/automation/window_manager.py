"""Gerenciamento de janelas para a expansao desktop do NEXUS."""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


@dataclass
class WindowInfo:
    title: str
    is_active: bool
    is_minimized: bool
    is_maximized: bool


def _normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text.lower()).strip()


class WindowManager:
    def _gw(self):
        try:
            import pygetwindow as gw

            return gw
        except Exception:
            return None

    def list_windows(self) -> list[WindowInfo]:
        gw = self._gw()
        if gw is None:
            return []
        try:
            raw = gw.getAllWindows()
        except Exception:
            return []

        items: list[WindowInfo] = []
        seen: set[str] = set()
        for window in raw:
            title = getattr(window, "title", "") or ""
            title = title.strip()
            if not title:
                continue
            key = _normalize(title)
            if key in seen:
                continue
            seen.add(key)
            items.append(
                WindowInfo(
                    title=title,
                    is_active=bool(getattr(window, "isActive", False)),
                    is_minimized=bool(getattr(window, "isMinimized", False)),
                    is_maximized=bool(getattr(window, "isMaximized", False)),
                )
            )
        return items

    def _resolve(self, title: str):
        gw = self._gw()
        if gw is None:
            return None, "pygetwindow nao disponivel."
        title_norm = _normalize(title)
        try:
            windows = gw.getAllWindows()
        except Exception:
            return None, "Nao consegui enumerar as janelas."

        matches = []
        for window in windows:
            current = getattr(window, "title", "") or ""
            if not current.strip():
                continue
            current_norm = _normalize(current)
            if title_norm == current_norm or title_norm in current_norm or current_norm in title_norm:
                matches.append(window)
        if not matches:
            return None, f"Janela nao encontrada: {title}"
        return matches[0], ""

    def focus_window(self, title: str) -> str:
        window, error = self._resolve(title)
        if error:
            return error
        try:
            window.restore()
        except Exception:
            pass
        try:
            window.activate()
            return f"Janela focada: {title}"
        except Exception as error:
            return f"Falha ao focar janela: {error}"

    def close_window(self, title: str) -> str:
        window, error = self._resolve(title)
        if error:
            return error
        try:
            window.close()
            return f"Janela fechada: {title}"
        except Exception as error:
            return f"Falha ao fechar janela: {error}"

    def minimize_window(self, title: str) -> str:
        window, error = self._resolve(title)
        if error:
            return error
        try:
            window.minimize()
            return f"Janela minimizada: {title}"
        except Exception as error:
            return f"Falha ao minimizar janela: {error}"

    def maximize_window(self, title: str) -> str:
        window, error = self._resolve(title)
        if error:
            return error
        try:
            window.maximize()
            return f"Janela maximizada: {title}"
        except Exception as error:
            return f"Falha ao maximizar janela: {error}"

    def restore_window(self, title: str) -> str:
        window, error = self._resolve(title)
        if error:
            return error
        try:
            window.restore()
            return f"Janela restaurada: {title}"
        except Exception as error:
            return f"Falha ao restaurar janela: {error}"
