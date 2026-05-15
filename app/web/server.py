from __future__ import annotations

import asyncio
import base64
import json
import logging
import os
import secrets
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Callable

from fastapi import Depends, FastAPI, Header, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response, StreamingResponse
from pydantic import BaseModel, Field
import psutil

import app.settings_manager as settings_manager
from app.chat.chat_engine import ChatEngine
from app.chat.chat_handler import ChatHandler
from app.chat.conversation_mode import ConversationModeRuntime
from app.config import BASE_DIR
from app.finance.service import FinanceService
from app.features.project_health import analyze_project
from app.features.session_recorder import SessionRecorder
from app.logger import get_recent_logs
from app.memory_graph import build_memory_graph
from app.voice.manager import clear_backend_cache, listen_once
from app.voice.tts_service import TTSService
from app.voice.voice_profiles import list_profiles
from app.voice.voice_queue import VoiceQueue
from app.self_improvement.web_runtime import WebNexusMindRuntime
from app.vision.capture import CameraCapture, CapturedImage, ScreenCapture
from app.vision.analyzer import VisionAnalyzer

LOGGER = logging.getLogger("nexus.web")
SESSION_PATH = BASE_DIR / "data" / "session_events.jsonl"
DEFAULT_WEB_ALLOWED_ORIGINS = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
]
LOCAL_API_TOKEN_HEADER = "X-NEXUS-TOKEN"
TEXT_MEDIA_EXTENSIONS = {".txt", ".md", ".markdown", ".json", ".csv", ".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".log", ".yaml", ".yml"}
IMAGE_MEDIA_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif"}


def _automation_sections() -> list[dict[str, Any]]:
    return [
        {
            "title": "Navegadores",
            "tone": "secondary",
            "actions": [
                {"label": "Chrome", "command": "abre o Chrome"},
                {"label": "Edge", "command": "abre o Edge"},
                {"label": "YouTube", "command": "abre o YouTube"},
                {"label": "Google", "command": "pesquisa no google"},
            ],
        },
        {
            "title": "Midia",
            "tone": "secondary",
            "actions": [
                {"label": "Spotify", "command": "abre o Spotify"},
                {"label": "Tocar no YouTube", "command": "toca música no youtube"},
                {"label": "Tocar no Spotify", "command": "toca música no spotify"},
            ],
        },
        {
            "title": "Arquivos",
            "tone": "secondary",
            "actions": [
                {"label": "Downloads", "command": "abre meus downloads"},
                {"label": "Area de trabalho", "command": "abre a área de trabalho"},
                {"label": "Bloco de Notas", "command": "abre o bloco de notas"},
                {"label": "Calculadora", "command": "abre a calculadora"},
            ],
        },
        {
            "title": "Desktop",
            "tone": "secondary",
            "actions": [
                {"label": "Listar janelas", "command": "listar janelas"},
                {"label": "Screenshot", "command": "tirar screenshot"},
                {"label": "Clipboard", "command": "ler clipboard"},
                {"label": "Limpar clipboard", "command": "limpar clipboard"},
                {"label": "Docs", "command": "abrir pasta documentos"},
            ],
        },
        {
            "title": "Apps",
            "tone": "secondary",
            "actions": [
                {"label": "Listar apps", "command": "listar apps"},
            ],
        },
        {
            "title": "Sistema",
            "tone": "success",
            "actions": [
                {"label": "Status PC", "command": "mostra o status do PC"},
                {"label": "Print", "command": "tira print"},
                {"label": "Data/Hora", "command": "que horas são"},
                {"label": "Bloquear", "command": "bloquear tela"},
            ],
        },
        {
            "title": "Volume",
            "tone": "ghost",
            "actions": [
                {"label": "Aumentar", "command": "aumenta o volume"},
                {"label": "Diminuir", "command": "diminui o volume"},
                {"label": "Mutar", "command": "muta o som"},
            ],
        },
        {
            "title": "Critico",
            "tone": "danger",
            "actions": [
                {"label": "Reiniciar", "command": "reinicia o computador"},
                {"label": "Desligar", "command": "desliga o computador"},
            ],
        },
    ]


def _runtime_status() -> dict[str, Any]:
    try:
        cpu = psutil.cpu_percent(interval=0)
        ram = psutil.virtual_memory().percent
        root_drive = Path.home().drive or "C:"
        disk = psutil.disk_usage(f"{root_drive}\\").percent
    except Exception as error:  # pragma: no cover - depends on host
        LOGGER.warning("Falha ao ler status local: %s", error)
        cpu = ram = disk = 0.0

    return {
        "cpu": round(float(cpu), 1),
        "ram": round(float(ram), 1),
        "disk": round(float(disk), 1),
        "updated_at": datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
    }


def _voice_devices_snapshot() -> dict[str, Any]:
    try:
        import sounddevice as sd
    except Exception as error:  # pragma: no cover - optional dependency/runtime-specific
        return {
            "ok": False,
            "error": f"sounddevice indisponivel: {error}",
            "default_input_index": None,
            "default_output_index": None,
            "inputs": [],
            "outputs": [],
        }

    try:
        default_input, default_output = list(sd.default.device)
    except Exception:  # pragma: no cover - defensive
        default_input, default_output = None, None

    inputs: list[dict[str, Any]] = []
    outputs: list[dict[str, Any]] = []
    for index, device in enumerate(sd.query_devices()):
        row = {
            "index": index,
            "name": str(device.get("name", "") or ""),
            "max_input_channels": int(device.get("max_input_channels", 0) or 0),
            "max_output_channels": int(device.get("max_output_channels", 0) or 0),
            "default_samplerate": float(device.get("default_samplerate", 0) or 0),
        }
        if row["max_input_channels"] > 0:
            inputs.append(row)
        if row["max_output_channels"] > 0:
            outputs.append(row)

    return {
        "ok": True,
        "default_input_index": default_input,
        "default_output_index": default_output,
        "inputs": inputs,
        "outputs": outputs,
    }


def _allowed_web_origins() -> list[str]:
    configured = os.getenv("NEXUS_WEB_ALLOWED_ORIGINS", "").strip()
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]

    settings_value = settings_manager.load().get("web_allowed_origins", [])
    if isinstance(settings_value, str) and settings_value.strip():
        return [origin.strip() for origin in settings_value.split(",") if origin.strip()]
    if isinstance(settings_value, list):
        sanitized = [str(origin).strip() for origin in settings_value if str(origin).strip()]
        if sanitized:
            return sanitized
    return list(DEFAULT_WEB_ALLOWED_ORIGINS)


