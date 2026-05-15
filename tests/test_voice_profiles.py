from app.voice.voice_profiles import get_profile, list_profiles


def test_get_profile_returns_jarvis_by_default():
    profile = get_profile("")

    assert profile.id == "jarvis"
    assert "portugues do Brasil" in profile.instructions


def test_list_profiles_exposes_expected_modes():
    profile_ids = {item["id"] for item in list_profiles()}

    assert {"natural", "jarvis", "professor", "rapido", "calmo"} <= profile_ids
