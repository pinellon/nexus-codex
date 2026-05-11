"""Utilitarios do sistema."""

import datetime
import os
from pathlib import Path


def aumentar_volume() -> str:
    try:
        import keyboard
        keyboard.send("volume up")
    except Exception:
        pass
    return "Volume aumentado."


def diminuir_volume() -> str:
    try:
        import keyboard
        keyboard.send("volume down")
    except Exception:
        pass
    return "Volume diminuído."


def mutar_volume() -> str:
    try:
        import keyboard
        keyboard.send("volume mute")
    except Exception:
        pass
    return "Volume mutado."


def tirar_print() -> str:
    try:
        from PIL import ImageGrab
        path = Path.home() / "Pictures" / f"nexus_print_{datetime.datetime.now():%Y%m%d_%H%M%S}.png"
        path.parent.mkdir(exist_ok=True)
        ImageGrab.grab().save(path)
        return f"Print salvo em {path}"
    except Exception:
        return "Não consegui tirar print."


def mostrar_data_hora() -> str:
    return datetime.datetime.now().strftime("Agora são %H:%M de %d/%m/%Y.")