def _local_api_token() -> str:
    settings_token = str(settings_manager.load().get("local_api_token", "") or "").strip()
    env_token = os.getenv("NEXUS_LOCAL_API_TOKEN", "").strip()
    return settings_token or env_token


def _require_local_api_token(x_nexus_token: str | None = Header(default=None, alias=LOCAL_API_TOKEN_HEADER)) -> None:
    expected_token = _local_api_token()
    if not expected_token:
        return
    if not x_nexus_token or not secrets.compare_digest(x_nexus_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing or invalid {LOCAL_API_TOKEN_HEADER} header.",
        )


class SilentSpeaker:
    def speak(self, _text: str) -> None:
        return None


class ChatRequest(BaseModel):
    text: str = Field(default="", min_length=1)
    confirm: bool = False


class SettingsPayload(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)


class MediaAnalysisPayload(BaseModel):
    filename: str = Field(default="midia")
    media_type: str = Field(default="application/octet-stream")
    question: str = Field(default="")
    content_base64: str = Field(default="", min_length=1)


class MindSettingsPayload(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)


class VisionQuestionPayload(BaseModel):
    question: str = Field(default="")
    camera_index: int = Field(default=0, ge=0)


class FinanceTransactionPayload(BaseModel):
    title: str = Field(default="Movimento")
    amount: float = Field(default=0.0, ge=0)
    type: str = Field(default="expense")
    category: str = Field(default="Geral")
    account: str = Field(default="Conta principal")
    date: str = Field(default="")
    notes: str = Field(default="")
    finance_type: str = Field(default="variable")


class FinanceBillPayload(BaseModel):
    title: str = Field(default="Conta")
    amount: float = Field(default=0.0, ge=0)
    due_date: str = Field(default="")
    paid: bool = Field(default=False)
    recurrence: str = Field(default="none")
    account: str = Field(default="Conta principal")
    category: str = Field(default="Contas")
    notes: str = Field(default="")


class FinanceGoalPayload(BaseModel):
    title: str = Field(default="Meta financeira")
    target_amount: float = Field(default=0.0, ge=0)
    current_amount: float = Field(default=0.0, ge=0)
    deadline: str = Field(default="")
    notes: str = Field(default="")


class ConversationMessagePayload(BaseModel):
    text: str = Field(default="", min_length=1)
    session_id: str = Field(default="")
    study_mode: bool = Field(default=True)
    save_to_obsidian: bool = Field(default=False)


class ConversationResetPayload(BaseModel):
    session_id: str = Field(default="", min_length=1)


class ConversationSaveNotePayload(BaseModel):
    session_id: str = Field(default="", min_length=1)
    title: str = Field(default="Resumo de conversa", min_length=1)
    content: str = Field(default="", min_length=1)


class VoiceListenPayload(BaseModel):
    timeout: int = Field(default=5, ge=1, le=20)
    phrase_time_limit: int = Field(default=8, ge=1, le=20)


class VoiceSpeakPayload(BaseModel):
    text: str = Field(default="", min_length=1, max_length=2400)
    provider: str = Field(default="auto")
    profile: str = Field(default="jarvis")
    voice: str = Field(default="default")
    stream: bool = Field(default=False)


class VoiceChunksPayload(BaseModel):
    text: str = Field(default="", min_length=1, max_length=5000)
    provider: str = Field(default="auto")
    profile: str = Field(default="jarvis")


class VoiceTestPayload(BaseModel):
    provider: str = Field(default="auto")
    profile: str = Field(default="jarvis")


def _media_kind(filename: str, content_type: str) -> str:
    suffix = Path(filename).suffix.lower()
    if content_type.startswith("image/") or suffix in IMAGE_MEDIA_EXTENSIONS:
        return "image"
    if content_type.startswith("text/") or suffix in TEXT_MEDIA_EXTENSIONS:
        return "text"
    return "unsupported"


