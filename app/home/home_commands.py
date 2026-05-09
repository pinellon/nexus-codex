"""Integração do módulo home com o CommandRouter do NEXUS.

Detecta comandos de automação residencial e Spotify e os executa.
"""
from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass
from typing import Callable

from .home_assistant import HomeAssistantClient
from .spotify import SpotifyClient

log = logging.getLogger("nexus.home_commands")


def _setting(settings, key: str, default: str = ""):
    if isinstance(settings, dict):
        return settings.get(key, default)
    return getattr(settings, key, default)


# ---------------------------------------------------------------------------
# Padrões de intenção
# ---------------------------------------------------------------------------

_PATTERNS: list[tuple[re.Pattern, str]] = [
    # ── Luzes ────────────────────────────────────────────────────────────
    (re.compile(r"(apaga?|desliga?|desative?)\s+(as\s+)?luz(es)?", re.I),    "lights_off"),
    (re.compile(r"(liga?|acende?|ative?)\s+(as\s+)?luz(es)?", re.I),         "lights_on"),
    (re.compile(r"(apaga?|desliga?)\s+tud[oa]", re.I),                        "lights_off_all"),
    (re.compile(r"brilho\s+(\d+)", re.I),                                     "set_brightness"),
    (re.compile(r"luz(es)?\s+(mais\s+)?(fraca|baixa|suave|dimmer?)", re.I),  "lights_dim"),
    (re.compile(r"luz(es)?\s+(mais\s+)?(forte|alta|máxima|brilhante)", re.I),"lights_bright"),

    # ── Cenas ───────────────────────────────────────────────────────────
    (re.compile(r"(ativa?|cena|modo)\s+(cena\s+)?(.+)", re.I),               "activate_scene"),
    (re.compile(r"modo\s+(filme|cinema|relaxar|jantar|leitura|trabalho)", re.I), "activate_scene"),

    # ── Ar-condicionado / Clima ──────────────────────────────────────────
    (re.compile(r"(temperatura|temp)\s+(\d+)", re.I),                         "set_temperature"),
    (re.compile(r"(liga?|ativa?)\s+(o\s+)?(ar|ac|ar.condicionado)", re.I),   "ac_on"),
    (re.compile(r"(desliga?|desative?)\s+(o\s+)?(ar|ac|ar.condicionado)", re.I), "ac_off"),
    (re.compile(r"(modo\s+)?(frio|gelado|refrigera)", re.I),                  "ac_cool"),
    (re.compile(r"(modo\s+)?(quente|aquece)", re.I),                          "ac_heat"),

    # ── Spotify / Música ────────────────────────────────────────────────
    (re.compile(r"(toca?|reproduz|coloca?|bota?)\s+(.+)\s+(no\s+spotify|spotify)", re.I), "spotify_play_query"),
    (re.compile(r"(toca?|reproduz|coloca?|bota?)\s+(ac/dc|acdc|ac dc|metallica|"
                r"beatles|nirvana|queen|billie|taylor|daft punk)", re.I),      "spotify_play_artist"),
    (re.compile(r"(toca?|play|música|coloca?)\s+(.+)", re.I),                 "spotify_play_query"),
    (re.compile(r"(pausa?|pause|para\s+a?\s+música)", re.I),                  "spotify_pause"),
    (re.compile(r"(retoma?|continua?|resume|desprende?)\s*(a\s+música)?", re.I), "spotify_play"),
    (re.compile(r"(próxima?|próximo|next|avança?)\s*(música|faixa|track)?", re.I), "spotify_next"),
    (re.compile(r"(anterior|voltar?|volta|previous|prev)\s*(música|faixa)?", re.I), "spotify_prev"),
    (re.compile(r"volume\s+(mais\s+)?(alto|alta|aumenta?|sobe?|up)", re.I),   "spotify_vol_up"),
    (re.compile(r"volume\s+(mais\s+)?(baixo|baixa|diminui?|desce?|down)", re.I), "spotify_vol_down"),
    (re.compile(r"volume\s+(\d+)", re.I),                                      "spotify_vol_set"),
    (re.compile(r"(o que (está|ta|tá) tocando|que música é essa|qual (é a |a )?música)", re.I), "spotify_now"),
    (re.compile(r"(ativa?|liga?)\s+shuffle", re.I),                            "spotify_shuffle_on"),
    (re.compile(r"(desativa?|desliga?)\s+shuffle", re.I),                      "spotify_shuffle_off"),
    (re.compile(r"(autentica?|loga?|conecta?)\s+(no\s+)?spotify", re.I),       "spotify_auth"),

    # ── Status da casa ───────────────────────────────────────────────────
    (re.compile(r"(status|estado|como (está|tá))\s+(a\s+)?(casa|home)", re.I), "home_status"),
    (re.compile(r"(lista?|mostra?|quais)\s+(as\s+)?(luzes?|lights?)", re.I),   "list_lights"),
]

