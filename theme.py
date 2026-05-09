"""
NEXUS — Assistente Pessoal Desktop
Ponto de entrada principal do sistema.

Uso:
    python theme.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
(ROOT / "data").mkdir(exist_ok=True)
(ROOT / "data" / "logs").mkdir(exist_ok=True)

from app.logger import log_action, log_command
from app.error_handler import handle_error
from app.intent_router import detectar_intent
from app.intent_apps import detectar_intent_apps
from app.security import avaliar_intent
from app.intent_desktop_actions import detect_desktop_intent
from app.action_policy_pc import evaluate_pc_action
from app.desktop_dispatcher import DesktopDispatcher
from app.memory import clear_memory
from app.core.command_router import CommandRouter
from app.core.text_utils import remove_wake_word
from app.features.command_suggestions import format_suggestions
from app.features.command_templates import describe_templates, get_template
from app.features.project_health import analyze_project
from app.features.session_recorder import SessionRecorder
from app.agent.agent_commands import AgentCommandHandler
from app.vision.vision_commands import VisionCommandHandler
from app.home.home_commands import HomeCommandHandler
from coding.intent_coding import detectar_intent_coding
from coding.dispatcher import executar_intent as executar_coding_intent


_desktop_dispatcher = DesktopDispatcher()
_command_router = CommandRouter()
_session_recorder = SessionRecorder(ROOT / "data" / "session_events.jsonl")
_agent_handler: AgentCommandHandler | None = None
_vision_handler: VisionCommandHandler | None = None
_home_handler: HomeCommandHandler | None = None


def _confirm_if_needed(intent_name: str, params: dict | None, confirm_callback) -> str | None:
    decision = avaliar_intent(intent_name, params)
    if not decision.allowed:
        return f"Ação bloqueada: {decision.reason or 'violou a política de segurança.'}"
    if decision.requires_confirmation:
        confirmado = confirm_callback(decision.message) if confirm_callback else False
        if not confirmado:
            return "Ação cancelada."
    return None


def processar_comando(texto: str, confirm_callback=None) -> str:
    texto = (texto or "").strip()
    if not texto:
        return "."

    _record_event("command", texto)
    try:
        result = _processar_comando_core(texto, confirm_callback)
        _record_event("response", result[:1200] if isinstance(result, str) else str(result))
        return result
    except Exception as error:
        result = handle_error(error)
        _record_event("error", result)
        return result


def _processar_comando_core(texto: str, confirm_callback=None) -> str:
    log_command(texto)
    try:
        from app.settings_manager import get as get_setting
        texto = remove_wake_word(texto, get_setting("wake_word", "nexus")) or texto
    except Exception:
        texto = remove_wake_word(texto, "nexus") or texto

    smart_response = _processar_recursos_inteligentes(texto, confirm_callback)
    if smart_response:
        return smart_response

    obsidian_response = _processar_obsidian(texto)
    if obsidian_response:
        return obsidian_response

    desktop_response = _processar_desktop(texto, confirm_callback)
    if desktop_response:
        return desktop_response

    coding_intent = detectar_intent_coding(texto)
    if coding_intent:
        blocked = _confirm_if_needed(coding_intent.name, coding_intent.params, confirm_callback)
        if blocked:
            return blocked
        return executar_coding_intent(coding_intent, confirm_callback)

    app_intent = detectar_intent_apps(texto)
    if app_intent:
        blocked = _confirm_if_needed(app_intent.name, app_intent.params, confirm_callback)
        if blocked:
            return blocked
        return _executar_intent(app_intent)

    intent = detectar_intent(texto)
    if intent is None:
        return _responder_ia(texto)

    blocked = _confirm_if_needed(intent.name, intent.params, confirm_callback)
    if blocked:
        return blocked

    return _executar_intent(intent)


def _record_event(kind: str, message: str, **data) -> None:
    try:
        _session_recorder.record(kind, message, **data)
    except Exception:
        pass


def _processar_recursos_inteligentes(texto: str, confirm_callback=None) -> str:
    command = _command_router.route(texto)

    if command.domain == "agent" and command.intent == "agent_task":
        task = command.args.get("task", texto)
        handler = _get_agent_handler()
        handler.handle(task)
        return f"Agente autônomo iniciado: {task}"

    if command.domain == "agent" and command.intent == "stop_agent":
        _get_agent_handler().stop()
        return "Agente autônomo parado."

    if command.domain == "vision" and command.intent == "vision":
        _get_vision_handler().handle(texto)
        return f"Visão NEXUS iniciada: {command.args.get('intent', 'análise')}"

    if command.domain == "home" and command.intent == "home":
        _get_home_handler().handle(texto)
        return f"Automação residencial iniciada: {command.args.get('intent', 'comando')}"

    if command.domain == "system" and command.intent == "help":
        return (
            "Comandos principais do NEXUS:\n"
            f"{describe_templates()}\n\n"
            f"{format_suggestions(texto, limit=8)}"
        )

    if command.intent == "run_template":
        return _executar_template(command.args.get("template", ""), confirm_callback)

    if command.intent == "project_health":
        return analyze_project(ROOT).as_text()

    if command.intent == "session_summary":
        return _session_recorder.summary(limit=20)

    return ""


def _get_agent_handler() -> AgentCommandHandler:
    global _agent_handler
    if _agent_handler is None:
        try:
            from app.settings_manager import load as load_settings
            cfg = load_settings()
        except Exception:
            cfg = {}
        _agent_handler = AgentCommandHandler(
            settings=cfg,
            ui_callback=lambda message: _record_event("agent", message),
        )
    return _agent_handler


def _get_vision_handler() -> VisionCommandHandler:
    global _vision_handler
    if _vision_handler is None:
        try:
            from app.settings_manager import load as load_settings
            cfg = load_settings()
        except Exception:
            cfg = {}
        _vision_handler = VisionCommandHandler(
            settings=cfg,
            ui_callback=lambda message: _record_event("vision", message),
        )
    return _vision_handler


def _get_home_handler() -> HomeCommandHandler:
    global _home_handler
    if _home_handler is None:
        try:
            from app.settings_manager import load as load_settings
            cfg = load_settings()
        except Exception:
            cfg = {}
        _home_handler = HomeCommandHandler(
            settings=cfg,
            ui_callback=lambda message: _record_event("home", message),
        )
    return _home_handler


def _executar_template(template_name: str, confirm_callback=None) -> str:
    template = get_template(template_name)
    if not template:
        return format_suggestions(template_name or "modo")

    if template.requires_confirmation:
        question = f"Confirmar execucao do template '{template.name}'?"
        if not (confirm_callback and confirm_callback(question)):
            return "Template cancelado."

    outputs = [f"Executando {template.name}: {template.description}"]
    for step in template.steps:
        intent_name = step.get("intent", "")
        args = step.get("args", {}) or {}
        try:
            decision = evaluate_pc_action(intent_name)
            if not decision.allowed:
                outputs.append(f"- {intent_name}: bloqueado ({decision.reason})")
                continue
            if decision.requires_confirmation:
                question = f"Confirmar acao '{intent_name}'? {decision.reason}".strip()
                if not (confirm_callback and confirm_callback(question)):
                    outputs.append(f"- {intent_name}: cancelado")
                    continue
            outputs.append(f"- {intent_name}: {_desktop_dispatcher.execute(intent_name, args)}")
        except Exception as error:
            outputs.append(f"- {intent_name}: {handle_error(error)}")
    return "\n".join(outputs)


def _processar_obsidian(texto: str) -> str:
    t = texto.strip()
    low = t.lower()
    if "obsidian" not in low and "vault" not in low:
        return ""
    try:
        from app.obsidian_memory import configure_vault, register, search_or_status

        if any(k in low for k in ("status", "conectado", "configurado")):
            return search_or_status()
        m = re.search(r"(?:conecta|configura|define|usar|usa)\s+(?:o\s+)?(?:obsidian|vault)(?:\s+em|\s+para|\s+como)?\s+(.+)", t, re.IGNORECASE)
        if m:
            return configure_vault(m.group(1).strip().strip('"'))
        m = re.search(r"(?:busca|procura|pesquisa)\s+(?:no\s+)?(?:obsidian|vault)\s+(.+)", t, re.IGNORECASE)
        if m:
            return search_or_status(m.group(1).strip())
        m = re.search(r"(?:salva|registra|guarda)\s+(?:no\s+)?(?:obsidian|vault)\s+(.+)", t, re.IGNORECASE)
        if m:
            note = register("Registro manual", m.group(1).strip(), source="nexus-manual")
            return f"Registrado no Obsidian: {note}" if note else "Não consegui registrar no Obsidian. Verifique o vault nas Configurações."
        return search_or_status()
    except Exception as e:
        return handle_error(e)


def _processar_desktop(texto: str, confirm_callback=None) -> str:
    desktop_intent = detect_desktop_intent(texto)
    if not desktop_intent:
        return ""

    decision = evaluate_pc_action(desktop_intent.name)
    if not decision.allowed:
        return f"Ação bloqueada: {decision.reason}"

    if decision.requires_confirmation:
        pergunta = f"Confirmar ação '{desktop_intent.name}'? {decision.reason}".strip()
        confirmado = confirm_callback(pergunta) if confirm_callback else False
        if not confirmado:
            return "Ação cancelada."

    try:
        return _desktop_dispatcher.execute(desktop_intent.name, desktop_intent.params)
    except Exception as error:
        return handle_error(error)


def _executar_intent(intent) -> str:
    """Despacha a intenção para o módulo correto."""
    try:
        name = intent.name
        p = intent.params

        if name in {"abrir_app", "abrir_programa"}:
            from automation.app_launcher import abrir_app
            if p.get("app"):
                return str(abrir_app(p.get("app", "")))
            from automation.apps import abrir_programa_por_nome
            return abrir_programa_por_nome(p.get("nome", ""))

        if name == "listar_apps":
            from automation.app_launcher import listar_apps
            return listar_apps()

        if name == "registrar_app":
            from automation.app_launcher import registrar_app
            return str(registrar_app(p.get("alias", ""), p.get("target", "")))

        if name == "abrir_chrome":
            from automation.apps import abrir_chrome
            return abrir_chrome()
        if name == "abrir_edge":
            from automation.apps import abrir_edge
            return abrir_edge()
        if name == "abrir_spotify":
            from automation.media import abrir_spotify
            return abrir_spotify()
        if name == "abrir_vscode":
            from automation.apps import abrir_vscode
            return abrir_vscode()
        if name == "abrir_bloco_de_notas":
            from automation.apps import abrir_bloco_de_notas
            return abrir_bloco_de_notas()
        if name == "abrir_calculadora":
            from automation.apps import abrir_calculadora
            return abrir_calculadora()

        if name == "abrir_youtube":
            from automation.browser import abrir_youtube
            return abrir_youtube()
        if name == "abrir_site":
            from automation.browser import abrir_site
            return abrir_site(p.get("url", ""))
        if name == "pesquisar_google":
            from automation.browser import pesquisar_google
            return pesquisar_google(p.get("termo", ""))
        if name == "pesquisar_youtube":
            from automation.browser import pesquisar_youtube
            return pesquisar_youtube(p.get("termo", ""))

        if name == "tocar_spotify":
            from automation.media import tocar_musica_spotify
            return tocar_musica_spotify(p.get("musica", ""))
        if name == "tocar_youtube":
            from automation.media import tocar_musica_youtube
            return tocar_musica_youtube(p.get("musica", ""))
        if name == "tocar_musica":
            from automation.media import escolher_plataforma_e_tocar
            return escolher_plataforma_e_tocar(p.get("musica", ""))

        if name == "abrir_downloads":
            from automation.files import abrir_downloads
            return abrir_downloads()
        if name == "abrir_desktop":
            from automation.files import abrir_area_trabalho
            return abrir_area_trabalho()
        if name == "criar_arquivo":
            from automation.files import criar_arquivo
            return criar_arquivo(p.get("nome", "arquivo.txt"))
        if name == "procurar_arquivo":
            from automation.files import procurar_arquivo
            return procurar_arquivo(p.get("nome", ""))

        if name == "status_pc":
            from automation.pc_control import mostrar_cpu_ram_disco
            return mostrar_cpu_ram_disco()
        if name == "desligar_pc":
            from automation.pc_control import desligar_pc
            return desligar_pc()
        if name == "reiniciar_pc":
            from automation.pc_control import reiniciar_pc
            return reiniciar_pc()
        if name == "suspender_pc":
            from automation.pc_control import suspender_pc
            return suspender_pc()
        if name == "bloquear_tela":
            from automation.pc_control import bloquear_tela
            return bloquear_tela()

        if name == "aumentar_volume":
            from automation.system import aumentar_volume
            return aumentar_volume()
        if name == "diminuir_volume":
            from automation.system import diminuir_volume
            return diminuir_volume()
        if name == "mutar_volume":
            from automation.system import mutar_volume
            return mutar_volume()

        if name == "tirar_print":
            from automation.system import tirar_print
            return tirar_print()
        if name == "mostrar_data_hora":
            from automation.system import mostrar_data_hora
            return mostrar_data_hora()
        if name == "limpar_memoria":
            clear_memory()
            return "Memória limpa."

        return _responder_ia(f"[Intenção desconhecida: {name}]")
    except Exception as e:
        return handle_error(e)


def _responder_ia(texto: str) -> str:
    """Envia o texto para a IA e retorna a resposta."""
    try:
        from app.assistant import responder
        return responder(texto)
    except Exception as e:
        return handle_error(e)


def main():
    """Inicializa o sistema NEXUS."""
    log_action("Sistema NEXUS iniciando...")

    from app.config import OPENAI_API_KEY
    if not OPENAI_API_KEY or OPENAI_API_KEY == "sua_chave_aqui":
        print("[AVISO] OPENAI_API_KEY não configurada. Respostas de IA indisponíveis.")
        print("        Configure o arquivo .env com sua chave da OpenAI.")

    from ui.desktop_app import NexusApp
    app = NexusApp(on_command_callback=processar_comando)
    log_action("Interface iniciada.")
    app.run()


if __name__ == "__main__":
    main()
