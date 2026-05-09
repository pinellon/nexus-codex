"""Testes do módulo app/home — rodar com:  pytest tests/test_home.py -v"""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.home.home_commands import detect_home_intent, is_home_command, HomeCommandHandler
from app.home.home_assistant import HAResult, HAState


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _settings():
    return SimpleNamespace(
        ha_url="http://homeassistant.local:8123",
        ha_token="token-fake",
        spotify_client_id="client-fake",
        ha_default_light="light.sala",
        ha_default_ac="climate.sala",
    )


# ---------------------------------------------------------------------------
# is_home_command
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "Nexus, apaga as luzes",
    "liga o ar condicionado",
    "toca AC/DC no Spotify",
    "volume mais alto",
    "modo cinema",
    "o que está tocando?",
    "status da casa",
    "temperatura 22",
])
def test_is_home_command_true(text):
    assert is_home_command(text) is True


@pytest.mark.parametrize("text", [
    "pesquisa Python no Obsidian",
    "o que está na tela?",
    "abrir Chrome",
    "status do CPU",
])
def test_is_home_command_false(text):
    assert is_home_command(text) is False


# ---------------------------------------------------------------------------
# detect_home_intent
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text, expected", [
    ("apaga as luzes",                "lights_off"),
    ("apaga tudo",                    "lights_off_all"),
    ("liga as luzes da sala",         "lights_on"),
    ("brilho 50",                     "set_brightness"),
    ("luz mais fraca",                "lights_dim"),
    ("luz mais forte",                "lights_bright"),
    ("modo cinema",                   "activate_scene"),
    ("temperatura 23",                "set_temperature"),
    ("liga o ar",                     "ac_on"),
    ("desliga o ar condicionado",     "ac_off"),
    ("modo frio",                     "ac_cool"),
    ("pausa a música",                "spotify_pause"),
    ("próxima música",                "spotify_next"),
    ("anterior",                      "spotify_prev"),
    ("volume mais alto",              "spotify_vol_up"),
    ("volume mais baixo",             "spotify_vol_down"),
    ("volume 70",                     "spotify_vol_set"),
    ("o que está tocando?",           "spotify_now"),
    ("ativa shuffle",                 "spotify_shuffle_on"),
    ("desativa shuffle",              "spotify_shuffle_off"),
    ("autentica no Spotify",          "spotify_auth"),
    ("status da casa",                "home_status"),
    ("lista as luzes",                "list_lights"),
])
def test_detect_intent(text, expected):
    intent, _ = detect_home_intent(text)
    assert intent == expected


# ---------------------------------------------------------------------------
# HomeAssistantClient
# ---------------------------------------------------------------------------

def test_ha_light_on():
    from app.home.home_assistant import HomeAssistantClient
    settings = _settings()
    ha = HomeAssistantClient(settings)

    with patch.object(ha._session, "post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200, text="")
        result = ha.light_on("light.sala", brightness=80)

    assert result.success is True
    assert "Sala" in result.message or "sala" in result.message.lower()


def test_ha_light_off():
    from app.home.home_assistant import HomeAssistantClient
    settings = _settings()
    ha = HomeAssistantClient(settings)

    with patch.object(ha._session, "post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200, text="")
        result = ha.light_off("light.sala")

    assert result.success is True


def test_ha_connection_error():
    from app.home.home_assistant import HomeAssistantClient
    import requests as req
    settings = _settings()
    ha = HomeAssistantClient(settings)

    with patch.object(ha._session, "post", side_effect=req.ConnectionError("refused")):
        result = ha.light_on("light.sala")

    assert result.success is False
    assert "não encontrado" in result.message.lower() or "connection" in result.message.lower()


def test_ha_state_from_json():
    data = {
        "entity_id": "light.sala",
        "state": "on",
        "attributes": {"friendly_name": "Sala", "brightness": 255},
    }
    state = HAState.from_json(data)
    assert state.entity_id == "light.sala"
    assert state.state == "on"
    assert state.friendly_name == "Sala"


# ---------------------------------------------------------------------------
# SpotifyClient
# ---------------------------------------------------------------------------

def test_spotify_currently_playing_nothing():
    from app.home.spotify import SpotifyClient
    settings = _settings()
    sp = SpotifyClient(settings)
    sp._token_data = {"access_token": "tok", "expires_at": 9999999999}

    with patch("app.home.spotify.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"is_playing": False, "item": None},
        )
        result = sp.currently_playing()

    assert result.success is True
    assert "Nenhuma" in result.message


def test_spotify_pause():
    from app.home.spotify import SpotifyClient
    settings = _settings()
    sp = SpotifyClient(settings)
    sp._token_data = {"access_token": "tok", "expires_at": 9999999999}

    with patch("app.home.spotify.requests.put") as mock_put:
        mock_put.return_value = MagicMock(status_code=204)
        result = sp.pause()

    assert result.success is True


# ---------------------------------------------------------------------------
# HomeCommandHandler
# ---------------------------------------------------------------------------

def test_handler_lights_off():
    settings = _settings()
    messages = []
    handler = HomeCommandHandler(settings, ui_callback=lambda m: messages.append(m))

    with patch.object(handler.ha._session, "post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200, text="")
        # Executa síncrono para testar
        intent, params = detect_home_intent("apaga as luzes da sala")
        result = handler._dispatch(intent, params)

    assert result is not None


def test_handler_extract_room():
    settings = _settings()
    handler = HomeCommandHandler(settings)
    assert handler._extract_room_light("luzes do quarto") == "light.quarto"
    assert handler._extract_room_light("luz da cozinha") == "light.cozinha"
    assert handler._extract_room_light("sem cômodo específico") is None


def test_handler_extract_music_query():
    settings = _settings()
    handler = HomeCommandHandler(settings)
    assert handler._extract_music_query("toca AC/DC no Spotify") == "AC/DC"
    assert handler._extract_music_query("coloca Metallica") == "Metallica"
    assert handler._extract_music_query("toca playlist de rock") == "playlist de rock"
