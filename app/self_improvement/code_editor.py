import os
import shutil
from pathlib import Path


class CodeEditor:
    """Aplica mudancas em arquivos com raiz opcionalmente restrita."""

    def __init__(self, root_dir: str | None = None):
        self.root_dir = Path(root_dir).resolve() if root_dir else None

    def _resolve_path(self, path: str) -> Path:
        resolved = Path(path).resolve()
        if self.root_dir is None:
            return resolved
        try:
            resolved.relative_to(self.root_dir)
        except ValueError as error:
            raise ValueError(f"Caminho fora da raiz permitida: {path}") from error
        return resolved

    def write_file(self, path: str, content: str) -> bool:
        try:
            resolved = self._resolve_path(path)
            os.makedirs(resolved.parent, exist_ok=True)
            with open(resolved, "w", encoding="utf-8") as file_handle:
                file_handle.write(content)
            return True
        except Exception as error:
            print(f"Erro ao escrever {path}: {error}")
            return False

    def delete_file(self, path: str) -> bool:
        try:
            resolved = self._resolve_path(path)
            os.remove(resolved)
            return True
        except Exception:
            return False

    def delete_folder(self, path: str) -> bool:
        try:
            resolved = self._resolve_path(path)
            shutil.rmtree(resolved)
            return True
        except Exception:
            return False

    def create_folder(self, path: str) -> bool:
        try:
            resolved = self._resolve_path(path)
            os.makedirs(resolved, exist_ok=True)
            return True
        except Exception:
            return False
