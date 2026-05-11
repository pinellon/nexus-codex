from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict
from queue import Empty, Queue
from typing import Any, Callable

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

import app.settings_manager as settings_manager
from app.chat.chat_engine import ChatEngine
from app.chat.chat_handler import ChatHandler
from app.config import BASE_DIR
from app.features.project_health import analyze_project
from app.features.session_recorder import SessionRecorder
from app.logger import get_recent_logs

LOGGER = logging.getLogger("nexus.web")
SESSION_PATH = BASE_DIR / "data" / "session_events.jsonl"


class SilentSpeaker:
    def speak(self, _text: str) -> None:
        return None


class ChatRequest(BaseModel):
    text: str = Field(default="", min_length=1)
    confirm: bool = False


class SettingsPayload(BaseModel):
    settings: dict[str, Any] = Field(default_factory=dict)


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
            "title": "Chat Core",
            "description": "Pipeline natural conectado ao roteador principal.",
            "status": "online",
            "tone": "cyan",
        },
        {
            "id": "coder",
            "title": "Coder",
            "description": "Editor, patching, git e assistencia a codigo.",
            "status": "ready",
            "tone": "amber",
        },
        {
            "id": "vision",
            "title": "Vision",
            "description": "OCR, camera e analise visual orientada a prompt.",
            "status": "ready",
            "tone": "lime",
        },
        {
            "id": "automation",
            "title": "Automation",
            "description": "Desktop, browser, media e acoes de sistema.",
            "status": "guarded",
            "tone": "orange",
        },
        {
            "id": "home",
            "title": "Home",
            "description": "Home Assistant e Spotify pela mesma interface.",
            "status": "plug-in",
            "tone": "rose",
        },
        {
            "id": "memory",
            "title": "Memory",
            "description": "Eventos de sessao, Obsidian e contexto persistente.",
            "status": "recording",
            "tone": "sky",
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
    def get_logs(limit: int = Query(default=80, ge=1, le=500)) -> dict[str, Any]:
        return {"items": get_recent_logs(limit)}

    @app.get("/api/events/recent")
    def get_recent_events(limit: int = Query(default=30, ge=1, le=120)) -> dict[str, Any]:
        return {"items": [asdict(item) for item in recorder.tail(limit)]}

    @app.get("/api/settings")
    def get_settings() -> dict[str, Any]:
        return {"settings": settings_manager.load()}

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