def _summarize_text_media(filename: str, text: str, question: str) -> str:
    cleaned = (text or "").strip()
    if not cleaned:
        return f"Recebi o arquivo '{filename}', mas ele nao trouxe texto legivel para eu analisar."

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    preview = "\n".join(lines[:12])[:2200]
    if question.strip():
        return (
            f"Recebi o arquivo '{filename}'. Ainda nao tenho analise multimidia completa para esse formato aqui na web, "
            f"mas consegui ler o conteudo textual inicial para te ajudar.\n\n"
            f"Pedido: {question.strip()}\n\n"
            f"Trecho detectado:\n{preview}"
        )
    return (
        f"Recebi o arquivo '{filename}' e consegui ler o conteudo textual inicial.\n\n"
        f"Trecho detectado:\n{preview}"
    )


def _serialize_captured_image(image: CapturedImage) -> dict[str, Any]:
    return {
        "base64_data": image.base64_data,
        "media_type": image.media_type,
        "width": image.width,
        "height": image.height,
        "source": image.source,
    }


_MIND_RUNTIME: WebNexusMindRuntime | None = None
_FINANCE_SERVICE: FinanceService | None = None
_CONVERSATION_RUNTIME: ConversationModeRuntime | None = None
_VOICE_QUEUE = VoiceQueue()


def _get_mind_runtime() -> WebNexusMindRuntime:
    global _MIND_RUNTIME
    if _MIND_RUNTIME is None:
        _MIND_RUNTIME = WebNexusMindRuntime()
    return _MIND_RUNTIME


def _get_finance_service() -> FinanceService:
    global _FINANCE_SERVICE
    if _FINANCE_SERVICE is None:
        _FINANCE_SERVICE = FinanceService(base_dir=BASE_DIR)
    return _FINANCE_SERVICE


def _get_conversation_runtime() -> ConversationModeRuntime:
    global _CONVERSATION_RUNTIME
    if _CONVERSATION_RUNTIME is None:
        _CONVERSATION_RUNTIME = ConversationModeRuntime()
    return _CONVERSATION_RUNTIME


def _resolve_theme_runtime() -> tuple[
    Callable[[str, Any | None], str],
    Callable[[Callable[[str, str, dict[str, Any]], None]], None],
    Callable[[Callable[[str, str, dict[str, Any]], None]], None],
]:
    try:
        from theme import processar_comando, subscribe_live_event, unsubscribe_live_event
    except Exception as error:  # pragma: no cover - fallback path
        LOGGER.warning("Pipeline principal indisponivel para a web: %s", error)
        message = f"Pipeline principal indisponivel: {error}"

        def _fallback_process(text: str, _confirm_callback=None) -> str:
            return message

        def _noop(_listener) -> None:
            return None

        return _fallback_process, _noop, _noop

    return processar_comando, subscribe_live_event, unsubscribe_live_event


def build_chat_engine() -> ChatEngine:
    settings = settings_manager.load()
    command_executor, _, _ = _resolve_theme_runtime()
    handler = ChatHandler(
        settings=settings,
        logger=LOGGER,
        command_executor=command_executor,
    )
    return ChatEngine(
        settings=settings,
        logger=LOGGER,
        speaker=SilentSpeaker(),
        handler=handler,
    )


def _flag(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "sim", "on"}


def _mind_settings_snapshot() -> dict[str, Any]:
    snapshot = {
        "directive": "",
        "auto_restart": False,
        "active": False,
        "mode": "supervisionado",
        "interval": 5,
    }
    path = BASE_DIR / "data" / "mind_settings.json"
    try:
        if path.exists():
            loaded = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                snapshot.update(loaded)
    except Exception as error:  # pragma: no cover - defensive read
        LOGGER.warning("Falha ao ler snapshot do NexusMind: %s", error)

    mode = str(snapshot.get("mode", "supervisionado") or "supervisionado").strip().lower()
    if mode == "autonomo":
        mode = "autônomo"
    snapshot["mode"] = mode
    return snapshot


