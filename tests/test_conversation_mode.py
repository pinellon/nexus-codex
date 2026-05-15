from app.chat.conversation_mode import ConversationModeRuntime
from app.chat.session_context import SessionContext


def test_session_context_tracks_messages_and_topic():
    context = SessionContext(session_id="sessao-1")
    context.add_user_message("me ajuda a estudar redes")
    context.add_assistant_message("Claro. Quer resumo ou perguntas?")
    context.set_topic("redes")
    context.set_goal("aprender redes")

    payload = context.to_dict()

    assert payload["session_id"] == "sessao-1"
    assert payload["current_topic"] == "redes"
    assert payload["current_goal"] == "aprender redes"
    assert payload["last_user_messages"][-1] == "me ajuda a estudar redes"
    assert "Topico atual: redes" in context.get_context_text()


def test_conversation_mode_rejects_empty_text():
    runtime = ConversationModeRuntime()

    result = runtime.process_message("", session_id="sessao-vazia")

    assert result.ok is False
    assert result.state == "error"
    assert "Diga ou escreva algo" in result.response


def test_conversation_mode_generates_contextual_reply(monkeypatch):
    monkeypatch.setattr("app.chat.conversation_mode.search", lambda *_args, **_kwargs: [])
    monkeypatch.setattr("app.chat.conversation_mode.conversar", lambda *_args, **_kwargs: ("Claro. Vamos comecar pelo basico de nuvem.", []))

    runtime = ConversationModeRuntime()
    result = runtime.process_message("me ajuda a estudar computacao em nuvem", session_id="sessao-estudo", study_mode=True)

    assert result.ok is True
    assert result.intent == "explain"
    assert result.topic == "computacao em nuvem"
    assert result.state == "ready"
    assert "basico de nuvem" in result.response


def test_conversation_mode_reset_clears_session(monkeypatch):
    monkeypatch.setattr("app.chat.conversation_mode.search", lambda *_args, **_kwargs: [])
    monkeypatch.setattr("app.chat.conversation_mode.conversar", lambda *_args, **_kwargs: ("Resumo curto.", []))
    runtime = ConversationModeRuntime()
    runtime.process_message("faz um resumo sobre redes", session_id="sessao-reset", study_mode=True)

    assert runtime.reset("sessao-reset") is True

    state = runtime.get_state()
    assert state["state"] == "idle"
    assert state["session"]["current_topic"] == ""
    assert state["session"]["last_user_messages"] == []


def test_conversation_mode_save_note_calls_obsidian(monkeypatch, tmp_path):
    saved_path = tmp_path / "Resumo.md"
    monkeypatch.setattr("app.chat.conversation_mode.search", lambda *_args, **_kwargs: [])
    monkeypatch.setattr("app.chat.conversation_mode.conversar", lambda *_args, **_kwargs: ("TCP confirma entrega; UDP prioriza velocidade.", []))
    monkeypatch.setattr("app.chat.conversation_mode.save_note", lambda **_kwargs: saved_path)

    runtime = ConversationModeRuntime()
    runtime.process_message("me explica TCP e UDP", session_id="sessao-save", study_mode=True)
    result = runtime.process_message("salva isso", session_id="sessao-save", study_mode=True)

    assert result.ok is True
    assert result.saved_note_path == str(saved_path)
    assert "Salvei no Obsidian" in result.response
