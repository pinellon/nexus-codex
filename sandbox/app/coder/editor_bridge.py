"""Ponte entre voz/botoes e o editor visual do NEXUS."""

from __future__ import annotations

from collections.abc import Callable


class EditorBridge:
    """Permite controlar o editor sem acoplar a logica ao Tkinter."""

    def __init__(
        self,
        initial_code: str = "",
        get_code: Callable[[], str] | None = None,
        set_code: Callable[[str], None] | None = None,
        get_filename: Callable[[], str] | None = None,
        set_filename: Callable[[str], None] | None = None,
        set_output: Callable[[str], None] | None = None,
        clear_output: Callable[[], None] | None = None,
    ):
        self._code = initial_code
        self._filename = "main.py"
        self._output = ""
        self._get_code = get_code
        self._set_code = set_code
        self._get_filename = get_filename
        self._set_filename = set_filename
        self._set_output = set_output
        self._clear_output = clear_output

    def get_code(self) -> str:
        return self._get_code() if self._get_code else self._code

    def set_code(self, code: str):
        if self._set_code:
            self._set_code(code)
        else:
            self._code = code

    def get_filename(self) -> str:
        return self._get_filename() if self._get_filename else self._filename

    def set_filename(self, filename: str):
        if self._set_filename:
            self._set_filename(filename)
        else:
            self._filename = filename

    def set_output(self, text: str):
        if self._set_output:
            self._set_output(text)
        else:
            self._output = text

    def clear_output(self):
        if self._clear_output:
            self._clear_output()
        else:
            self._output = ""
