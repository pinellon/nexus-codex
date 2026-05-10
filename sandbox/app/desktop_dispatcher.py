from __future__ import annotations

from automation.browser_control import BrowserController
from automation.clipboard_tools import ClipboardTools
from automation.file_manager import FileManager
from automation.media_control import MediaController
from automation.screenshot_tools import ScreenshotTools
from automation.window_manager import WindowManager
from automation.app_launcher import abrir_app


class DesktopDispatcher:
    def __init__(self) -> None:
        self.windows = WindowManager()
        self.media = MediaController()
        self.browser = BrowserController()
        self.clipboard = ClipboardTools()
        self.shots = ScreenshotTools()
        self.files = FileManager()

    def execute(self, intent_name: str, params: dict) -> str:
        mapping = {
            "list_windows": self._list_windows,
            "focus_window": lambda: self.windows.focus_window(params.get("title", "")),
            "close_window": lambda: self.windows.close_window(params.get("title", "")),
            "minimize_window": lambda: self.windows.minimize_window(params.get("title", "")),
            "maximize_window": lambda: self.windows.maximize_window(params.get("title", "")),
            "restore_window": lambda: self.windows.restore_window(params.get("title", "")),
            "open_url": lambda: self.browser.open_url(params.get("url", "")),
            "open_app": lambda: str(abrir_app(params.get("app_id", "") or params.get("app", ""))),
            "open_youtube": lambda: self.browser.youtube_search(params.get("query", "")),
            "google_search": lambda: self.browser.google_search(params.get("query", "")),
            "youtube_search": lambda: self.browser.youtube_search(params.get("query", "")),
            "copy_text": lambda: self.clipboard.copy_text(params.get("text", "")),
            "paste_text": self.clipboard.paste_text,
            "clear_clipboard": self.clipboard.clear,
            "capture_screen": self.shots.capture_screen,
            "screenshot": self.shots.capture_screen,
            "open_folder": lambda: self.files.open_folder(params.get("folder", "")),
            "create_folder": lambda: self.files.create_folder(params.get("path", "")),
            "volume_up": self.media.volume_up,
            "volume_down": self.media.volume_down,
            "volume_mute": self.media.volume_mute,
            "mute_volume": self.media.volume_mute,
            "media_play_pause": self.media.media_play_pause,
            "media_next": self.media.media_next,
            "media_previous": self.media.media_previous,
            "pc_status": self._pc_status,
        }
        handler = mapping.get(intent_name)
        if handler is None:
            raise ValueError(f"Intent desktop nao suportada: {intent_name}")
        return handler()

    def _list_windows(self) -> str:
        windows = self.windows.list_windows()
        if not windows:
            return "Nenhuma janela detectada."
        lines = []
        for win in windows[:20]:
            flags = []
            if win.is_active:
                flags.append("ativa")
            if win.is_minimized:
                flags.append("minimizada")
            if win.is_maximized:
                flags.append("maximizada")
            suffix = f" ({', '.join(flags)})" if flags else ""
            lines.append(f"- {win.title}{suffix}")
        return "Janelas abertas:\n" + "\n".join(lines)

    def _pc_status(self) -> str:
        try:
            from automation.pc_control import mostrar_cpu_ram_disco
            return mostrar_cpu_ram_disco()
        except Exception as error:
            return f"Nao consegui ler o status do PC: {error}"
