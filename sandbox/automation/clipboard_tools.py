"""Ferramentas de clipboard para o NEXUS."""

from __future__ import annotations


class ClipboardTools:
    def _clip(self):
        try:
            import pyperclip

            return pyperclip
        except Exception:
            return None

    def copy_text(self, text: str) -> str:
        clip = self._clip()
        if clip is None:
            return "pyperclip nao disponivel."
        clip.copy(text or "")
        return "Texto copiado para o clipboard."

    def paste_text(self) -> str:
        clip = self._clip()
        if clip is None:
            return "pyperclip nao disponivel."
        text = clip.paste()
        return text if text else "Clipboard vazio."

    def clear(self) -> str:
        clip = self._clip()
        if clip is None:
            return "pyperclip nao disponivel."
        clip.copy("")
        return "Clipboard limpo."
