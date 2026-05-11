from __future__ import annotations

import logging
from types import SimpleNamespace

from app.chat.chat_engine import ChatEngine
from app.chat.command_router import ChatCommandRouter
from app.chat.text_chat import TextChat


class DummyRouter:
    def route(self, text: str):
        return SimpleNamespace(
            intent="ask_ai",
            label="assistant:ask_ai",
            args={"text": text},
        )

    def describe(self, text: str) -> str:
        return f"assistant:ask_ai {{'text': '{text}'}}"

    def is_exit_command(self, text: str, command=None) -> bool:
        return text.strip().lower() == "sair"


class DummySpeaker:
    def __init__(self):
        self.messages = []

    def speak(self, text: str):
        self.messages.append(text)


class DummyHandler:
    def __init__(self, response: str = "ok"):
        self.response = response
        self.calls = []

    def handle_message(self, text: str, command=None, confirm_callback=None) -> str:
        self.calls.append((text, command))
        return self.response


class DummyEngine:
    def process_input(self, text, speak=False, confirm_callback=None):
        return {"response": f"eco:{text}"}


def test_chat_command_router_accepts_wake_word_exit():
    router = ChatCommandRouter()
    assert router.is_exit_command("nexus sair") is True
    assert router.is_exit_command("nexus parar") is True


def test_chat_engine_short_circuits_exit_without_speaking():
    speaker = DummySpeaker()
    handler = DummyHandler(response="nao deveria acontecer")
    engine = ChatEngine(
        settings={},
        logger=logging.getLogger("test.chat.engine"),
        router=DummyRouter(),
        speaker=speaker,
        handler=handler,
    )

    result = engine.process_input("sair", speak=True)

    assert result["should_exit"] is True
    assert result["response"] == "Encerrando chat."
    assert handler.calls == []
    assert speaker.messages == []


def test_text_chat_uses_engine_response():
    chat = TextChat(settings={}, engine=DummyEngine())

    assert chat.handle_input("teste") == "eco:teste"
