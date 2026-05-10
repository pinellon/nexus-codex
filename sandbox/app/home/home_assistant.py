"""HomeAssistantClient — integração com o Home Assistant via REST API.

Controla qualquer entidade do HA: luzes, switches, termostatos, cenas,
scripts, persianas, travas, TV, etc.

Referência: https://developers.home-assistant.io/docs/api/rest/
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import requests

log = logging.getLogger("nexus.home.ha")


def _setting(settings, key: str, default: str = ""):
    if isinstance(settings, dict):
        return settings.get(key, default)
    return getattr(settings, key, default)


# ---------------------------------------------------------------------------
# Tipos de retorno
# ---------------------------------------------------------------------------

@dataclass
class HAState:
    """Estado de uma entidade do Home Assistant."""
    entity_id: str
    state: str
    friendly_name: str
    attributes: dict

    @classmethod
    def from_json(cls, data: dict) -> "HAState":
        attrs = data.get("attributes", {})
        return cls(
            entity_id=data.get("entity_id", ""),
            state=data.get("state", "unknown"),
            friendly_name=attrs.get("friendly_name", data.get("entity_id", "")),
            attributes=attrs,
        )

    def __str__(self) -> str:
        return f"{self.friendly_name}: {self.state}"


@dataclass
class HAResult:
    """Resultado de um comando enviado ao Home Assistant."""
    success: bool
    message: str
    entity_id: str = ""
    data: dict | None = None


# ---------------------------------------------------------------------------
# Cliente principal
# ---------------------------------------------------------------------------

class HomeAssistantClient:
    """Controla o Home Assistant via API REST."""

    def __init__(self, settings, logger: logging.Logger | None = None):
        """
        Args:
            settings: Objeto com:
                - ha_url (str)   — ex: "http://homeassistant.local:8123"
                - ha_token (str) — Long-Lived Access Token do HA
        """
        self.base_url = str(_setting(settings, "ha_url", "") or "").rstrip("/")
        self.token = str(_setting(settings, "ha_token", "") or "")
        self.log = logger or log
        self._session = requests.Session()
        self._session.headers.update({
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        })
        self._entity_cache: dict[str, HAState] = {}

    # ------------------------------------------------------------------
    # Diagnóstico
    # ------------------------------------------------------------------

    def is_connected(self) -> bool:
        """Verifica se o Home Assistant está acessível."""
        try:
            resp = self._session.get(f"{self.base_url}/api/", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Luzes
    # ------------------------------------------------------------------

    def light_on(self, entity_id: str, brightness: int | None = None,
                 color_temp: int | None = None, rgb: tuple | None = None) -> HAResult:
        """Liga uma luz com parâmetros opcionais."""
        data: dict[str, Any] = {"entity_id": entity_id}
        if brightness is not None:
            data["brightness_pct"] = max(1, min(100, brightness))
        if color_temp is not None:
            data["color_temp"] = color_temp
        if rgb is not None:
            data["rgb_color"] = list(rgb)
        return self._call_service("light", "turn_on", data, entity_id)

    def light_off(self, entity_id: str) -> HAResult:
        """Apaga uma luz."""
        return self._call_service("light", "turn_off", {"entity_id": entity_id}, entity_id)

    def light_toggle(self, entity_id: str) -> HAResult:
        """Alterna uma luz."""
        return self._call_service("light", "toggle", {"entity_id": entity_id}, entity_id)

    def set_brightness(self, entity_id: str, pct: int) -> HAResult:
        """Define o brilho de uma luz (0-100%)."""
        return self.light_on(entity_id, brightness=pct)

    def lights_all_off(self) -> HAResult:
        """Apaga todas as luzes da casa."""
        return self._call_service("light", "turn_off",
                                  {"entity_id": "all"}, "all")

    # ------------------------------------------------------------------
    # Switches / tomadas
    # ------------------------------------------------------------------

    def switch_on(self, entity_id: str) -> HAResult:
        return self._call_service("switch", "turn_on", {"entity_id": entity_id}, entity_id)

    def switch_off(self, entity_id: str) -> HAResult:
        return self._call_service("switch", "turn_off", {"entity_id": entity_id}, entity_id)

    def switch_toggle(self, entity_id: str) -> HAResult:
        return self._call_service("switch", "toggle", {"entity_id": entity_id}, entity_id)

    # ------------------------------------------------------------------
    # Cenas (scenes)
    # ------------------------------------------------------------------

    def activate_scene(self, scene_id: str) -> HAResult:
        """Ativa uma cena do Home Assistant."""
        if not scene_id.startswith("scene."):
            scene_id = f"scene.{scene_id}"
        return self._call_service("scene", "turn_on", {"entity_id": scene_id}, scene_id)

    # ------------------------------------------------------------------
    # Clima / termostato
    # ------------------------------------------------------------------

    def set_temperature(self, entity_id: str, temperature: float) -> HAResult:
        """Define a temperatura do termostato."""
        return self._call_service(
            "climate", "set_temperature",
            {"entity_id": entity_id, "temperature": temperature},
            entity_id,
        )

    def set_hvac_mode(self, entity_id: str, mode: str) -> HAResult:
        """Define o modo do ar-condicionado (heat, cool, off, auto, fan_only)."""
        return self._call_service(
            "climate", "set_hvac_mode",
            {"entity_id": entity_id, "hvac_mode": mode},
            entity_id,
        )

    # ------------------------------------------------------------------
    # Scripts
    # ------------------------------------------------------------------

    def run_script(self, script_id: str) -> HAResult:
        """Executa um script do Home Assistant."""
        if not script_id.startswith("script."):
            script_id = f"script.{script_id}"
        return self._call_service("script", "turn_on", {"entity_id": script_id}, script_id)

    # ------------------------------------------------------------------
    # Estados
    # ------------------------------------------------------------------

    def get_state(self, entity_id: str) -> HAState | None:
        """Retorna o estado atual de uma entidade."""
        try:
            resp = self._session.get(
                f"{self.base_url}/api/states/{entity_id}", timeout=5
            )
            if resp.status_code == 200:
                state = HAState.from_json(resp.json())
                self._entity_cache[entity_id] = state
                return state
            self.log.warning("Estado não encontrado: %s (%d)", entity_id, resp.status_code)
            return None
        except Exception as exc:
            self.log.error("Erro ao buscar estado: %s", exc)
            return None

    def list_entities(self, domain: str | None = None) -> list[HAState]:
        """Lista todas as entidades, filtrando por domínio opcional."""
        try:
            resp = self._session.get(f"{self.base_url}/api/states", timeout=10)
            if resp.status_code != 200:
                return []
            entities = [HAState.from_json(e) for e in resp.json()]
            if domain:
                entities = [e for e in entities if e.entity_id.startswith(f"{domain}.")]
            return entities
        except Exception as exc:
            self.log.error("Erro ao listar entidades: %s", exc)
            return []

    def get_lights(self) -> list[HAState]:
        return self.list_entities("light")

    def get_switches(self) -> list[HAState]:
        return self.list_entities("switch")

    def get_scenes(self) -> list[HAState]:
        return self.list_entities("scene")

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------

    def _call_service(
        self,
        domain: str,
        service: str,
        data: dict,
        entity_id: str = "",
    ) -> HAResult:
        url = f"{self.base_url}/api/services/{domain}/{service}"
        try:
            resp = self._session.post(url, json=data, timeout=8)
            if resp.status_code in (200, 201):
                friendly = entity_id.replace("_", " ").split(".")[-1].title()
                action_map = {
                    "turn_on": "ligado", "turn_off": "desligado",
                    "toggle": "alternado", "set_temperature": "temperatura definida",
                    "set_hvac_mode": "modo definido", "turn_on scene": "cena ativada",
                }
                action = action_map.get(service, service)
                msg = f"{friendly} {action} com sucesso."
                self.log.info("HA: %s/%s → %s", domain, service, msg)
                return HAResult(success=True, message=msg, entity_id=entity_id)
            else:
                msg = f"HA retornou {resp.status_code}: {resp.text[:200]}"
                self.log.warning(msg)
                return HAResult(success=False, message=msg, entity_id=entity_id)
        except requests.ConnectionError:
            msg = "Home Assistant não encontrado. Verifique a URL e a conexão."
            self.log.error(msg)
            return HAResult(success=False, message=msg, entity_id=entity_id)
        except Exception as exc:
            msg = f"Erro inesperado: {exc}"
            self.log.error(msg)
            return HAResult(success=False, message=msg, entity_id=entity_id)