_ALL_HOME_WORDS = re.compile(
    r"\b(luz|luzes|lampada|lâmpada|abajur|spot|teto|sala|quarto|banheiro|"
    r"cozinha|escritório|varanda|garage|garagem|ar.condicionado|temperatura|"
    r"spotify|música|musica|toca|play|pausa|volume|shuffle|cena|modo cinema|"
    r"casa|home assistant|automação)\b",
    re.I,
)


def is_home_command(text: str) -> bool:
    """Retorna True se o texto parece um comando de casa ou Spotify."""
    if "tocando" in (text or "").lower():
        return True
    return bool(_ALL_HOME_WORDS.search(text))


def detect_home_intent(text: str) -> tuple[str, dict]:
    """Retorna (intent, params) para o texto."""
    lowered = (text or "").lower()
    priority_patterns = [
        (r"desliga\s+o\s+ar(\s+condicionado)?", "ac_off"),
        (r"modo\s+frio", "ac_cool"),
        (r"desativa\s+shuffle", "spotify_shuffle_off"),
        (r"ativa\s+shuffle", "spotify_shuffle_on"),
        (r"status\s+da\s+casa", "home_status"),
        (r"o que (esta|está|ta|tá) tocando", "spotify_now"),
    ]
    for pattern, intent in priority_patterns:
        match = re.search(pattern, lowered, re.I)
        if match:
            return intent, {"match": match, "text": text}

    for pattern, intent in _PATTERNS:
        m = pattern.search(text)
        if m:
            return intent, {"match": m, "text": text}
    return "unknown", {"text": text}


# ---------------------------------------------------------------------------
# Resultado
# ---------------------------------------------------------------------------

@dataclass
class HomeResult:
    intent: str = "home"
    label: str = "Automação Residencial"
    args: dict = None

    def __post_init__(self):
        self.args = self.args or {}


# ---------------------------------------------------------------------------
# Handler principal
# ---------------------------------------------------------------------------

