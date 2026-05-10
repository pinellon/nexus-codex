"""Controle de midia para o NEXUS desktop."""

from __future__ import annotations


class MediaController:
    def _press(self, key: str, fallback: str | None = None) -> None:
        try:
            import pyautogui

            pyautogui.press(key)
            return
        except Exception:
            pass

        try:
            import keyboard

            keyboard.send(fallback or key)
        except Exception:
            pass

    def volume_up(self) -> str:
        self._press("volumeup", "volume up")
        return "Volume aumentado."

    def volume_down(self) -> str:
        self._press("volumedown", "volume down")
        return "Volume diminuido."

    def volume_mute(self) -> str:
        self._press("volumemute", "volume mute")
        return "Volume mutado."

    def media_play_pause(self) -> str:
        self._press("playpause", "play/pause media")
        return "Play/Pause enviado."

    def media_next(self) -> str:
        self._press("nexttrack", "next track")
        return "Proxima faixa enviada."

    def media_previous(self) -> str:
        self._press("prevtrack", "previous track")
        return "Faixa anterior enviada."
