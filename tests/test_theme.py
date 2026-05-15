from __future__ import annotations

from types import SimpleNamespace

import theme


class DummySmartRouter:
    def __init__(self, domain: str):
        self.domain = domain

    def route(self, text: str):
        return SimpleNamespace(domain=self.domain, intent=self.domain, args={"intent": "status"}, raw=text, normalized=text)


def test_smart_home_returns_final_message(monkeypatch):
    monkeypatch.setattr(theme, "_command_router", DummySmartRouter("home"))
    monkeypatch.setattr(theme, "_get_home_handler", lambda: SimpleNamespace(run_and_wait=lambda text: "status final da casa"))

    result = theme._processar_recursos_inteligentes("status da casa")

    assert result == "status final da casa"


def test_smart_vision_returns_final_message(monkeypatch):
    monkeypatch.setattr(theme, "_command_router", DummySmartRouter("vision"))
    monkeypatch.setattr(theme, "_get_vision_handler", lambda: SimpleNamespace(run_and_wait=lambda text: "leitura final da tela"))

    result = theme._processar_recursos_inteligentes("descreve a tela")

    assert result == "leitura final da tela"