class HomeCommandHandler:
    """Gerencia automação residencial integrado ao NEXUS."""

    # Volume padrão para aumentar/diminuir
    VOL_STEP = 15
    # Entidade padrão de luz (sobrescrito pelo settings)
    DEFAULT_LIGHT = "light.sala"
    # Entidade padrão de AC
    DEFAULT_AC = "climate.sala"

    def __init__(
        self,
        settings,
        logger: logging.Logger | None = None,
        ui_callback: Callable[[str], None] | None = None,
    ):
        self.settings = settings
        self.log = logger or log
        self.ui_callback = ui_callback or (lambda msg: print(f"[NEXUS Home] {msg}"))
        self.ha = HomeAssistantClient(settings, logger)
        self.spotify = SpotifyClient(settings, logger)
        self._vol_current = 50   # volume atual estimado

        # Entidades configuráveis
        self.default_light: str = str(_setting(settings, "ha_default_light", self.DEFAULT_LIGHT) or self.DEFAULT_LIGHT)
        self.default_ac: str = str(_setting(settings, "ha_default_ac", self.DEFAULT_AC) or self.DEFAULT_AC)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def handle(self, raw_text: str) -> HomeResult:
        """Detecta intent e executa em background."""
        intent, params = detect_home_intent(raw_text)
        threading.Thread(
            target=self._execute,
            args=(intent, params),
            daemon=True,
            name="nexus-home",
        ).start()
        return HomeResult(intent="home", label="Automação Residencial",
                          args={"intent": intent})

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def _execute(self, intent: str, params: dict) -> None:
        try:
            msg = self._dispatch(intent, params)
            if msg:
                self.ui_callback(f"🏠 {msg}")
        except Exception as exc:
            self.log.error("Home execute error: %s", exc)
            self.ui_callback(f"⚠️ Erro na automação: {exc}")

    def _dispatch(self, intent: str, params: dict) -> str:
        text: str = params.get("text", "")
        match = params.get("match")

        # ── Luzes ────────────────────────────────────────────────────
        if intent == "lights_off":
            entity = self._extract_room_light(text) or self.default_light
            r = self.ha.light_off(entity)
            return r.message

        if intent in ("lights_off_all",):
            r = self.ha.lights_all_off()
            return r.message

        if intent == "lights_on":
            entity = self._extract_room_light(text) or self.default_light
            r = self.ha.light_on(entity)
            return r.message

        if intent == "set_brightness":
            pct = int(match.group(1)) if match else 50
            entity = self._extract_room_light(text) or self.default_light
            r = self.ha.set_brightness(entity, pct)
            return r.message

        if intent == "lights_dim":
            entity = self._extract_room_light(text) or self.default_light
            r = self.ha.set_brightness(entity, 20)
            return r.message

        if intent == "lights_bright":
            entity = self._extract_room_light(text) or self.default_light
            r = self.ha.set_brightness(entity, 100)
            return r.message

        # ── Cenas ───────────────────────────────────────────────────
        if intent == "activate_scene":
            scene = self._extract_scene(text)
            r = self.ha.activate_scene(scene)
            return r.message

        # ── Clima ───────────────────────────────────────────────────
        if intent == "set_temperature":
            temp = float(match.group(2)) if match else 22.0
            r = self.ha.set_temperature(self.default_ac, temp)
            return r.message

        if intent == "ac_on":
            r = self.ha.set_hvac_mode(self.default_ac, "cool")
            return r.message

        if intent == "ac_off":
            r = self.ha.set_hvac_mode(self.default_ac, "off")
            return r.message

        if intent == "ac_cool":
            r = self.ha.set_hvac_mode(self.default_ac, "cool")
            return r.message

        if intent == "ac_heat":
            r = self.ha.set_hvac_mode(self.default_ac, "heat")
            return r.message

        # ── Spotify ─────────────────────────────────────────────────
        if intent == "spotify_auth":
            self.ui_callback("🔐 Abrindo autenticação do Spotify no navegador...")
            ok = self.spotify.authenticate()
            return "Spotify autenticado com sucesso! ✅" if ok else "Falha na autenticação."

        if intent == "spotify_pause":
            r = self.spotify.pause()
            return "⏸ Música pausada." if r else r.message

        if intent == "spotify_play":
            r = self.spotify.play()
            return "▶ Reprodução retomada." if r else r.message

        if intent == "spotify_next":
            r = self.spotify.next_track()
            return "⏭ Próxima faixa." if r else r.message

        if intent == "spotify_prev":
            r = self.spotify.previous_track()
            return "⏮ Faixa anterior." if r else r.message

        if intent == "spotify_vol_up":
            self._vol_current = min(100, self._vol_current + self.VOL_STEP)
            r = self.spotify.set_volume(self._vol_current)
            return f"🔊 Volume: {self._vol_current}%"

        if intent == "spotify_vol_down":
            self._vol_current = max(0, self._vol_current - self.VOL_STEP)
            r = self.spotify.set_volume(self._vol_current)
            return f"🔉 Volume: {self._vol_current}%"

        if intent == "spotify_vol_set":
            vol = int(match.group(1)) if match else 50
            self._vol_current = vol
            r = self.spotify.set_volume(vol)
            return f"🔊 Volume definido: {vol}%"

        if intent == "spotify_now":
            r = self.spotify.currently_playing()
            return r.message

        if intent == "spotify_shuffle_on":
            self.spotify.shuffle(True)
            return "🔀 Shuffle ativado."

        if intent == "spotify_shuffle_off":
            self.spotify.shuffle(False)
            return "➡️ Shuffle desativado."

        if intent in ("spotify_play_query", "spotify_play_artist"):
            query = self._extract_music_query(text)
            if not query:
                return "Não entendi o que tocar. Tente: 'Toca AC/DC no Spotify'."
            r = self.spotify.play_mood(query)
            return r.message

        # ── Status ───────────────────────────────────────────────────
        if intent == "home_status":
            return self._build_home_status()

        if intent == "list_lights":
            lights = self.ha.get_lights()
            if not lights:
                return "Nenhuma luz encontrada no Home Assistant."
            lines = [f"- {l.friendly_name}: {l.state}" for l in lights]
            return "Luzes:\n" + "\n".join(lines)

        return f"Comando não reconhecido: {intent}"

    # ------------------------------------------------------------------
    # Extratores de entidades
    # ------------------------------------------------------------------

    _ROOM_MAP = {
        "sala":      "light.sala",
        "quarto":    "light.quarto",
        "cozinha":   "light.cozinha",
        "banheiro":  "light.banheiro",
        "escritório":"light.escritorio",
        "varanda":   "light.varanda",
        "garagem":   "light.garagem",
        "garage":    "light.garagem",
    }

    _SCENE_MAP = {
        "filme": "filme",  "cinema": "filme",
        "relaxar": "relaxar", "relax": "relaxar",
        "jantar": "jantar",
        "leitura": "leitura",
        "trabalho": "trabalho", "foco": "trabalho",
        "festa": "festa",
    }

    def _extract_room_light(self, text: str) -> str | None:
        for word, entity in self._ROOM_MAP.items():
            if word in text.lower():
                return entity
        return None

    def _extract_scene(self, text: str) -> str:
        lower = text.lower()
        for word, scene in self._SCENE_MAP.items():
            if word in lower:
                return scene
        # Pega última palavra como nome de cena
        words = lower.split()
        return words[-1] if words else "padrao"

    def _extract_music_query(self, text: str) -> str:
        """Extrai o nome da música/artista/playlist do comando."""
        # Remove prefixos comuns
        cleaned = re.sub(
            r"^(nexus[,\s]+)?(toca?|reproduz|coloca?|bota?|play)\s+",
            "", text, flags=re.I,
        ).strip()
        cleaned = re.sub(r"\s+(no\s+)?spotify$", "", cleaned, flags=re.I).strip()
        return cleaned

    def _build_home_status(self) -> str:
        """Resumo rápido do estado da casa."""
        lines = ["**Status da casa:**\n"]

        lights = self.ha.get_lights()
        on = [l for l in lights if l.state == "on"]
        off = [l for l in lights if l.state == "off"]
        lines.append(f"💡 Luzes: {len(on)} ligadas, {len(off)} apagadas")
        for l in on:
            lines.append(f"   ▸ {l.friendly_name}")

        now = self.spotify.currently_playing()
        lines.append(f"\n🎵 {now.message}")

        return "\n".join(lines)
