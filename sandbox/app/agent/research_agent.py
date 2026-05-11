"""ResearchAgent — agente autônomo do NEXUS.

Fluxo:
  1. Recebe uma tarefa em linguagem natural (ex: "pesquisa Python async e salva no Obsidian").
  2. Chama o modelo OpenAI em loop com function calling.
  3. A cada iteração executa as ferramentas solicitadas (busca, scrape, salvar).
  4. Emite eventos de progresso via callback para a UI mostrar em tempo real.
  5. Para quando o modelo retorna uma resposta de texto sem chamar mais ferramentas
     (significa que a tarefa foi concluída).

Uso standalone:
    agent = ResearchAgent(settings)
    agent.run("pesquisa os melhores livros de Python 2025 e salva no Obsidian",
              on_event=print)
"""
from __future__ import annotations

import json
import logging
import threading
from dataclasses import dataclass, field
from typing import Any, Callable

from openai import OpenAI

from .tools import TOOL_SCHEMAS, dispatch

log = logging.getLogger("nexus.agent")

# Máximo de iterações do loop agentic para evitar loops infinitos
MAX_ITERATIONS = 12

SYSTEM_PROMPT = """Você é NEXUS, o assistente de IA pessoal do usuário, inspirado no JARVIS do Homem de Ferro.

Seu objetivo é executar tarefas de pesquisa de forma autônoma usando as ferramentas disponíveis.

Diretrizes:
- Pense passo a passo antes de agir.
- Use web_search para descobrir o que existe sobre o tema.
- Use scrape_page para ler o conteúdo completo das páginas mais relevantes.
- Consolide as informações em um resumo claro e bem estruturado em Markdown.
- Use save_to_obsidian para arquivar o resultado quando tiver informações suficientes.
- Responda sempre em português brasileiro, com tom direto e confiante.
- Quando a tarefa estiver concluída, confirme o que foi feito de forma sucinta.
- Nunca invente informações — baseie-se apenas no que as ferramentas retornaram.
"""


# ---------------------------------------------------------------------------
# Configuracao
# ---------------------------------------------------------------------------

def _setting(settings: Any, key: str, default: str = "") -> str:
    """Le configuracao em objeto dataclass/SimpleNamespace ou dict."""
    if isinstance(settings, dict):
        return str(settings.get(key, default) or default)
    return str(getattr(settings, key, default) or default)


# ---------------------------------------------------------------------------
# Tipos de eventos emitidos para a UI
# ---------------------------------------------------------------------------

@dataclass
class AgentEvent:
    """Evento emitido pelo agente durante a execução."""
    kind: str          # "thinking" | "tool_call" | "tool_result" | "done" | "error"
    message: str       # Texto exibido na UI
    data: dict = field(default_factory=dict)  # Dados extras (ex: resultado da ferramenta)


# ---------------------------------------------------------------------------
# ResearchAgent
# ---------------------------------------------------------------------------