def _module_cards() -> list[dict[str, Any]]:
    settings = settings_manager.load()
    openai_ready = bool(str(settings.get("openai_api_key", "") or "").strip())
    local_token_ready = bool(_local_api_token())
    voice_engine = str(settings.get("voice_engine", "pyttsx3") or "pyttsx3").strip().lower()
    eleven_ready = bool(str(settings.get("elevenlabs_api_key", "") or "").strip()) and bool(str(settings.get("elevenlabs_voice_id", "") or "").strip())
    obsidian_enabled = _flag(settings.get("obsidian_enabled", True), default=True)
    obsidian_path_text = str(settings.get("obsidian_vault_path", "") or "").strip()
    obsidian_path_ready = bool(obsidian_path_text and Path(obsidian_path_text).exists())
    git_ready = (BASE_DIR / ".git").exists()
    spotify_ready = bool(str(settings.get("spotify_client_id", "") or "").strip())
    ha_token_ready = bool(str(settings.get("ha_token", "") or "").strip())
    voice_confirm_ready = _flag(settings.get("voice_confirm_commands", True), default=True)
    mind_autonomy_unlocked = _flag(settings.get("mind_allow_autonomous", False), default=False)
    mind_settings = _mind_settings_snapshot()
    mind_mode = str(mind_settings.get("mode", "supervisionado") or "supervisionado")
    mind_active = _flag(mind_settings.get("active", False), default=False)

    integrations_missing: list[str] = []
    if not spotify_ready:
        integrations_missing.append("Spotify")
    if not ha_token_ready:
        integrations_missing.append("Home Assistant")

    if voice_engine == "elevenlabs":
        voice_status = "online" if eleven_ready else "partial"
        voice_tone = "lime" if eleven_ready else "amber"
        voice_detail = "ElevenLabs configurado e pronto para fala premium." if eleven_ready else "Falta ElevenLabs API key ou Voice ID para voz premium."
    else:
        voice_status = "online"
        voice_tone = "lime"
        voice_detail = f"Voz local pronta via {voice_engine or 'pyttsx3'}."

    if not obsidian_enabled:
        memory_status = "paused"
        memory_tone = "amber"
        memory_detail = "Memoria Obsidian desativada nas configuracoes."
    elif obsidian_path_ready:
        memory_status = "online"
        memory_tone = "sky"
        memory_detail = "Vault configurado e acessivel para memoria persistente."
    else:
        memory_status = "offline"
        memory_tone = "rose"
        memory_detail = "Vault nao configurado ou caminho indisponivel."

    if not mind_autonomy_unlocked:
        mind_status = "paused"
        mind_tone = "amber"
        mind_detail = "Modo supervisionado ativo; autonomia avancada segue bloqueada."
    elif mind_active and mind_mode != "supervisionado":
        mind_status = "online"
        mind_tone = "lime"
        mind_detail = f"NexusMind ativo em modo {mind_mode}."
    else:
        mind_status = "guarded"
        mind_tone = "orange"
        mind_detail = f"NexusMind pronto em modo {mind_mode}, aguardando aprovacao."

    return [
        {
            "id": "api",
            "title": "Web API local",
            "description": "Camada FastAPI que conecta painel, chat, visao e automacoes locais.",
            "status": "online" if local_token_ready else "guarded",
            "tone": "cyan",
            "sector": "Plataforma",
            "icon": "monitor-smartphone",
            "examples": ["dashboard", "logs", "eventos ao vivo"],
            "detail": "Origens locais e token de protecao ativos." if local_token_ready else "Defina local_api_token para proteger chat, visao e automacoes.",
            "permission": "Somente localhost" if local_token_ready else "Token recomendado",
            "action_label": "abrir sistema",
            "configured": local_token_ready,
        },
        {
            "id": "chat",
            "title": "Chat e IA",
            "description": "Entrada principal para conversar com o NEXUS e disparar acoes por texto.",
            "status": "online" if openai_ready else "partial",
            "tone": "cyan" if openai_ready else "amber",
            "sector": "Atendimento",
            "icon": "message-square",
            "examples": ["ajuda", "ultimos eventos", "diagnostico do projeto"],
            "detail": "OpenAI configurada e pronta para respostas." if openai_ready else "Configure a chave da OpenAI para ativar respostas inteligentes.",
            "permission": "Confirmacao em acoes de risco",
            "action_label": "abrir chat",
            "configured": openai_ready,
        },
        {
            "id": "voice",
            "title": "Voz",
            "description": "Captura de microfone, wake word e resposta falada com backend local ou premium.",
            "status": voice_status,
            "tone": voice_tone,
            "sector": "Atendimento",
            "icon": "message-square",
            "examples": ["nexus ajuda", "nexus abrir chrome", "nexus que horas sao"],
            "detail": voice_detail,
            "permission": "Microfone sob demanda",
            "action_label": "abrir perfil",
            "configured": voice_status == "online",
        },
        {
            "id": "vision",
            "title": "Vision",
            "description": "OCR, camera e leitura visual da tela para suporte contextual.",
            "status": "online" if openai_ready else "partial",
            "tone": "lime" if openai_ready else "amber",
            "sector": "Analise",
            "icon": "scan-search",
            "examples": ["descreve a tela", "analisa o codigo na tela", "le esse texto da imagem"],
            "detail": "Captura de tela e camera prontas para analise." if openai_ready else "Visao local pronta, mas falta IA configurada para interpretar imagens.",
            "permission": "Tela e camera sob comando",
            "action_label": "abrir visao",
            "configured": openai_ready,
        },
        {
            "id": "automation",
            "title": "Desktop e navegador",
            "description": "Abre, fecha, foca e pesquisa em janelas, apps, pastas e sites.",
            "status": "guarded",
            "tone": "orange",
            "sector": "Desktop",
            "icon": "monitor-smartphone",
            "examples": ["abrir spotify", "fechar spotify", "pesquisar no youtube lofi coding"],
            "detail": "Automacoes locais prontas; revise confirmacoes para comandos mais criticos." if voice_confirm_ready else "Confirmacao de voz desativada. Revise o nivel de risco antes de ampliar automacoes.",
            "permission": "Confirmacao para risco",
            "action_label": "abrir automacao",
            "configured": voice_confirm_ready,
        },
        {
            "id": "coder",
            "title": "Coder e Git",
            "description": "Fluxos de codigo, patch, diff, testes e contexto de projeto para desenvolvimento local.",
            "status": "ready" if git_ready else "partial",
            "tone": "amber" if git_ready else "rose",
            "sector": "Desenvolvimento",
            "icon": "code-2",
            "examples": ["rode esse codigo", "explique esse codigo", "corrija esse codigo"],
            "detail": "Repositorio Git detectado com workspace local pronto." if git_ready else "Repositorio Git nao detectado na raiz atual.",
            "permission": "Diff antes de escrita",
            "action_label": "abrir painel",
            "configured": git_ready,
        },
        {
            "id": "memory",
            "title": "Memoria e contexto",
            "description": "Historico de sessao, eventos, notas e contexto persistente.",
            "status": memory_status,
            "tone": memory_tone,
            "sector": "Memoria",
            "icon": "database",
            "examples": ["historico da sessao", "salva no obsidian resumo da reuniao", "status do vault"],
            "detail": memory_detail,
            "permission": "Acesso ao vault local",
            "action_label": "abrir memoria",
            "configured": memory_status == "online",
        },
        {
            "id": "integrations",
            "title": "Integracoes",
            "description": "Spotify, Home Assistant e servicos externos ligados ao ecossistema do Nexus.",
            "status": "online" if not integrations_missing else "partial",
            "tone": "rose" if not integrations_missing else "amber",
            "sector": "Integracoes",
            "icon": "music-4",
            "examples": ["quero ouvir luan santana", "status da casa", "ligar luz da sala"],
            "detail": "Spotify e Home Assistant configurados." if not integrations_missing else f"Pendencias de configuracao: {', '.join(integrations_missing)}.",
            "permission": "Tokens locais",
            "action_label": "abrir integracoes",
            "configured": not integrations_missing,
        },
        {
            "id": "mind",
            "title": "NexusMind",
            "description": "Autoanalise, ciclos supervisionados e melhoria assistida do proprio sistema.",
            "status": mind_status,
            "tone": mind_tone,
            "sector": "Evolucao",
            "icon": "code-2",
            "examples": ["diagnostico do projeto", "ciclo manual", "proof of work"],
            "detail": mind_detail,
            "permission": "Autonomia supervisionada",
            "action_label": "abrir mind",
            "configured": mind_autonomy_unlocked,
        },
    ]


