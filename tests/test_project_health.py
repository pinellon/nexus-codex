from __future__ import annotations

from app.features.project_health import analyze_project


def test_project_health_prefers_web_first_stack(tmp_path):
    (tmp_path / "app" / "web").mkdir(parents=True)
    (tmp_path / "frontend" / "src").mkdir(parents=True)
    (tmp_path / "app" / "core").mkdir(parents=True)
    (tmp_path / "app" / "voice").mkdir(parents=True)
    (tmp_path / "app" / "coder").mkdir(parents=True)
    (tmp_path / "README.md").write_text("nexus", encoding="utf-8")
    (tmp_path / "requirements.txt").write_text(
        "fastapi\nspeechrecognition\npsutil\npyautogui\n",
        encoding="utf-8",
    )
    (tmp_path / "main.py").write_text("print('nexus')", encoding="utf-8")
    (tmp_path / "app" / "web" / "server.py").write_text("", encoding="utf-8")
    (tmp_path / "frontend" / "package.json").write_text("{}", encoding="utf-8")
    (tmp_path / "frontend" / "src" / "App.tsx").write_text("export default null", encoding="utf-8")
    (tmp_path / "app" / "settings_manager.py").write_text("", encoding="utf-8")
    (tmp_path / "app" / "core" / "command_router.py").write_text("", encoding="utf-8")
    (tmp_path / "app" / "core" / "safety.py").write_text("", encoding="utf-8")
    (tmp_path / "app" / "voice" / "voice_loop.py").write_text("", encoding="utf-8")
    (tmp_path / "app" / "coder" / "editor_bridge.py").write_text("", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")

    report = analyze_project(tmp_path)

    assert "app/web/server.py" in report.found
    assert "frontend/package.json" in report.found
    assert "frontend/src/App.tsx" in report.found
    assert not any("customtkinter" in warning.lower() for warning in report.warnings)


def test_project_health_marks_desktop_as_legacy_when_present(tmp_path):
    (tmp_path / "ui").mkdir(parents=True)
    (tmp_path / "ui" / "desktop_app.py").write_text("# legacy", encoding="utf-8")

    report = analyze_project(tmp_path)

    assert "ui/desktop_app.py (legado)" in report.found
