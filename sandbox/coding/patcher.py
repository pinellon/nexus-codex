"""Preview e aplicacao de patches gerados pela IA."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import difflib
from pathlib import Path


class PatchError(Exception):
    """Erro seguro de patch."""


@dataclass(frozen=True)
class PatchFile:
    path: str
    content: str


def preview_file_diff(root: Path, relative_path: str, new_content: str) -> str:
    target = _resolve_target(root, relative_path)
    old_content = target.read_text(encoding="utf-8", errors="replace") if target.exists() else ""
    old_lines = old_content.splitlines(keepends=True)
    new_lines = new_content.splitlines(keepends=True)
    diff = difflib.unified_diff(
        old_lines,
        new_lines,
        fromfile=f"antes/{relative_path}",
        tofile=f"depois/{relative_path}",
        lineterm="",
    )
    return "\n".join(diff)


def preview_patch(root: Path, files: list[dict[str, str]] | list[PatchFile]) -> str:
    blocks: list[str] = []
    for item in files:
        path, content = _item_path_content(item)
        if not path:
            continue
        blocks.append(preview_file_diff(root, path, content))
    return "\n\n".join(block for block in blocks if block.strip()).strip() or "Nenhuma alteracao de arquivo."


def apply_patch_files(root: Path, files: list[dict[str, str]] | list[PatchFile], make_backup: bool = True) -> list[str]:
    changed: list[str] = []
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for item in files:
        relative_path, new_content = _item_path_content(item)
        if not relative_path:
            continue
        target = _resolve_target(root, relative_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if make_backup and target.exists():
            backup = target.with_suffix(target.suffix + f".bak_{stamp}")
            backup.write_text(target.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        target.write_text(new_content, encoding="utf-8")
        changed.append(relative_path)
    return changed


def _item_path_content(item) -> tuple[str, str]:
    if isinstance(item, PatchFile):
        return item.path, item.content
    return str(item.get("path", "")), str(item.get("content", ""))


def _resolve_target(root: Path, relative_path: str) -> Path:
    if not relative_path:
        raise PatchError("Caminho vazio.")
    rel = Path(relative_path.replace("\\", "/"))
    if rel.is_absolute() or ".." in rel.parts:
        raise PatchError(f"Caminho fora do projeto bloqueado: {relative_path}")
    root = root.resolve()
    target = (root / rel).resolve()
    if target != root and root not in target.parents:
        raise PatchError(f"Caminho fora do projeto bloqueado: {target}")
    return target
