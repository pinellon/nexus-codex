"""Exemplo de integracao do EditorBridge com Tkinter/CustomTkinter."""

from __future__ import annotations

import threading

from app.coder.editor_bridge import EditorBridge


def build_editor_bridge(code_textbox, output_textbox, filename_var):
    def get_code():
        return code_textbox.get("1.0", "end-1c")

    def set_code(text: str):
        code_textbox.delete("1.0", "end")
        code_textbox.insert("1.0", text)

    def set_output(text: str):
        output_textbox.delete("1.0", "end")
        output_textbox.insert("1.0", text)

    return EditorBridge(
        get_code=get_code,
        set_code=set_code,
        get_filename=lambda: filename_var.get(),
        set_filename=lambda name: filename_var.set(name),
        set_output=set_output,
        clear_output=lambda: set_output(""),
    )


def start_voice_in_background(voice_loop):
    thread = threading.Thread(target=voice_loop.run, daemon=True)
    thread.start()
    return thread
