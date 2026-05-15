from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.vision.capture import CapturedImage
from app.web.server import _module_cards, create_app


@pytest.fixture(autouse=True)
def clear_local_api_token_env(monkeypatch):
    monkeypatch.delenv("NEXUS_LOCAL_API_TOKEN", raising=False)


class DummyEngine:
    def __init__(self, response: str = "ok", confirmation_required: bool = False):
        self.response = response
        self.confirmation_required = confirmation_required
        self.calls: list[tuple[str, bool]] = []

    def process_input(self, text: str, speak: bool = False, confirm_callback=None):
        asked_confirmation = False
        if self.confirmation_required and confirm_callback is not None:
            asked_confirmation = True
            confirm_callback("Confirmar acao de risco?")
        self.calls.append((text, asked_confirmation))
        return {
            "command": {"intent": "assistant"},
            "understood": f"assistant:{text}",
            "response": self.response,
            "should_exit": False,
        }


class DummyMindRuntime:
    def __init__(self):
        self.calls: list[tuple[str, object]] = []

    def get_state(self):
        self.calls.append(("get_state", None))
        return {"running": False, "settings": {"mode": "supervisionado"}}

    def update_settings(self, settings):
        self.calls.append(("update_settings", settings))
        return {"running": False, "settings": settings}

    def start(self):
        self.calls.append(("start", None))
        return {"running": True}

    def stop(self):
        self.calls.append(("stop", None))
        return {"running": False}

    def run_manual_cycle(self):
        self.calls.append(("cycle", None))
        return {"cycle_active": True}

    def rollback(self):
        self.calls.append(("rollback", None))
        return {"rolled_back": True}

    def refresh_proof(self):
        self.calls.append(("proof", None))
        return {"proof": {"verifications": []}}

    def clear_restart_flag(self):
        self.calls.append(("clear_restart", None))
        return {"restart": {"pending_reason": None}}


class DummyScreenCapture:
    def capture(self):
        return CapturedImage(base64_data="screen-b64", width=1280, height=720, source="screen")


class DummyCameraCapture:
    def __init__(self, camera_index: int = 0):
        self.camera_index = camera_index

    def list_cameras(self):
        return [0, 2]

    def capture(self):
        return CapturedImage(base64_data=f"camera-{self.camera_index}", width=640, height=480, source="camera")


class DummyVisionAnalyzer:
    def __init__(self, settings, logger):
        self.settings = settings
        self.logger = logger

    def describe(self, image):
        return f"describe:{image.source}"

    def read_text(self, image):
        return f"ocr:{image.source}"

    def analyze_code(self, image):
        return f"code:{image.source}"

    def find_objects(self, image):
        return f"objects:{image.source}"

    def watch_camera(self, image):
        return f"watch:{image.source}"

    def custom(self, image, question):
        return f"ask:{image.source}:{question}"


class DummyFinanceService:
    def __init__(self):
        self.calls: list[tuple[str, object]] = []

    def summary(self):
        self.calls.append(("summary", None))
        return {"current_balance": 1200.0, "month_income": 2100.0, "month_expense": 900.0}

    def list_transactions(self):
        self.calls.append(("transactions", None))
        return [{"id": "txn_1", "title": "Lanche", "amount": 35.0}]

    def add_transaction(self, payload):
        self.calls.append(("add_transaction", payload))
        return {"id": "txn_2", **payload}

    def list_bills(self):
        self.calls.append(("bills", None))
        return [{"id": "bill_1", "title": "Internet", "amount": 120.0, "paid": False}]

    def add_bill(self, payload):
        self.calls.append(("add_bill", payload))
        return {"id": "bill_2", **payload}

    def pay_bill(self, bill_id):
        self.calls.append(("pay_bill", bill_id))
        return {"id": bill_id, "paid": True}

    def list_goals(self):
        self.calls.append(("goals", None))
        return [{"id": "goal_1", "title": "Reserva", "target_amount": 500.0}]

    def add_goal(self, payload):
        self.calls.append(("add_goal", payload))
        return {"id": "goal_2", **payload}

    def monthly_chart(self):
        self.calls.append(("chart", None))
        return {"points": [{"date": "2026-05-01", "balance": 900.0}]}

    def categories(self):
        self.calls.append(("categories", None))
        return {"categories": [{"category": "Alimentacao", "amount": 35.0}]}


class DummyVoiceResult:
    def __init__(self, text: str = "teste de voz", backend: str = "sounddevice-google", confidence: float | None = 0.91):
        self.text = text
        self.backend = backend
        self.confidence = confidence


