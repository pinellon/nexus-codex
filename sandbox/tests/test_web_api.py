from __future__ import annotations

from fastapi.testclient import TestClient

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
        },
    )
    client = TestClient(create_app())

    response = client.get("/api/dashboard")

    assert response.status_code == 200
    payload = response.json()
    assert payload["health"]["score"] == 98
    assert payload["modules"][0]["id"] == "chat"


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
