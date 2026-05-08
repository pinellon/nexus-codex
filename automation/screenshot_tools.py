"""Captura de tela para a expansao desktop do NEXUS."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path


class ScreenshotTools:
    def capture_screen(self) -> str:
        try:
            from PIL import ImageGrab
        except Exception:
            return "Pillow/ImageGrab nao disponivel."

        target_dir = Path.home() / "Pictures" / "NexusShots"
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"nexus_shot_{datetime.now():%Y%m%d_%H%M%S}.png"
        try:
            try:
                image = ImageGrab.grab(all_screens=True)
            except TypeError:
                image = ImageGrab.grab()
            image.save(target)
            return f"Screenshot salvo em {target}"
        except Exception as error:
            return f"Falha ao capturar a tela: {error}"
