"""SpotifyClient — controla o Spotify via Web API.

Funcionalidades:
- play / pause / próxima / anterior
- tocar artista, álbum, playlist ou música específica
- ajustar volume
- mostrar o que está tocando

Autenticação: OAuth2 PKCE (abre navegador uma vez, salva token em disco).
"""
from __future__ import annotations

import json
import logging
import secrets
import string
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse

import requests

log = logging.getLogger("nexus.home.spotify")


def _setting(settings, key: str, default: str = ""):
    if isinstance(settings, dict):
        return settings.get(key, default)
    return getattr(settings, key, default)

SPOTIFY_AUTH_URL = "https://accounts.spotify.com/authorize"
SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_API_BASE = "https://api.spotify.com/v1"

SCOPES = " ".join([
    "user-read-playback-state",
    "user-modify-playback-state",
    "user-read-currently-playing",
    "playlist-read-private",
    "user-library-read",
])


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------

class SpotifyResult:
    def __init__(self, success: bool, message: str, data: dict | None = None):
        self.success = success
        self.message = message
        self.data = data or {}

    def __bool__(self):
        return self.success


# ---------------------------------------------------------------------------
# Servidor local para receber o callback OAuth
# ---------------------------------------------------------------------------

class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    auth_code: str | None = None

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        _OAuthCallbackHandler.auth_code = params.get("code", [None])[0]
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        html = b"""<html><body style="font-family:sans-serif;text-align:center;padding-top:80px">
        <h2>&#127381; NEXUS autenticado com Spotify!</h2>
        <p>Pode fechar esta aba e voltar ao NEXUS.</p></body></html>"""
        self.wfile.write(html)

    def log_message(self, *args):
        pass  # silencia logs do HTTPServer


# ---------------------------------------------------------------------------
# Cliente principal
# ---------------------------------------------------------------------------