class DummyTTSItem:
    def __init__(self, path):
        self.key = "audio_1"
        self.path = path
        self.content_type = "audio/mpeg"


class DummyTTSService:
    def __init__(self, settings):
        self.settings = settings

    def synthesize_to_file(self, *_args, **_kwargs):
        from pathlib import Path

        path = Path("data/audio_cache/test-audio.mp3")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"audio")
        return DummyTTSItem(path)

    def synthesize_chunks(self, *_args, **_kwargs):
        return [{"id": "audio_1", "text": "Pronto.", "audio_url": "/api/voice/cache/test-audio.mp3", "content_type": "audio/mpeg", "order": "1"}]


def test_dashboard_endpoint_returns_health_and_modules(monkeypatch):
    monkeypatch.setattr(
        "app.web.server.build_dashboard_payload",
        lambda log_limit=40, event_limit=20: {
            "project_root": "C:/nexus",
            "health": {"score": 98, "status": "forte", "found": [], "missing": [], "warnings": []},
            "modules": [{"id": "chat", "title": "Chat Core", "description": "x", "status": "online", "tone": "cyan"}],
            "logs": ["linha 1"],
            "events": [],
            "settings": {"wake_word": "nexus"},
            "runtime": {"cpu": 10, "ram": 20, "disk": 30, "updated_at": "2026-05-13T00:00:00Z"},
        },
    )
    client = TestClient(create_app())

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["health"]["score"] == 98
    assert payload["modules"][0]["id"] == "chat"


def test_runtime_status_endpoint_returns_metrics():
    client = TestClient(create_app())

    response = client.get("/api/runtime/status")

    assert response.status_code == 200
    payload = response.json()
    assert {"cpu", "ram", "disk", "updated_at"} <= payload.keys()


def test_voice_devices_endpoint_lists_backend_snapshot(monkeypatch):
    monkeypatch.setattr(
        "app.web.server._voice_devices_snapshot",
        lambda: {
            "ok": True,
            "default_input_index": 1,
            "default_output_index": 4,
            "inputs": [{"index": 1, "name": "fone Microfone (Realtek(R) Audio)"}],
            "outputs": [{"index": 4, "name": "Realtek HD Audio 2nd output (Realtek(R) Audio)"}],
        },
    )
    client = TestClient(create_app())

    response = client.get("/api/voice/devices")

    assert response.status_code == 200
    assert response.json()["default_input_index"] == 1
    assert response.json()["inputs"][0]["name"].startswith("fone Microfone")


def test_voice_listen_once_endpoint_uses_backend(monkeypatch):
    monkeypatch.setattr("app.web.server.settings_manager.load", lambda: {"voice_backend": "sounddevice", "voice_input_device": "1"})
    monkeypatch.setattr("app.web.server.clear_backend_cache", lambda: None)
    monkeypatch.setattr("app.web.server.listen_once", lambda **_kwargs: DummyVoiceResult())
    client = TestClient(create_app())

    response = client.post("/api/voice/listen-once", json={"timeout": 4, "phrase_time_limit": 7})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["text"] == "teste de voz"
    assert payload["backend"] == "sounddevice-google"
    assert payload["device_index"] == "1"


def test_voice_profiles_endpoint_returns_profiles():
    client = TestClient(create_app())

    response = client.get("/api/voice/profiles")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert any(item["id"] == "jarvis" for item in payload["profiles"])


def test_voice_chunks_endpoint_uses_tts_service(monkeypatch):
    monkeypatch.setattr("app.web.server.TTSService", DummyTTSService)
    client = TestClient(create_app())

    response = client.post("/api/voice/chunks", json={"text": "Pronto.", "provider": "edge", "profile": "jarvis"})

    assert response.status_code == 200
    assert response.json()["chunks"][0]["audio_url"].endswith("test-audio.mp3")


def test_voice_speak_endpoint_returns_audio(monkeypatch):
    monkeypatch.setattr("app.web.server.TTSService", DummyTTSService)
    client = TestClient(create_app())

    response = client.post("/api/voice/speak", json={"text": "Pronto.", "provider": "edge", "profile": "jarvis"})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("audio/mpeg")
    assert response.content == b"audio"


def test_automation_catalog_endpoint_lists_sections():
    client = TestClient(create_app())

    response = client.get("/api/automation/catalog")

    assert response.status_code == 200
    payload = response.json()
    assert payload["sections"]
    assert payload["sections"][0]["actions"]


