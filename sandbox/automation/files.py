"""Automacoes de arquivos e pastas."""

import os
from pathlib import Path
from app.logger import log_action

DESKTOP = Path.home() / "Desktop"
DOWNLOADS = Path.home() / "Downloads"


def abrir_pasta(path: str | Path) -> str:
    os.startfile(str(path))
    log_action(f"Pasta aberta: {path}")
    return "Pasta aberta."


def abrir_downloads() -> str:
    return abrir_pasta(DOWNLOADS)


def abrir_area_trabalho() -> str:
    return abrir_pasta(DESKTOP)


def criar_arquivo(nome: str, conteudo: str = "") -> str:
    path = DESKTOP / nome
    path.write_text(conteudo, encoding="utf-8")
    log_action(f"Arquivo criado: {path}")
    return f"Arquivo '{nome}' criado."


def procurar_arquivo(nome: str, pasta_raiz: str | None = None) -> str:
    raiz = Path(pasta_raiz) if pasta_raiz else Path.home()
    resultados = list(raiz.rglob(f"*{nome}*"))[:5]
    if not resultados:
        return f"Nenhum arquivo com '{nome}' encontrado."
    return "Encontrado:\n" + "\n".join(str(p) for p in resultados)

