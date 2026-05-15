from __future__ import annotations

from app.self_improvement.code_editor import CodeEditor


def test_code_editor_writes_inside_allowed_root(tmp_path):
    editor = CodeEditor(root_dir=str(tmp_path))
    target = tmp_path / "nested" / "note.txt"

    assert editor.write_file(str(target), "ok") is True
    assert target.read_text(encoding="utf-8") == "ok"


def test_code_editor_rejects_path_escape(tmp_path):
    editor = CodeEditor(root_dir=str(tmp_path))
    escaped = tmp_path.parent / "outside.txt"

    assert editor.write_file(str(escaped), "nope") is False
    assert not escaped.exists()