def test_automation_catalog_endpoint_filters_results():
    client = TestClient(create_app())

    response = client.get("/api/automation/catalog", params={"query": "spotify"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["sections"]
    assert all(
        any("spotify" in action["label"].lower() or "spotify" in action["command"].lower() for action in section["actions"])
        or "spotify" in section["title"].lower()
        for section in payload["sections"]
    )


def test_module_cards_reflect_configuration_state(monkeypatch, tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "mind_settings.json").write_text(
        json.dumps({"active": False, "mode": "supervisionado"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("app.web.server.BASE_DIR", tmp_path)
    monkeypatch.setattr(
        "app.web.server.settings_manager.load",
        lambda: {
            "openai_api_key": "test-key",
            "local_api_token": "",
            "voice_engine": "pyttsx3",
            "obsidian_enabled": True,
            "obsidian_vault_path": "",
            "spotify_client_id": "",
            "ha_token": "",
            "voice_confirm_commands": True,
            "mind_allow_autonomous": False,
        },
    )

    modules = {module["id"]: module for module in _module_cards()}

    assert modules["api"]["status"] == "guarded"
    assert modules["chat"]["status"] == "online"
    assert modules["memory"]["status"] == "offline"
    assert modules["mind"]["status"] == "paused"
    assert modules["coder"]["configured"] is True


def test_cors_preflight_allows_known_local_origin():
    client = TestClient(create_app())

    response = client.options(
        "/api/chat",
        headers={
            "Origin": "http://127.0.0.1:5173",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5173"
    assert response.headers.get("access-control-allow-credentials") != "true"


def test_cors_preflight_rejects_unknown_origin():
    client = TestClient(create_app())

    response = client.options(
        "/api/chat",
        headers={
            "Origin": "https://evil.example",
            "Access-Control-Request-Method": "POST",
        },
    )

    assert response.status_code in {200, 400}
    assert "access-control-allow-origin" not in response.headers


def test_mind_state_endpoint_uses_runtime(monkeypatch):
    runtime = DummyMindRuntime()
    monkeypatch.setattr("app.web.server._get_mind_runtime", lambda: runtime)
    client = TestClient(create_app())

    response = client.get("/api/mind/state")

    assert response.status_code == 200
    assert response.json()["settings"]["mode"] == "supervisionado"
    assert runtime.calls == [("get_state", None)]


def test_mind_settings_endpoint_updates_runtime(monkeypatch):
    runtime = DummyMindRuntime()
    monkeypatch.setattr("app.web.server._get_mind_runtime", lambda: runtime)
    client = TestClient(create_app())

    response = client.put("/api/mind/settings", json={"settings": {"mode": "autônomo", "interval": 2}})

    assert response.status_code == 200
    assert runtime.calls == [("update_settings", {"mode": "autônomo", "interval": 2})]


def test_mind_action_endpoints_delegate_to_runtime(monkeypatch):
    runtime = DummyMindRuntime()
    monkeypatch.setattr("app.web.server._get_mind_runtime", lambda: runtime)
    client = TestClient(create_app())

    assert client.post("/api/mind/start").status_code == 200
    assert client.post("/api/mind/stop").status_code == 200
    assert client.post("/api/mind/cycle").status_code == 200
    assert client.post("/api/mind/rollback").status_code == 200
    assert client.post("/api/mind/proof").status_code == 200
    assert client.post("/api/mind/restart/clear").status_code == 200

    assert runtime.calls == [
        ("start", None),
        ("stop", None),
        ("cycle", None),
        ("rollback", None),
        ("proof", None),
        ("clear_restart", None),
    ]


def test_vision_status_endpoint_lists_cameras(monkeypatch):
    monkeypatch.setattr("app.web.server.CameraCapture", DummyCameraCapture)
    monkeypatch.setattr("app.web.server.settings_manager.load", lambda: {"camera_index": 2})
    client = TestClient(create_app())

    response = client.get("/api/vision/status")

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "camera_indices": [0, 2],
        "default_camera_index": 2,
    }


def test_vision_screen_capture_returns_preview(monkeypatch):
    monkeypatch.setattr("app.web.server.ScreenCapture", DummyScreenCapture)
    client = TestClient(create_app())

    response = client.post("/api/vision/screen/capture")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["action"] == "screen_capture"
    assert payload["image"]["base64_data"] == "screen-b64"
    assert payload["image"]["source"] == "screen"


def test_vision_screen_action_uses_analyzer(monkeypatch):
    monkeypatch.setattr("app.web.server.ScreenCapture", DummyScreenCapture)
    monkeypatch.setattr("app.web.server.VisionAnalyzer", DummyVisionAnalyzer)
    monkeypatch.setattr("app.web.server.settings_manager.load", lambda: {"openai_api_key": "test"})
    client = TestClient(create_app())

    response = client.post("/api/vision/screen/ask", json={"question": "o que voce ve?"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["action"] == "ask"
    assert payload["response"] == "ask:screen:o que voce ve?"
    assert payload["image"]["source"] == "screen"


def test_vision_camera_action_uses_selected_camera(monkeypatch):
    monkeypatch.setattr("app.web.server.CameraCapture", DummyCameraCapture)
    monkeypatch.setattr("app.web.server.VisionAnalyzer", DummyVisionAnalyzer)
    monkeypatch.setattr("app.web.server.settings_manager.load", lambda: {"openai_api_key": "test"})
    client = TestClient(create_app())

    response = client.post("/api/vision/camera/describe", json={"camera_index": 2})

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["action"] == "describe"
    assert payload["response"] == "watch:camera"
    assert payload["image"]["base64_data"] == "camera-2"


def test_chat_endpoint_uses_engine(monkeypatch):
    engine = DummyEngine(response="Tudo certo.")
    monkeypatch.setattr("app.web.server.build_chat_engine", lambda: engine)
    client = TestClient(create_app())

    response = client.post("/api/chat", json={"text": "oi nexus"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["response"] == "Tudo certo."
    assert payload["confirmation_required"] is False
    assert engine.calls == [("oi nexus", False)]


def test_chat_endpoint_exposes_confirmation_prompt(monkeypatch):
    engine = DummyEngine(response="Acao cancelada.", confirmation_required=True)
    monkeypatch.setattr("app.web.server.build_chat_engine", lambda: engine)
    client = TestClient(create_app())

    response = client.post("/api/chat", json={"text": "desligar pc"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["confirmation_required"] is True
    assert payload["confirmation_message"] == "Confirmar acao de risco?"
    assert payload["response"] == "Confirmar acao de risco?"


def test_chat_endpoint_requires_token_when_configured(monkeypatch):
    engine = DummyEngine(response="Tudo certo.")
    monkeypatch.setattr("app.web.server.build_chat_engine", lambda: engine)
    monkeypatch.setattr("app.web.server.settings_manager.load", lambda: {"local_api_token": "segredo"})
    client = TestClient(create_app())

    response = client.post("/api/chat", json={"text": "oi nexus"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Missing or invalid X-NEXUS-TOKEN header."
    assert engine.calls == []


def test_chat_endpoint_accepts_valid_token_when_configured(monkeypatch):
    engine = DummyEngine(response="Tudo certo.")
    monkeypatch.setattr("app.web.server.build_chat_engine", lambda: engine)
    monkeypatch.setattr("app.web.server.settings_manager.load", lambda: {"local_api_token": "segredo"})
    client = TestClient(create_app())

    response = client.post(
        "/api/chat",
        json={"text": "oi nexus"},
        headers={"X-NEXUS-TOKEN": "segredo"},
    )

    assert response.status_code == 200
    assert response.json()["response"] == "Tudo certo."
    assert engine.calls == [("oi nexus", False)]


def test_finance_get_endpoints_return_service_payload(monkeypatch):
    service = DummyFinanceService()
    monkeypatch.setattr("app.web.server._get_finance_service", lambda: service)
    client = TestClient(create_app())

    assert client.get("/api/finance/summary").json()["current_balance"] == 1200.0
    assert client.get("/api/finance/transactions").json()["items"][0]["title"] == "Lanche"
    assert client.get("/api/finance/bills").json()["items"][0]["title"] == "Internet"
    assert client.get("/api/finance/goals").json()["items"][0]["title"] == "Reserva"
    assert client.get("/api/finance/chart/monthly").json()["points"][0]["balance"] == 900.0
    assert client.get("/api/finance/categories").json()["categories"][0]["category"] == "Alimentacao"


def test_finance_post_endpoints_require_token_and_delegate(monkeypatch):
    service = DummyFinanceService()
    monkeypatch.setattr("app.web.server._get_finance_service", lambda: service)
    monkeypatch.setattr("app.web.server.settings_manager.load", lambda: {"local_api_token": "segredo"})
    client = TestClient(create_app())

    assert client.post("/api/finance/transactions", json={"title": "Cafe", "amount": 12}).status_code == 401

    create_response = client.post(
        "/api/finance/transactions",
        json={"title": "Cafe", "amount": 12, "type": "expense"},
        headers={"X-NEXUS-TOKEN": "segredo"},
    )
    pay_response = client.put(
        "/api/finance/bills/bill_2/pay",
        headers={"X-NEXUS-TOKEN": "segredo"},
    )

    assert create_response.status_code == 200
    assert create_response.json()["item"]["title"] == "Cafe"
    assert pay_response.status_code == 200
    assert pay_response.json()["item"]["paid"] is True
