"""Acoes de Coder acionadas por voz."""

from __future__ import annotations

from pathlib import Path

from app.core.text_utils import safe_filename
from coding.code_assistant import documentar_codigo, explicar_codigo, revisar_codigo
from coding.code_runner import executar_auto
from coding.file_manager import criar_arquivo_codigo


class CoderActions:
    def __init__(self, editor):
        self.editor = editor

    def run_current_code(self, language: str = "python") -> str:
        code = self.editor.get_code()
        result = executar_auto(code, language)
        output = result.format()
        self.editor.set_output(output)
        return output

    def explain_current_code(self) -> str:
        answer = explicar_codigo(self.editor.get_code())
        self.editor.set_output(answer)
        return answer

    def fix_current_code(self) -> str:
        answer = revisar_codigo(self.editor.get_code())
        self.editor.set_output(answer)
        return answer

    def document_current_code(self) -> str:
        answer = documentar_codigo(self.editor.get_code())
        self.editor.set_output(answer)
        return answer

    def save_current_file(self, filename: str | None = None) -> str:
        filename = safe_filename(filename or self.editor.get_filename() or "main.py")
        result = criar_arquivo_codigo(filename, self.editor.get_code())
        if result.success:
            self.editor.set_filename(Path(result.data).name)
        return result.message

    def new_file(self, filename: str | None = None) -> str:
        filename = safe_filename(filename or "novo_arquivo.py")
        self.editor.set_filename(filename)
        self.editor.set_code("")
        self.editor.set_output(f"Novo arquivo: {filename}")
        return f"Novo arquivo: {filename}"

    def clear_output(self) -> str:
        self.editor.clear_output()
        return "Terminal limpo."
