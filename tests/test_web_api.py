from __future__ import annotations

from fastapi.testclient import TestClient

from app.vision.capture import CapturedImage
from app.web.server import create_app


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
