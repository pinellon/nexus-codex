from __future__ import annotations

import app.settings_manager as settings_manager


def test_save_preserves_existing_unedited_values(tmp_path, monkeypatch):
    settings_file = tmp_path / "settings.json"
    monkeypatch.setattr(settings_manager, "SETTINGS_FILE", settings_file)

    settings_manager.save(
        {
            "voice_require_wake_word": False,
            "voice_listen_timeout": 9,
            "voice_phrase_time_limit": 18,
        }
    )

    saved = settings_manager.save({"owner_name": "Nexus"})

    assert saved["owner_name"] == "Nexus"
    assert saved["voice_require_wake_word"] is False
    assert saved["voice_listen_timeout"] == 9
    assert saved["voice_phrase_time_limit"] == 18