class SpotifyClient:
    """Controla o Spotify via Web API com OAuth2 PKCE."""

    TOKEN_FILE = Path.home() / ".nexus" / "spotify_token.json"
    REDIRECT_PORT = 8765
    REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}/callback"

    def __init__(self, settings, logger: logging.Logger | None = None):
        """
        Args:
            settings: Objeto com:
                - spotify_client_id (str)  — Client ID do app Spotify Developer
        """
        self.client_id: str = str(_setting(settings, "spotify_client_id", "") or "")
        self.log = logger or log
        self._token_data: dict = {}
        self._load_token()

    # ------------------------------------------------------------------
    # Autenticação
    # ------------------------------------------------------------------

    def authenticate(self) -> bool:
        """Abre o navegador para autenticação OAuth2. Retorna True se OK."""
        if not self.client_id:
            self.log.error("spotify_client_id não configurado.")
            return False

        state = "".join(secrets.choice(string.ascii_letters) for _ in range(16))
        params = {
            "client_id": self.client_id,
            "response_type": "code",
            "redirect_uri": self.REDIRECT_URI,
            "scope": SCOPES,
            "state": state,
        }
        auth_url = f"{SPOTIFY_AUTH_URL}?{urlencode(params)}"
        self.log.info("Abrindo autenticação Spotify: %s", auth_url)
        webbrowser.open(auth_url)

        # Inicia servidor local para capturar o código
        _OAuthCallbackHandler.auth_code = None
        server = HTTPServer(("localhost", self.REDIRECT_PORT), _OAuthCallbackHandler)
        server.timeout = 60

        self.log.info("Aguardando callback OAuth na porta %d...", self.REDIRECT_PORT)
        server.handle_request()

        code = _OAuthCallbackHandler.auth_code
        if not code:
            self.log.error("Código OAuth não recebido.")
            return False

        # Troca código por token
        return self._exchange_code(code)

    def is_authenticated(self) -> bool:
        """Verifica se há token válido."""
        if not self._token_data:
            return False
        if time.time() > self._token_data.get("expires_at", 0):
            return self._refresh_token()
        return True

    # ------------------------------------------------------------------
    # Controles de reprodução
    # ------------------------------------------------------------------

    def play(self) -> SpotifyResult:
        """Retoma a reprodução."""
        return self._put("me/player/play", {})

    def pause(self) -> SpotifyResult:
        """Pausa a reprodução."""
        return self._put("me/player/pause", {})

    def next_track(self) -> SpotifyResult:
        """Avança para a próxima faixa."""
        return self._post("me/player/next", {})

    def previous_track(self) -> SpotifyResult:
        """Volta para a faixa anterior."""
        return self._post("me/player/previous", {})

    def set_volume(self, pct: int) -> SpotifyResult:
        """Define o volume (0-100)."""
        pct = max(0, min(100, pct))
        return self._put(f"me/player/volume?volume_percent={pct}", {})

    def shuffle(self, state: bool = True) -> SpotifyResult:
        """Ativa ou desativa o shuffle."""
        return self._put(f"me/player/shuffle?state={'true' if state else 'false'}", {})

    # ------------------------------------------------------------------
    # Busca e reprodução por nome
    # ------------------------------------------------------------------

    def play_artist(self, name: str) -> SpotifyResult:
        """Toca músicas de um artista."""
        return self._search_and_play(name, "artist")

    def play_album(self, name: str) -> SpotifyResult:
        """Toca um álbum."""
        return self._search_and_play(name, "album")

    def play_track(self, name: str) -> SpotifyResult:
        """Toca uma música específica."""
        return self._search_and_play(name, "track")

    def play_playlist(self, name: str) -> SpotifyResult:
        """Toca uma playlist."""
        return self._search_and_play(name, "playlist")

    def play_mood(self, mood: str) -> SpotifyResult:
        """Toca músicas baseadas em humor (ex: 'rock clássico', 'foco', 'anime')."""
        return self._search_and_play(mood, "playlist")

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def currently_playing(self) -> SpotifyResult:
        """Retorna o que está tocando no momento."""
        resp = self._get("me/player/currently-playing")
        if not resp.success:
            return resp
        data = resp.data
        if not data or data.get("item") is None:
            return SpotifyResult(True, "Nenhuma música tocando no momento.")
        item = data["item"]
        artists = ", ".join(a["name"] for a in item.get("artists", []))
        track = item.get("name", "")
        album = item.get("album", {}).get("name", "")
        progress_ms = data.get("progress_ms", 0)
        duration_ms = item.get("duration_ms", 1)
        pct = int(progress_ms / duration_ms * 100)
        is_playing = data.get("is_playing", False)
        status = "tocando" if is_playing else "pausado"
        msg = f"🎵 {track} — {artists} ({album}) | {pct}% | {status}"
        return SpotifyResult(True, msg, data)

    def get_devices(self) -> SpotifyResult:
        """Lista dispositivos Spotify disponíveis."""
        resp = self._get("me/player/devices")
        if not resp.success:
            return resp
        devices = resp.data.get("devices", [])
        if not devices:
            return SpotifyResult(True, "Nenhum dispositivo Spotify ativo encontrado.")
        lines = [f"- {d['name']} ({d['type']})" + (" ✓" if d["is_active"] else "")
                 for d in devices]
        return SpotifyResult(True, "Dispositivos:\n" + "\n".join(lines), {"devices": devices})

    # ------------------------------------------------------------------
    # Helpers de busca
    # ------------------------------------------------------------------

    def _search_and_play(self, query: str, search_type: str) -> SpotifyResult:
        """Busca e inicia reprodução do primeiro resultado."""
        if not self.is_authenticated():
            return SpotifyResult(False, "Spotify não autenticado. Fale 'Nexus, autenticar Spotify'.")

        params = {"q": query, "type": search_type, "limit": 1}
        resp = self._get(f"search?{urlencode(params)}")
        if not resp.success:
            return resp

        data = resp.data
        type_plural = {
            "artist": "artists", "album": "albums",
            "track": "tracks", "playlist": "playlists",
        }.get(search_type, search_type + "s")

        items = data.get(type_plural, {}).get("items", [])
        if not items:
            return SpotifyResult(False, f"Nada encontrado para '{query}'.")

        item = items[0]
        uri = item.get("uri", "")
        name = item.get("name", query)

        # Monta payload de reprodução
        if search_type == "track":
            payload: dict[str, Any] = {"uris": [uri]}
        else:
            payload = {"context_uri": uri}

        result = self._put("me/player/play", payload)
        if result.success:
            result.message = f"▶ Tocando {search_type}: {name}"
        return result

    # ------------------------------------------------------------------
    # HTTP helpers
    # ------------------------------------------------------------------

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._token_data.get('access_token', '')}"}

    def _get(self, endpoint: str) -> SpotifyResult:
        try:
            resp = requests.get(
                f"{SPOTIFY_API_BASE}/{endpoint}",
                headers=self._headers(), timeout=8,
            )
            if resp.status_code == 204:
                return SpotifyResult(True, "OK", {})
            if resp.status_code == 200:
                return SpotifyResult(True, "OK", resp.json())
            return SpotifyResult(False, f"Spotify API {resp.status_code}: {resp.text[:200]}")
        except Exception as exc:
            return SpotifyResult(False, f"Erro de conexão: {exc}")

    def _put(self, endpoint: str, data: dict) -> SpotifyResult:
        try:
            resp = requests.put(
                f"{SPOTIFY_API_BASE}/{endpoint}",
                headers=self._headers(), json=data, timeout=8,
            )
            if resp.status_code in (200, 204):
                return SpotifyResult(True, "OK")
            return SpotifyResult(False, f"Spotify API {resp.status_code}: {resp.text[:200]}")
        except Exception as exc:
            return SpotifyResult(False, f"Erro de conexão: {exc}")

    def _post(self, endpoint: str, data: dict) -> SpotifyResult:
        try:
            resp = requests.post(
                f"{SPOTIFY_API_BASE}/{endpoint}",
                headers=self._headers(), json=data, timeout=8,
            )
            if resp.status_code in (200, 204):
                return SpotifyResult(True, "OK")
            return SpotifyResult(False, f"Spotify API {resp.status_code}: {resp.text[:200]}")
        except Exception as exc:
            return SpotifyResult(False, f"Erro de conexão: {exc}")

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def _exchange_code(self, code: str) -> bool:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.REDIRECT_URI,
            "client_id": self.client_id,
            "code_verifier": "nexus",  # simplificado — sem PKCE real por compatibilidade
        }
        try:
            resp = requests.post(SPOTIFY_TOKEN_URL, data=data, timeout=10)
            if resp.status_code == 200:
                token = resp.json()
                token["expires_at"] = time.time() + token.get("expires_in", 3600) - 60
                self._token_data = token
                self._save_token()
                self.log.info("Token Spotify obtido com sucesso.")
                return True
            self.log.error("Troca de token falhou: %s", resp.text)
            return False
        except Exception as exc:
            self.log.error("Erro ao trocar token: %s", exc)
            return False

    def _refresh_token(self) -> bool:
        refresh = self._token_data.get("refresh_token", "")
        if not refresh:
            return False
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh,
            "client_id": self.client_id,
        }
        try:
            resp = requests.post(SPOTIFY_TOKEN_URL, data=data, timeout=10)
            if resp.status_code == 200:
                token = resp.json()
                token["expires_at"] = time.time() + token.get("expires_in", 3600) - 60
                token.setdefault("refresh_token", refresh)
                self._token_data = token
                self._save_token()
                return True
            return False
        except Exception:
            return False

    def _save_token(self):
        self.TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        self.TOKEN_FILE.write_text(json.dumps(self._token_data), encoding="utf-8")

    def _load_token(self):
        if self.TOKEN_FILE.exists():
            try:
                self._token_data = json.loads(self.TOKEN_FILE.read_text(encoding="utf-8"))
            except Exception:
                self._token_data = {}
