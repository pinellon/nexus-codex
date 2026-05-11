"""Contexto de projeto para o NEXUS CODER."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from coding.file_manager import CODE_EXTENSIONS, IGNORED_DIRS, get_projeto


@dataclass(frozen=True)
class FileChunk:
    path: str
    content: str


def resolve_project_root(root: str | Path | None = None) -> Path | None:
    if root:
        path = Path(root).expanduser().resolve()
        return path if path.exists() and path.is_dir() else None
    project = get_projeto()
    return project.resolve() if project else None


def iter_project_files(root: Path) -> Iterable[Path]:
    root = root.resolve()
    for path in root.rglob("*"):
        if any(part in IGNORED_DIRS for part in path.parts):
            continue
        if path.is_file() and path.suffix.lower() in CODE_EXTENSIONS:
            yield path


def safe_read(path: Path, max_bytes: int = 80_000) -> str:
    data = path.read_bytes()[:max_bytes]
    return data.decode("utf-8", errors="replace")


def build_tree(root: Path, max_items: int = 160) -> str:
    items: list[str] = []
    for path in iter_project_files(root):
        items.append(path.relative_to(root).as_posix())
        if len(items) >= max_items:
            break
    return "\n".join(f"- {item}" for item in sorted(items))


def build_context_snapshot(
    root: Path | None = None,
    active_file: str = "",
    selection: str = "",
    max_chars: int = 42_000,
) -> str:
    project_root = resolve_project_root(root)
    if not project_root:
        return "Nenhum projeto ativo. Use: define o projeto em C:\\caminho\\do\\projeto"

    parts = ["# ARVORE DO PROJETO", build_tree(project_root)]

    active_rel = active_file.strip().replace("\\", "/")
    if active_rel:
        active_path = (project_root / active_rel).resolve()
        if _inside_root(project_root, active_path) and active_path.exists() and active_path.is_file():
            parts.extend([f"\n# ARQUIVO ATIVO: {active_rel}", safe_read(active_path)])

    if selection.strip():
        parts.extend(["\n# TRECHO SELECIONADO", selection.strip()])

    used = sum(len(part) for part in parts)
    for path in iter_project_files(project_root):
        rel = path.relative_to(project_root).as_posix()
        if active_rel and rel == active_rel:
            continue
        content = safe_read(path, max_bytes=30_000)
        block = f"\n# ARQUIVO: {rel}\n{content}"
        if used + len(block) > max_chars:
            break
        parts.append(block)
        used += len(block)

    return "\n".join(parts)


def summarize_context(root: Path | None = None) -> str:
    project_root = resolve_project_root(root)
    if not project_root:
        return "Nenhum projeto ativo. Use: define o projeto em C:\\caminho\\do\\projeto"

    counts: dict[str, int] = {}
    total = 0
    for path in iter_project_files(project_root):
        counts[path.suffix.lower() or "sem_ext"] = counts.get(path.suffix.lower() or "sem_ext", 0) + 1
        total += 1

    lines = [f"Projeto ativo: {project_root}", f"Arquivos indexados: {total}", "", "Por tipo:"]
    for ext, count in sorted(counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"- {ext}: {count}")
    lines.extend(["", "Arvore:", build_tree(project_root, max_items=80)])
    return "\n".join(lines)


def _inside_root(root: Path, target: Path) -> bool:
    root = root.resolve()
    target = target.resolve()
    return target == root or root in target.parents