class ResearchAgent:
    """Agente autônomo que pesquisa e salva no Obsidian via function calling."""

    def __init__(self, settings: Any, logger: logging.Logger | None = None):
        """
        Args:
            settings: Objeto com atributos:
                - openai_api_key (str)
                - obsidian_vault_path (str)  — caminho do vault Obsidian
                - agent_model (str, opcional) — modelo a usar (default gpt-4o-mini)
            logger: Logger opcional.
        """
        self.settings = settings
        self.log = logger or log
        self.client = OpenAI(api_key=_setting(settings, "openai_api_key"))
        self.vault_path: str = _setting(settings, "obsidian_vault_path")
        self.model: str = _setting(settings, "agent_model", "gpt-4o-mini")
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def run(
        self,
        task: str,
        on_event: Callable[[AgentEvent], None] | None = None,
    ) -> str:
        """Executa a tarefa de forma síncrona e retorna o resultado final.

        Args:
            task: Instrução em linguagem natural.
            on_event: Callback chamado a cada evento (pode atualizar a UI).

        Returns:
            Texto da última resposta do modelo (resumo final da tarefa).
        """
        emit = on_event or (lambda e: None)

        messages: list[dict] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task},
        ]

        emit(AgentEvent("thinking", f"Analisando tarefa: «{task}»"))
        self.log.info("Agent iniciando tarefa: %s", task)

        for iteration in range(MAX_ITERATIONS):
            if self._stop_event.is_set():
                emit(AgentEvent("error", "Agente interrompido pelo usuário."))
                return "Operação cancelada."

            # Chama o modelo
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOL_SCHEMAS,
                    tool_choice="auto",
                    temperature=0.2,
                )
            except Exception as exc:
                self.log.error("Erro na API OpenAI: %s", exc)
                emit(AgentEvent("error", f"Erro ao chamar a IA: {exc}"))
                return f"Erro: {exc}"

            choice = response.choices[0]
            msg = choice.message

            # Adiciona a resposta do modelo ao histórico
            messages.append(msg.model_dump(exclude_unset=True))

            # Se não há tool calls → tarefa concluída
            if not msg.tool_calls:
                final_text = msg.content or "Tarefa concluída."
                emit(AgentEvent("done", final_text))
                self.log.info("Agent concluiu em %d iteração(ões).", iteration + 1)
                return final_text

            # Processa cada tool call solicitada
            for tc in msg.tool_calls:
                tool_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}

                # Evento: NEXUS está usando uma ferramenta
                human_label = _tool_label(tool_name, args)
                emit(AgentEvent("tool_call", human_label, {"tool": tool_name, "args": args}))
                self.log.debug("Tool call: %s %s", tool_name, args)

                # Executa a ferramenta
                result = dispatch(tool_name, args, vault_path=self.vault_path)

                # Evento: resultado da ferramenta
                result_summary = _summarize_result(tool_name, result)
                emit(AgentEvent("tool_result", result_summary, {"tool": tool_name, "result": result}))

                # Adiciona o resultado ao histórico para o modelo continuar
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })

        # Segurança: loop encerrado por limite de iterações
        emit(AgentEvent("error", "Limite de iterações atingido. Tarefa pode estar incompleta."))
        return "Limite de iterações atingido."

    def run_async(
        self,
        task: str,
        on_event: Callable[[AgentEvent], None] | None = None,
        on_done: Callable[[str], None] | None = None,
    ) -> threading.Thread:
        """Executa a tarefa em thread separada para não travar a UI.

        Args:
            task: Instrução em linguagem natural.
            on_event: Callback chamado a cada evento (thread-safe se usar queue).
            on_done: Callback chamado com o resultado final.

        Returns:
            Thread iniciada (daemon=True).
        """
        def _worker():
            result = self.run(task, on_event=on_event)
            if on_done:
                on_done(result)

        thread = threading.Thread(target=_worker, daemon=True, name="nexus-agent")
        thread.start()
        return thread

    def stop(self) -> None:
        """Sinaliza para o agente parar na próxima iteração."""
        self._stop_event.set()


# ---------------------------------------------------------------------------
# Helpers de formatação para a UI
# ---------------------------------------------------------------------------

def _tool_label(tool_name: str, args: dict) -> str:
    if tool_name == "web_search":
        return f"🔍 Pesquisando: \"{args.get('query', '')}\""
    if tool_name == "scrape_page":
        url = args.get("url", "")
        short = url[:60] + "…" if len(url) > 60 else url
        return f"📄 Lendo página: {short}"
    if tool_name == "save_to_obsidian":
        return f"💾 Salvando no Obsidian: \"{args.get('title', '')}\""
    return f"⚙️ Executando: {tool_name}"


def _summarize_result(tool_name: str, result: dict) -> str:
    if tool_name == "web_search":
        n = len(result.get("results", []))
        return f"✅ {n} resultado(s) encontrado(s)."
    if tool_name == "scrape_page":
        if result.get("error"):
            return f"⚠️ Erro ao ler página: {result['error']}"
        chars = len(result.get("text", ""))
        return f"✅ Página lida — {chars} caracteres extraídos."
    if tool_name == "save_to_obsidian":
        if result.get("saved"):
            return f"✅ Nota salva: {result.get('filename', '')}"
        return f"⚠️ Erro ao salvar: {result.get('error', 'desconhecido')}"
    return f"✅ {tool_name} concluído."
