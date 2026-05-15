from __future__ import annotations

import asyncio
import base64
import json
import logging
import tempfile
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from queue import Empty, Queue
from typing import Any, Callable

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import psutil

import app.settings_manager as settings_manager
from app.chat.chat_engine import ChatEngine
from app.chat.chat_handler import ChatHandler
from app.config import BASE_DIR
from app.features.project_health import analyze_project
from app.features.session_recorder import SessionRecorder
from app.logger import get_recent_logs
from app.memory_graph import build_memory_graph
from app.self_improvement.web_runtime import WebNexusMindRuntime
from app.vision.capture import CameraCapture, CapturedImage, ScreenCapture
from app.vision.analyzer import VisionAnalyzer

LOGGER = logging.getLogger("nexus.web")
SESSION_PATH = BASE_DIR / "data" / "session_events.jsonl"
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


def _get_mind_runtime() -> WebNexusMindRuntime:
    global _MIND_RUNTIME
    if _MIND_RUNTIME is None:
        _MIND_RUNTIME = WebNexusMindRuntime()
    return _MIND_RUNTIME


def _resolve_theme_runtime() -> tuple[
    Callable[[str, Any | None], str],
    Callable[[Callable[[str, str, dict[str, Any]], None]], None],
    Callable[[Callable[[str, str, dict[str, Any]], None]], None],
]:
    try:
        from theme import processar_comando, subscribe_live_event, unsubscribe_live_event
    except Exception as error:  # pragma: no cover - fallback path
        LOGGER.warning("Pipeline principal indisponivel para a web: %s", error)

        def _fallback_process(text: str, _confirm_callback=None) -> str:
            return f"Pipeline principal indisponivel: {error}"

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


def _module_cards() -> list[dict[str, Any]]:
    return [
        {
            "id": "chat",
            "title": "Chat e comandos",
            "description": "Entrada principal para conversar com o NEXUS e disparar acoes por texto.",
            "status": "online",
            "tone": "cyan",
            "sector": "Atendimento",
            "icon": "message-square",
            "examples": ["ajuda", "ultimos eventos", "diagnostico do projeto"],
        },
        {
            "id": "coder",
            "title": "Coder",
            "description": "Fluxos de codigo, patch, git, terminal e automacoes de desenvolvimento.",
            "status": "ready",
            "tone": "amber",
            "sector": "Desenvolvimento",
            "icon": "code-2",
            "examples": ["rode esse codigo", "explique esse codigo", "corrija esse codigo"],
        },
        {
            "id": "vision",
            "title": "Vision",
            "description": "OCR, camera e leitura visual da tela para suporte contextual.",
            "status": "ready",
            "tone": "lime",
            "sector": "Analise",
            "icon": "scan-search",
            "examples": ["descreve a tela", "analisa o codigo na tela", "le esse texto da imagem"],
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
        },
        {
            "id": "media-home",
            "title": "Midia e casa",
            "description": "Spotify, YouTube e automacao residencial pela mesma central.",
            "status": "plug-in",
            "tone": "rose",
            "sector": "Entretenimento",
            "icon": "music-4",
            "examples": ["quero ouvir luan santana", "toca meteoro", "status da casa"],
        },
        {
            "id": "memory",
            "title": "Memoria e contexto",
            "description": "Historico de sessao, eventos, notas e contexto persistente.",
            "status": "recording",
            "tone": "sky",
            "sector": "Memoria",
            "icon": "database",
            "examples": ["historico da sessao", "salva no obsidian resumo da reuniao", "status do vault"],
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
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
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

    @app.put("/api/mind/settings")
    def put_mind_settings(payload: MindSettingsPayload) -> dict[str, Any]:
        return _get_mind_runtime().update_settings(payload.settings)

    @app.post("/api/mind/start")
    def post_mind_start() -> dict[str, Any]:
        return _get_mind_runtime().start()

    @app.post("/api/mind/stop")
    def post_mind_stop() -> dict[str, Any]:
        return _get_mind_runtime().stop()

    @app.post("/api/mind/cycle")
    def post_mind_cycle() -> dict[str, Any]:
        return _get_mind_runtime().run_manual_cycle()

    @app.post("/api/mind/rollback")
    def post_mind_rollback() -> dict[str, Any]:
        return _get_mind_runtime().rollback()

    @app.post("/api/mind/proof")
    def post_mind_proof() -> dict[str, Any]:
        return _get_mind_runtime().refresh_proof()

    @app.post("/api/mind/restart/clear")
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

    @app.post("/api/vision/screen/capture")
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

    @app.post("/api/vision/camera/capture")
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

    @app.post("/api/vision/screen/{action}")
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

    @app.post("/api/vision/camera/{action}")
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

    @app.put("/api/settings")
    def put_settings(payload: SettingsPayload) -> dict[str, Any]:
        saved = settings_manager.save(payload.settings)
        return {"settings": saved}

    @app.post("/api/chat")
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

    @app.post("/api/media/analyze")
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
