"""Controle e status do computador."""

import ctypes
import os
import subprocess


def mostrar_cpu_ram_disco() -> str:
    try:
        import psutil
        cpu = psutil.cpu_percent(interval=0.2)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage(os.getenv("SystemDrive", "C:") + "\\").percent
        return f"CPU {cpu:.0f}% · RAM {ram:.0f}% · Disco {disk:.0f}%"
    except Exception:
        return "Status indisponível."


def desligar_pc() -> str:
    subprocess.Popen("shutdown /s /t 0", shell=True)
    return "Desligando."


def reiniciar_pc() -> str:
    subprocess.Popen("shutdown /r /t 0", shell=True)
    return "Reiniciando."


def suspender_pc() -> str:
    ctypes.windll.PowrProf.SetSuspendState(0, 1, 0)
    return "Suspendendo."


def bloquear_tela() -> str:
    ctypes.windll.user32.LockWorkStation()
    return "Tela bloqueada."

