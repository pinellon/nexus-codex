"""Testes do módulo app/agent — rodar com:  pytest tests/test_agent.py -v"""
from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from app.agent.agent_commands import extract_task, is_agent_command
from app.agent.research_agent import _summarize_result, _tool_label
from app.agent.tools import save_to_obsidian, scrape_page, web_search


# ---------------------------------------------------------------------------
# is_agent_command
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "Nexus, pesquisa Python async e salva no Obsidian",
    "pesquise os melhores livros de IA e salve no Obsidian",
    "busca tutoriais de FastAPI e salva",
    "modo agente: encontra artigos sobre LLMs",
    "agente pesquisa sobre rust lang",
])
def test_is_agent_command_true(text):
    assert is_agent_command(text) is True


@pytest.mark.parametrize("text", [
    "Nexus, abrir Chrome",
    "status do PC",
    "qual a hora?",
    "rode o código",
])
def test_is_agent_command_false(text):
    assert is_agent_command(text) is False


# ---------------------------------------------------------------------------
# extract_task
# ---------------------------------------------------------------------------

def test_extract_task_strips_wake_word():
    result = extract_task("Nexus, pesquisa Python e salva no Obsidian")
    assert result == "pesquisa Python e salva no Obsidian"


def test_extract_task_no_wake_word():
    result = extract_task("pesquisa Python e salva")
    assert result == "pesquisa Python e salva"


# ---------------------------------------------------------------------------
# _tool_label
# ---------------------------------------------------------------------------

def test_tool_label_search():
    label = _tool_label("web_search", {"query": "Python 2025"})
    assert "Python 2025" in label
    assert "🔍" in label


def test_tool_label_scrape():
    label = _tool_label("scrape_page", {"url": "https://example.com/article"})
    assert "📄" in label
    assert "example.com" in label


def test_tool_label_save():
    label = _tool_label("save_to_obsidian", {"title": "Minha Nota"})
    assert "💾" in label
    assert "Minha Nota" in label


# ---------------------------------------------------------------------------
# _summarize_result
# ---------------------------------------------------------------------------

def test_summarize_search_result():
    result = {"results": [{"title": "A"}, {"title": "B"}]}
    summary = _summarize_result("web_search", result)
    assert "2" in summary


def test_summarize_save_success():
    result = {"saved": True, "filename": "2025-01-01 Teste.md"}
    summary = _summarize_result("save_to_obsidian", result)
    assert "✅" in summary
    assert "Teste" in summary


def test_summarize_save_error():
    result = {"saved": False, "error": "Permissão negada"}
    summary = _summarize_result("save_to_obsidian", result)
    assert "⚠️" in summary


# ---------------------------------------------------------------------------
# ResearchAgent — mock da API OpenAI
# ---------------------------------------------------------------------------

def _make_settings(tmp_path):
    return SimpleNamespace(
        openai_api_key="sk-test",
        obsidian_vault_path=str(tmp_path),
        agent_model="gpt-4o-mini",
    )


def _mock_openai_done(content="Tarefa concluída com sucesso."):
    """Simula resposta do modelo sem tool calls (tarefa finalizada)."""
    msg = MagicMock()
    msg.tool_calls = []
    msg.content = content
    msg.model_dump.return_value = {"role": "assistant", "content": content}

    choice = MagicMock()
    choice.message = msg

    response = MagicMock()
    response.choices = [choice]
    return response


def _mock_openai_tool_then_done(tool_name, tool_args, final_content="Feito!"):
    """Simula: 1ª chamada usa ferramenta, 2ª finaliza."""
    # Primeira resposta: tool call
    tc = MagicMock()
    tc.id = "call_001"
    tc.function.name = tool_name
    tc.function.arguments = json.dumps(tool_args)

    msg1 = MagicMock()
    msg1.tool_calls = [tc]
    msg1.content = None
    msg1.model_dump.return_value = {
        "role": "assistant",
        "tool_calls": [{"id": "call_001", "function": {"name": tool_name, "arguments": json.dumps(tool_args)}}],
    }

    choice1 = MagicMock()
    choice1.message = msg1

    resp1 = MagicMock()
    resp1.choices = [choice1]

    # Segunda resposta: finaliza
    resp2 = _mock_openai_done(final_content)

    return [resp1, resp2]


def test_agent_run_done_immediately(tmp_path):
    from app.agent.research_agent import ResearchAgent

    settings = _make_settings(tmp_path)
    agent = ResearchAgent(settings)

    events = []

    with patch.object(agent.client.chat.completions, "create",
                      return_value=_mock_openai_done("Pesquisa concluída!")):
        result = agent.run("pesquisa algo", on_event=lambda e: events.append(e))

    assert "Pesquisa concluída!" in result
    kinds = [e.kind for e in events]
    assert "thinking" in kinds
    assert "done" in kinds


def test_agent_run_with_web_search(tmp_path):
    from app.agent.research_agent import ResearchAgent

    settings = _make_settings(tmp_path)
    agent = ResearchAgent(settings)

    events = []
    responses = _mock_openai_tool_then_done(
        "web_search", {"query": "Python 2025"}, "Pesquisa salva!"
    )

    fake_search_result = {
        "query": "Python 2025",
        "results": [{"title": "Python News", "snippet": "...", "url": "https://python.org"}],
    }

    with patch.object(agent.client.chat.completions, "create", side_effect=responses):
        with patch("app.agent.tools.web_search", return_value=fake_search_result):
            result = agent.run("pesquisa Python 2025", on_event=lambda e: events.append(e))

    assert "Pesquisa salva!" in result
    tool_events = [e for e in events if e.kind == "tool_call"]
    assert any("web_search" in e.data.get("tool", "") for e in tool_events)


def test_agent_stop(tmp_path):
    """Agente deve parar quando stop() é chamado entre iterações."""
    from app.agent.research_agent import ResearchAgent

    settings = _make_settings(tmp_path)
    agent = ResearchAgent(settings)
    agent.stop()  # Para antes mesmo de começar

    result = agent.run("pesquisa algo", on_event=lambda e: None)
    assert "cancelada" in result.lower() or "interrompido" in result.lower()


def test_save_to_obsidian_requires_real_vault(tmp_path):
    result = save_to_obsidian("Teste", "Conteudo", vault_path=str(tmp_path))

    assert result["saved"] is False
    assert "vault" in result["error"].lower()
