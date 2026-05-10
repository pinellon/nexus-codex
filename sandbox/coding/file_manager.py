"""Gerenciador de arquivos e projetos para o NEXUS CODER."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import os
import re
import shutil
import subprocess


CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss", ".java", ".c",
    ".cpp", ".cs", ".go", ".rs", ".rb", ".php", ".sql", ".sh", ".bat", ".ps1",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env", ".md", ".txt", ".xml",
}

IGNORED_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", "dist", "build", ".next", ".idea", ".vscode"}


@dataclass
class FileResult:
    success: bool
    message: str
    data: str = ""

    def __str__(self) -> str:
        return self.message


_projeto_ativo: Path | None = None


def definir_projeto(caminho: str) -> FileResult:
    global _projeto_ativo
    path = Path(caminho).expanduser().resolve()
    if not path.exists():
        return FileResult(False, f"Caminho nao encontrado: {caminho}")
    if not path.is_dir():
        return FileResult(False, f"Nao e um diretorio: {caminho}")
    _projeto_ativo = path
    return FileResult(True, f"Projeto definido: {path}", str(path))


def get_projeto() -> Path | None:
    return _projeto_ativo


def _base() -> Path:
    return _projeto_ativo or (Path.home() / "Desktop")


def criar_arquivo_codigo(nome: str, conteudo: str, subpasta: str = "") -> FileResult:
    base = _base()
    folder = base / subpasta if subpasta else base
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / nome
    if path.exists():
        backup = path.with_suffix(path.suffix + f".bak{datetime.now():%H%M%S}")
        shutil.copy2(path, backup)
    path.write_text(conteudo, encoding="utf-8")
    return FileResult(True, f"Arquivo criado: {path}", str(path))


def _resolver_caminho(caminho: str) -> Path | None:
    p = Path(caminho).expanduser()
    if p.is_absolute() and p.exists():
        return p
    if _projeto_ativo:
        candidate = _projeto_ativo / caminho
        if candidate.exists():
            return candidate
        matches = list(_projeto_ativo.rglob(caminho))
        if matches:
            return matches[0]
    return p if p.exists() else None


def ler_arquivo(caminho: str) -> FileResult:
    path = _resolver_caminho(caminho)
    if not path:
        return FileResult(False, f"Arquivo nao encontrado: {caminho}")
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        return FileResult(True, f"{path.name} ({len(content.splitlines())} linhas)", content)
    except Exception as error:
        return FileResult(False, f"Erro ao ler: {error}")


def editar_arquivo(caminho: str, busca: str, substituto: str) -> FileResult:
    path = _resolver_caminho(caminho)
    if not path:
        return FileResult(False, f"Arquivo nao encontrado: {caminho}")
    content = path.read_text(encoding="utf-8")
    if busca not in content:
        return FileResult(False, f"Trecho nao encontrado em {path.name}")
    path.with_suffix(path.suffix + ".bak").write_text(content, encoding="utf-8")
    path.write_text(content.replace(busca, substituto, 1), encoding="utf-8")
    return FileResult(True, f"Arquivo editado: {path.name}")


def adicionar_ao_arquivo(caminho: str, conteudo: str, posicao: str = "fim") -> FileResult:
    path = _resolver_caminho(caminho)
    if not path:
        return FileResult(False, f"Arquivo nao encontrado: {caminho}")
    current = path.read_text(encoding="utf-8")
    new = f"{conteudo}\n{current}" if posicao == "inicio" else f"{current}\n{conteudo}"
    path.write_text(new, encoding="utf-8")
    return FileResult(True, f"Conteudo adicionado ao {path.name}")


def listar_projeto(profundidade: int = 3, apenas_codigo: bool = True) -> FileResult:
    base = _projeto_ativo
    if not base:
        return FileResult(False, "Nenhum projeto ativo. Use 'define o projeto em ...'.")
    lines = [f"{base.name}/"]
    _tree(base, lines, "", profundidade, apenas_codigo)
    return FileResult(True, "\n".join(lines), "\n".join(lines))


def _tree(path: Path, lines: list[str], prefix: str, depth: int, apenas_codigo: bool):
    if depth <= 0:
        return
    try:
        items = sorted([p for p in path.iterdir() if p.name not in IGNORED_DIRS and not p.name.startswith(".")], key=lambda p: (p.is_file(), p.name.lower()))
    except PermissionError:
        return
    for index, item in enumerate(items):
        connector = "`-- " if index == len(items) - 1 else "|-- "
        extension = "    " if index == len(items) - 1 else "|   "
        if item.is_dir():
            lines.append(f"{prefix}{connector}{item.name}/")
            _tree(item, lines, prefix + extension, depth - 1, apenas_codigo)
        elif item.is_file() and (not apenas_codigo or item.suffix in CODE_EXTENSIONS):
            lines.append(f"{prefix}{connector}{item.name} ({_human_size(item.stat().st_size)})")


def _human_size(size: int) -> str:
    for unit in ("B", "KB", "MB"):
        if size < 1024:
            return f"{size:.0f}{unit}"
        size /= 1024
    return f"{size:.1f}GB"


def buscar_em_projeto(termo: str, extensoes: list[str] | None = None) -> FileResult:
    base = _projeto_ativo
    if not base:
        return FileResult(False, "Nenhum projeto ativo.")
    results = []
    for file in base.rglob("*"):
        if any(part in IGNORED_DIRS for part in file.parts) or not file.is_file():
            continue
        if extensoes and file.suffix not in extensoes:
            continue
        if file.suffix not in CODE_EXTENSIONS:
            continue
        try:
            for number, line in enumerate(file.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                if re.search(termo, line, re.IGNORECASE):
                    results.append(f"{file.relative_to(base)}:{number} -> {line.strip()[:100]}")
        except Exception:
            continue
    if not results:
        return FileResult(False, f"'{termo}' nao encontrado.")
    text = f"{len(results)} ocorrencias de '{termo}':\n" + "\n".join(results[:40])
    if len(results) > 40:
        text += f"\n... e mais {len(results) - 40}."
    return FileResult(True, text, "\n".join(results))


def abrir_no_editor(caminho: str) -> FileResult:
    path = _resolver_caminho(caminho)
    if not path:
        return FileResult(False, f"Arquivo nao encontrado: {caminho}")
    for command in (["code", str(path)], ["cursor", str(path)], ["notepad", str(path)]):
        if shutil.which(command[0]):
            subprocess.Popen(command)
            return FileResult(True, f"Abrindo no editor: {path.name}")
    try:
        os.startfile(str(path))
        return FileResult(True, f"Arquivo aberto: {path.name}")
    except Exception as error:
        return FileResult(False, f"Nao foi possivel abrir: {error}")


def contar_linhas_projeto() -> FileResult:
    base = _projeto_ativo
    if not base:
        return FileResult(False, "Nenhum projeto ativo.")
    counts: dict[str, int] = {}
    total_files = 0
    for file in base.rglob("*"):
        if any(part in IGNORED_DIRS for part in file.parts) or not file.is_file() or file.suffix not in CODE_EXTENSIONS:
            continue
        try:
            lines = len(file.read_text(encoding="utf-8", errors="ignore").splitlines())
            counts[file.suffix or "sem_ext"] = counts.get(file.suffix or "sem_ext", 0) + lines
            total_files += 1
        except Exception:
            continue
    if not counts:
        return FileResult(False, "Nenhum arquivo de codigo encontrado.")
    ordered = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    text = [f"Estatisticas de {base.name}:"]
    text += [f"{ext:10s} {qty:>7} linhas" for ext, qty in ordered]
    text.append(f"TOTAL      {sum(counts.values()):>7} linhas em {total_files} arquivos")
    return FileResult(True, "\n".join(text))

