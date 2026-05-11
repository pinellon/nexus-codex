"""Abertura de aplicativos comuns no Windows."""

import os
import subprocess
from app.logger import log_action


def _start(command: str, label: str) -> str:
    subprocess.Popen(command, shell=True)
    log_action(f"{label} aberto")
    return f"{label} aberto."


def abrir_chrome() -> str:
    return _start("start chrome", "Chrome")


def abrir_edge() -> str:
    return _start("start msedge", "Edge")


def abrir_vscode() -> str:
    return _start("code", "VS Code")


def abrir_bloco_de_notas() -> str:
    return _start("notepad", "Bloco de Notas")


def abrir_calculadora() -> str:
    return _start("calc", "Calculadora")


def abrir_programa(nome: str) -> str:
    return _start(f"start {nome}", nome)


def abrir_programa_por_nome(nome: str) -> str:
    return abrir_programa(nome)