def build_dashboard_payload(log_limit: int = 40, event_limit: int = 20) -> dict[str, Any]:
    report = analyze_project(BASE_DIR)
    recorder = SessionRecorder(SESSION_PATH)
    return {
        "project_root": str(BASE_DIR),
        "health": asdict(report),
        "modules": _module_cards(),
        "logs": get_recent_logs(log_limit),
        "events": [asdict(item) for item in recorder.tail(event_limit)],
        "settings": settings_manager.load(),
        "runtime": _runtime_status(),
    }


def create_app() -> FastAPI:
    app = FastAPI(
        title="NEXUS Web API",
        version="0.1.0",
        description="HTTP layer for the new Magic UI-driven NEXUS interface.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_web_origins(),
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Content-Type", LOCAL_API_TOKEN_HEADER],
    )
    recorder = SessionRecorder(SESSION_PATH)

    @app.get("/api/health")
    def get_health() -> dict[str, Any]:
        payload = build_dashboard_payload(log_limit=1, event_limit=1)
        return {
            "ok": True,
            "project_root": payload["project_root"],
            "health": payload["health"],
            "modules": payload["modules"],
        }

    @app.get("/api/dashboard")
    def get_dashboard(
        log_limit: int = Query(default=40, ge=1, le=200),
        event_limit: int = Query(default=20, ge=1, le=100),
    ) -> dict[str, Any]:
        return build_dashboard_payload(log_limit=log_limit, event_limit=event_limit)

    @app.get("/api/logs")
    def get_logs(
        limit: int = Query(default=80, ge=1, le=500),
        query: str = Query(default=""),
    ) -> dict[str, Any]:
        items = get_recent_logs(limit)
        if query.strip():
            needle = query.strip().lower()
            items = [line for line in items if needle in line.lower()]
        return {"items": items}

    @app.get("/api/events/recent")
    def get_recent_events(limit: int = Query(default=30, ge=1, le=120)) -> dict[str, Any]:
        return {"items": [asdict(item) for item in recorder.tail(limit)]}

    @app.get("/api/settings")
    def get_settings() -> dict[str, Any]:
        return {"settings": settings_manager.load()}

    @app.get("/api/memory/graph")
    def get_memory_graph(note_limit: int = Query(default=90, ge=10, le=250)) -> dict[str, Any]:
        return build_memory_graph(note_limit=note_limit)

    @app.get("/api/finance/summary")
    def get_finance_summary() -> dict[str, Any]:
        return _get_finance_service().summary()

    @app.get("/api/finance/transactions")
    def get_finance_transactions() -> dict[str, Any]:
        return {"items": _get_finance_service().list_transactions()}

    @app.post("/api/finance/transactions", dependencies=[Depends(_require_local_api_token)])
    def post_finance_transaction(payload: FinanceTransactionPayload) -> dict[str, Any]:
        return {"item": _get_finance_service().add_transaction(payload.model_dump())}

    @app.get("/api/finance/bills")
    def get_finance_bills() -> dict[str, Any]:
        return {"items": _get_finance_service().list_bills()}

    @app.post("/api/finance/bills", dependencies=[Depends(_require_local_api_token)])
    def post_finance_bill(payload: FinanceBillPayload) -> dict[str, Any]:
        return {"item": _get_finance_service().add_bill(payload.model_dump())}

    @app.put("/api/finance/bills/{bill_id}/pay", dependencies=[Depends(_require_local_api_token)])
    def put_finance_bill_pay(bill_id: str) -> dict[str, Any]:
        return {"item": _get_finance_service().pay_bill(bill_id)}

    @app.get("/api/finance/goals")
    def get_finance_goals() -> dict[str, Any]:
        return {"items": _get_finance_service().list_goals()}

    @app.post("/api/finance/goals", dependencies=[Depends(_require_local_api_token)])
    def post_finance_goal(payload: FinanceGoalPayload) -> dict[str, Any]:
        return {"item": _get_finance_service().add_goal(payload.model_dump())}

    @app.get("/api/finance/chart/monthly")
    def get_finance_chart_monthly() -> dict[str, Any]:
        return _get_finance_service().monthly_chart()

    @app.get("/api/finance/categories")
    def get_finance_categories() -> dict[str, Any]:
        return _get_finance_service().categories()

    @app.post("/api/conversation/message", dependencies=[Depends(_require_local_api_token)])
    def post_conversation_message(payload: ConversationMessagePayload) -> dict[str, Any]:
        return _get_conversation_runtime().process_message(
            payload.text,
            session_id=payload.session_id or None,
            study_mode=payload.study_mode,
            save_to_obsidian=payload.save_to_obsidian,
        ).to_dict()

    @app.post("/api/conversation/reset", dependencies=[Depends(_require_local_api_token)])
    def post_conversation_reset(payload: ConversationResetPayload) -> dict[str, Any]:
        _get_conversation_runtime().reset(payload.session_id)
        return {"ok": True}

    @app.post("/api/conversation/save-note", dependencies=[Depends(_require_local_api_token)])
    def post_conversation_save_note(payload: ConversationSaveNotePayload) -> dict[str, Any]:
        path = _get_conversation_runtime().save_note(
            session_id=payload.session_id,
            title=payload.title,
            content=payload.content,
        )
        return {"ok": bool(path), "path": path}

    @app.get("/api/conversation/state")
    def get_conversation_state() -> dict[str, Any]:
        return _get_conversation_runtime().get_state()

    @app.get("/api/voice/devices")
    def get_voice_devices() -> dict[str, Any]:
        return _voice_devices_snapshot()

    @app.post("/api/voice/listen-once", dependencies=[Depends(_require_local_api_token)])
    def post_voice_listen_once(payload: VoiceListenPayload) -> dict[str, Any]:
        settings = settings_manager.load()
        clear_backend_cache()
        try:
            result = listen_once(
                settings=settings,
                backend=str(settings.get("voice_backend", "auto") or "auto"),
                timeout=payload.timeout,
                phrase_time_limit=payload.phrase_time_limit,
            )
            return {
                "ok": True,
                "text": (result.text or "").strip(),
                "backend": result.backend,
                "confidence": result.confidence,
                "device_index": settings.get("voice_input_device") if settings.get("voice_input_device") not in (None, "") else None,
            }
        except Exception as error:
            return {
                "ok": False,
                "text": "",
                "backend": str(settings.get("voice_backend", "auto") or "auto"),
                "confidence": None,
                "device_index": settings.get("voice_input_device") if settings.get("voice_input_device") not in (None, "") else None,
                "error": str(error),
            }

    @app.get("/api/voice/profiles")
    def get_voice_profiles() -> dict[str, Any]:
        return {
            "ok": True,
            "profiles": list_profiles(),
            "providers": ["auto", "openai", "elevenlabs", "edge", "pyttsx3", "browser_fallback"],
        }

    @app.post("/api/voice/speak", dependencies=[Depends(_require_local_api_token)])
    def post_voice_speak(payload: VoiceSpeakPayload) -> Response:
        service = TTSService(settings_manager.load())
        item = service.synthesize_to_file(
            payload.text,
            provider=payload.provider,
            voice=payload.voice,
            profile=payload.profile,
        )
        _VOICE_QUEUE.enqueue(payload.text)
        return Response(
            content=item.path.read_bytes(),
            media_type=item.content_type,
            headers={
                "Cache-Control": "no-store",
                "X-NEXUS-AUDIO-ID": item.key,
                "X-NEXUS-AUDIO-URL": f"/api/voice/cache/{item.path.name}",
            },
        )

    @app.post("/api/voice/stream", dependencies=[Depends(_require_local_api_token)])
    def post_voice_stream(payload: VoiceSpeakPayload) -> StreamingResponse:
        service = TTSService(settings_manager.load())
        item = service.synthesize_to_file(
            payload.text,
            provider=payload.provider,
            voice=payload.voice,
            profile=payload.profile,
        )

        def _iter_audio():
            with item.path.open("rb") as file:
                while chunk := file.read(64 * 1024):
                    yield chunk

        return StreamingResponse(_iter_audio(), media_type=item.content_type, headers={"X-NEXUS-AUDIO-ID": item.key})

    @app.post("/api/voice/chunks", dependencies=[Depends(_require_local_api_token)])
    def post_voice_chunks(payload: VoiceChunksPayload) -> dict[str, Any]:
        service = TTSService(settings_manager.load())
        chunks = service.synthesize_chunks(payload.text, provider=payload.provider, profile=payload.profile)
        for chunk in chunks:
            _VOICE_QUEUE.enqueue(chunk["text"])
        return {"ok": True, "chunks": chunks}

    @app.get("/api/voice/cache/{filename}")
    def get_voice_cache(filename: str) -> FileResponse:
        safe_name = Path(filename).name
        path = BASE_DIR / "data" / "audio_cache" / safe_name
        if not path.exists() or path.suffix.lower() not in {".mp3", ".wav"}:
            raise HTTPException(status_code=404, detail="Audio nao encontrado.")
        media_type = "audio/wav" if path.suffix.lower() == ".wav" else "audio/mpeg"
        return FileResponse(path, media_type=media_type)

    @app.post("/api/voice/test", dependencies=[Depends(_require_local_api_token)])
    def post_voice_test(payload: VoiceTestPayload) -> Response:
        service = TTSService(settings_manager.load())
        item = service.synthesize_to_file(
            "Nexus online. Voz profissional ativada.",
            provider=payload.provider,
            profile=payload.profile,
        )
        return Response(content=item.path.read_bytes(), media_type=item.content_type, headers={"X-NEXUS-AUDIO-ID": item.key})

    @app.post("/api/voice/stop", dependencies=[Depends(_require_local_api_token)])
    def post_voice_stop() -> dict[str, Any]:
        token = _VOICE_QUEUE.stop()
        return {"ok": True, "state": "interrupted", "token": token}

    @app.get("/api/runtime/status")
    def get_runtime_status() -> dict[str, Any]:
        return _runtime_status()

    @app.get("/api/automation/catalog")
    def get_automation_catalog(query: str = Query(default="")) -> dict[str, Any]:
        sections = _automation_sections()
        if query.strip():
            needle = query.strip().lower()
            filtered_sections: list[dict[str, Any]] = []
            for section in sections:
                shown = [
                    action
                    for action in section["actions"]
                    if needle in section["title"].lower()
                    or needle in action["label"].lower()
                    or needle in action["command"].lower()
                ]
                if shown:
                    filtered_sections.append({**section, "actions": shown})
            sections = filtered_sections
        return {"sections": sections}

    @app.get("/api/mind/state")
    def get_mind_state() -> dict[str, Any]:
        return _get_mind_runtime().get_state()

    @app.put("/api/mind/settings", dependencies=[Depends(_require_local_api_token)])
    def put_mind_settings(payload: MindSettingsPayload) -> dict[str, Any]:
        return _get_mind_runtime().update_settings(payload.settings)

    @app.post("/api/mind/start", dependencies=[Depends(_require_local_api_token)])
    def post_mind_start() -> dict[str, Any]:
        return _get_mind_runtime().start()

    @app.post("/api/mind/stop", dependencies=[Depends(_require_local_api_token)])
    def post_mind_stop() -> dict[str, Any]:
        return _get_mind_runtime().stop()

    @app.post("/api/mind/cycle", dependencies=[Depends(_require_local_api_token)])
    def post_mind_cycle() -> dict[str, Any]:
        return _get_mind_runtime().run_manual_cycle()

    @app.post("/api/mind/rollback", dependencies=[Depends(_require_local_api_token)])
    def post_mind_rollback() -> dict[str, Any]:
        return _get_mind_runtime().rollback()

    @app.post("/api/mind/proof", dependencies=[Depends(_require_local_api_token)])
    def post_mind_proof() -> dict[str, Any]:
        return _get_mind_runtime().refresh_proof()

    @app.post("/api/mind/restart/clear", dependencies=[Depends(_require_local_api_token)])
    def post_mind_clear_restart() -> dict[str, Any]:
        return _get_mind_runtime().clear_restart_flag()

    @app.get("/api/vision/status")
    def get_vision_status() -> dict[str, Any]:
        try:
            camera_indices = CameraCapture().list_cameras()
        except Exception as error:
            camera_indices = []
            LOGGER.warning("Falha ao listar cameras: %s", error)
        return {
            "ok": True,
            "camera_indices": camera_indices,
            "default_camera_index": int(settings_manager.load().get("camera_index", 0) or 0),
        }

    @app.post("/api/vision/screen/capture", dependencies=[Depends(_require_local_api_token)])
    def post_vision_screen_capture() -> dict[str, Any]:
        try:
            image = ScreenCapture().capture()
            return {
                "ok": True,
                "action": "screen_capture",
                "image": _serialize_captured_image(image),
                "response": "Tela capturada com sucesso.",
            }
        except Exception as error:
            return {
                "ok": False,
                "action": "screen_capture",
                "image": None,
                "response": f"Falha ao capturar a tela: {error}",
            }

    @app.post("/api/vision/camera/capture", dependencies=[Depends(_require_local_api_token)])
    def post_vision_camera_capture(payload: VisionQuestionPayload | None = None) -> dict[str, Any]:
        camera_index = payload.camera_index if payload else 0
        try:
            image = CameraCapture(camera_index=camera_index).capture()
            return {
                "ok": True,
                "action": "camera_capture",
                "image": _serialize_captured_image(image),
                "response": "Frame da câmera capturado com sucesso.",
            }
        except Exception as error:
            return {
                "ok": False,
                "action": "camera_capture",
                "image": None,
                "response": f"Falha ao capturar a câmera: {error}",
            }

    @app.post("/api/vision/screen/{action}", dependencies=[Depends(_require_local_api_token)])
    def post_vision_screen_action(action: str, payload: VisionQuestionPayload | None = None) -> dict[str, Any]:
        analyzer = VisionAnalyzer(settings_manager.load(), LOGGER)
        try:
            image = ScreenCapture().capture()
            if action == "describe":
                response = analyzer.describe(image)
            elif action == "read-text":
                response = analyzer.read_text(image)
            elif action == "analyze-code":
                response = analyzer.analyze_code(image)
            elif action == "find-objects":
                response = analyzer.find_objects(image)
            elif action == "ask":
                question = (payload.question if payload else "").strip()
                response = analyzer.custom(image, question or "O que você observa nesta tela?")
            else:
                return {
                    "ok": False,
                    "action": action,
                    "image": None,
                    "response": "Ação de visão de tela não suportada.",
                }
            return {
                "ok": not str(response).startswith("[NEXUS Vision] Erro"),
                "action": action,
                "image": _serialize_captured_image(image),
                "response": response,
            }
        except Exception as error:
            return {
                "ok": False,
                "action": action,
                "image": None,
                "response": f"Falha na visão de tela: {error}",
            }

    @app.post("/api/vision/camera/{action}", dependencies=[Depends(_require_local_api_token)])
    def post_vision_camera_action(action: str, payload: VisionQuestionPayload | None = None) -> dict[str, Any]:
        analyzer = VisionAnalyzer(settings_manager.load(), LOGGER)
        camera_index = payload.camera_index if payload else 0
        try:
            image = CameraCapture(camera_index=camera_index).capture()
            if action == "describe":
                response = analyzer.watch_camera(image)
            elif action == "find-objects":
                response = analyzer.find_objects(image)
            elif action == "ask":
                question = (payload.question if payload else "").strip()
                response = analyzer.custom(image, question or "O que aparece na câmera?")
            else:
                return {
                    "ok": False,
                    "action": action,
                    "image": None,
                    "response": "Ação de visão de câmera não suportada.",
                }
            return {
                "ok": not str(response).startswith("[NEXUS Vision] Erro"),
                "action": action,
                "image": _serialize_captured_image(image),
                "response": response,
            }
        except Exception as error:
            return {
                "ok": False,
                "action": action,
                "image": None,
                "response": f"Falha na visão de câmera: {error}",
            }

    @app.put("/api/settings", dependencies=[Depends(_require_local_api_token)])
    def put_settings(payload: SettingsPayload) -> dict[str, Any]:
        saved = settings_manager.save(payload.settings)
        return {"settings": saved}

    @app.post("/api/chat", dependencies=[Depends(_require_local_api_token)])
    def post_chat(payload: ChatRequest) -> dict[str, Any]:
        engine = build_chat_engine()
        confirmation_prompt: str | None = None

        def _confirm(message: str) -> bool:
            nonlocal confirmation_prompt
            confirmation_prompt = message
            return payload.confirm

        result = engine.process_input(
            payload.text,
            speak=False,
            confirm_callback=_confirm,
        )
        if confirmation_prompt and not payload.confirm:
            result["response"] = confirmation_prompt
        result["confirmation_required"] = bool(confirmation_prompt and not payload.confirm)
        result["confirmation_message"] = confirmation_prompt
        return result

    @app.post("/api/media/analyze", dependencies=[Depends(_require_local_api_token)])
    def post_media_analyze(payload: MediaAnalysisPayload) -> dict[str, Any]:
        filename = payload.filename or "midia"
        content_type = payload.media_type or "application/octet-stream"
        media_kind = _media_kind(filename, content_type)
        binary = base64.b64decode(payload.content_base64.encode("utf-8"))

        if not binary:
            return {
                "filename": filename,
                "media_type": media_kind,
                "response": "Nao encontrei dados nessa midia. Tente anexar novamente.",
                "supported": False,
            }

        if media_kind == "image":
            temp_path: Path | None = None
            try:
                suffix = Path(filename).suffix or ".jpg"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                    temp_file.write(binary)
                    temp_path = Path(temp_file.name)

                analyzer = VisionAnalyzer(settings_manager.load(), LOGGER)
                response = analyzer.custom(temp_path, payload.question.strip()) if payload.question.strip() else analyzer.describe(temp_path)
                return {
                    "filename": filename,
                    "media_type": media_kind,
                    "response": response,
                    "supported": not response.startswith("[NEXUS Vision] Erro"),
                }
            finally:
                if temp_path and temp_path.exists():
                    temp_path.unlink(missing_ok=True)

        if media_kind == "text":
            text = binary.decode("utf-8", errors="replace")
            return {
                "filename": filename,
                "media_type": media_kind,
                "response": _summarize_text_media(filename, text, payload.question),
                "supported": True,
            }

        return {
            "filename": filename,
            "media_type": media_kind,
            "response": "Consigo analisar imagens e arquivos de texto por aqui. Para esse formato, anexe uma imagem ou um arquivo textual.",
            "supported": False,
        }

    @app.get("/api/events/stream")
    async def stream_events() -> StreamingResponse:
        event_queue: Queue[dict[str, Any]] = Queue()
        _, subscribe_live_event, unsubscribe_live_event = _resolve_theme_runtime()

        def _listener(kind: str, message: str, data: dict[str, Any]) -> None:
            event_queue.put(
                {
                    "kind": kind,
                    "message": message,
                    "data": data,
                }
            )

        async def _event_iterator():
            subscribe_live_event(_listener)
            try:
                while True:
                    try:
                        event = await asyncio.to_thread(event_queue.get, True, 12)
                        payload = json.dumps(event, ensure_ascii=False)
                        yield f"data: {payload}\n\n"
                    except Empty:
                        yield ": keepalive\n\n"
            finally:
                unsubscribe_live_event(_listener)

        return StreamingResponse(_event_iterator(), media_type="text/event-stream")

    return app


app = create_app()


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    import uvicorn

    uvicorn.run(app, host=host, port=port, reload=False)
