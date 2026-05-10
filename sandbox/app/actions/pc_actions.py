"""Acoes de PC em classe, para voz e UI compartilharem o mesmo estilo."""

from __future__ import annotations


class PcActions:
    def __init__(self, settings=None, logger=None):
        self.settings = settings
        self.logger = logger

    def open_app(self, app_name: str) -> str:
        from automation.app_launcher import abrir_app
        return str(abrir_app(app_name))

    def open_youtube(self, query: str = "") -> str:
        from automation.browser import abrir_youtube, pesquisar_youtube
        return pesquisar_youtube(query) if query else abrir_youtube()

    def google_search(self, query: str) -> str:
        from automation.browser import pesquisar_google
        return pesquisar_google(query)

    def pc_status(self) -> str:
        from automation.pc_control import mostrar_cpu_ram_disco
        return mostrar_cpu_ram_disco()

    def volume_up(self) -> str:
        from automation.system import aumentar_volume
        return aumentar_volume()

    def volume_down(self) -> str:
        from automation.system import diminuir_volume
        return diminuir_volume()

    def mute_volume(self) -> str:
        from automation.system import mutar_volume
        return mutar_volume()

    def screenshot(self) -> str:
        from automation.screenshot_tools import ScreenshotTools
        return ScreenshotTools().capture_screen()

    def close_active_window(self) -> str:
        try:
            import pyautogui
            pyautogui.hotkey("alt", "f4")
            return "Janela ativa fechada."
        except Exception as error:
            return f"Falha ao fechar janela ativa: {error}"
