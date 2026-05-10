"""Integração do módulo de visão com o CommandRouter do NEXUS.

Detecta comandos de visão e os roteia para o VisionAnalyzer.
"""
from __future__ import annotations

import logging
import re
import threading
from dataclasses import dataclass
from typing import Callable

from .analyzer import VisionAnalyzer

log = logging.getLogger("nexus.vision_commands")

# ---------------------------------------------------------------------------
# Mapeamento de intenções de visão
# ---------------------------------------------------------------------------

_VISION_INTENTS = [
    # (padrão regex, intent_key)
    (r"o que (está|tem|vejo|aparece|tem) na (tela|monitor|screen)", "describe_screen"),
    (r"descr[ei]v[ae].*(tela|monitor|screen|câmera|camera)", "describe_screen"),
    (r"(lê|leia|extrai|extraia|copiar?).*(texto|texto da tela|screen)", "read_text"),
    (r"(lê|leia|extrai|extraia|text[oa]).*(tela|screen|monitor)", "read_text"),
    (r"(analisa|analise|explica|explique).*(código|code).*(tela|screen)", "analyze_code"),
    (r"(vê|veja|olha|olhe).*(código|code)", "analyze_code"),
    (r"(olha|olhe|vê|veja|ativa|ative).*(câmera|camera|webcam)", "describe_camera"),
    (r"(o que (tem|está|acontece) na câmera|câmera ligada|visão|camera view)", "describe_camera"),
    (r"(detecta|detecte|identifica|identifique|o que.*(tem|está).*(câmera|camera))", "find_objects_camera"),
    (r"(o que|quais|lista|liste).*(objetos|elementos|pessoas).*(tela|screen|câmera|camera)", "find_objects"),
    (r"(quem|quem (está|há).*(tela|câmera|camera))", "find_objects_camera"),
]

_VISION_INTENTS.extend([
    (r"(analisa|analise|explica|explique).*(codigo|code).*(tela|screen)", "analyze_code"),
    (r"(veja|olha|olhe).*(codigo|code)", "analyze_code"),
])

_COMPILED_INTENTS = [
    (re.compile(pat, re.IGNORECASE), key)
    for pat, key in _VISION_INTENTS
]

# Padrão genérico de perguntas sobre a tela
_SCREEN_QUESTION = re.compile(
    r"(o que|por que|como|qual|onde|quando).*(tela|screen|monitor)",
    re.IGNORECASE,
)
_CAMERA_QUESTION = re.compile(
    r"(o que|por que|como|qual|onde|quando).*(câmera|camera|webcam)",
    re.IGNORECASE,
)


def is_vision_command(text: str) -> bool:
    """Retorna True se o texto parece um comando de visão."""
    return any(p.search(text) for p, _ in _COMPILED_INTENTS)


def detect_intent(text: str) -> tuple[str, str]:
    """Retorna (intent_key, question_if_any) para o texto.

    Se for uma pergunta sobre a tela, retorna ('ask_screen', question).
    """
    for pattern, intent in _COMPILED_INTENTS:
        if pattern.search(text):
            return intent, ""

    # Pergunta genérica sobre tela ou câmera
    if _SCREEN_QUESTION.search(text):
        return "ask_screen", text
    if _CAMERA_QUESTION.search(text):
        return "ask_camera", text

    return "describe_screen", ""


# ---------------------------------------------------------------------------
# Resultado retornado ao CommandRouter
# ---------------------------------------------------------------------------

@dataclass
class VisionResult:
    intent: str = "vision"
    label: str = "Visão Computacional"
    args: dict = None

    def __post_init__(self):
        self.args = self.args or {}


# ---------------------------------------------------------------------------
# Handler
# ---------------------------------------------------------------------------

class VisionCommandHandler:
    """Gerencia comandos de visão integrado ao NEXUS."""

    def __init__(
        self,
        settings,
        logger: logging.Logger | None = None,
        ui_callback: Callable[[str], None] | None = None,
    ):
        self.settings = settings
        self.log = logger or log
        self.ui_callback = ui_callback or (lambda msg: print(f"[NEXUS Vision] {msg}"))
        self.analyzer = VisionAnalyzer(settings, logger)

    # ------------------------------------------------------------------
    # API pública — chamada pelo CommandRouter
    # ------------------------------------------------------------------

    def handle(self, raw_text: str) -> VisionResult:
        """Despacha o comando de visão em background e retorna imediatamente."""
        intent, question = detect_intent(raw_text)
        self.log.info("Vision intent detectado: %s | texto: %s", intent, raw_text)

        self.ui_callback("👁️ Sistema de visão ativado...")

        # Roda em thread separada para não travar a UI
        thread = threading.Thread(
            target=self._execute,
            args=(intent, question),
            daemon=True,
            name="nexus-vision",
        )
        thread.start()

        return VisionResult(intent="vision", label="Visão Computacional",
                            args={"intent": intent})

    # ------------------------------------------------------------------
    # Execução dos intents
    # ------------------------------------------------------------------

    def _execute(self, intent: str, question: str) -> None:
        try:
            result = self._dispatch(intent, question)
            self.ui_callback(f"👁️ **Visão NEXUS:**\n\n{result}")
        except Exception as exc:
            self.log.error("Erro no vision handler: %s", exc)
            self.ui_callback(f"⚠️ Erro no sistema de visão: {exc}")

    def _dispatch(self, intent: str, question: str) -> str:
        if intent == "describe_screen":
            self.ui_callback("📷 Capturando tela...")
            return self.analyzer.describe_screen()

        if intent == "read_text":
            self.ui_callback("🔍 Lendo texto na tela...")
            return self.analyzer.read_screen_text()

        if intent == "analyze_code":
            self.ui_callback("💻 Analisando código na tela...")
            return self.analyzer.analyze_screen_code()

        if intent == "describe_camera":
            self.ui_callback("📸 Acessando câmera...")
            return self.analyzer.describe_camera()

        if intent == "find_objects":
            self.ui_callback("🔎 Identificando elementos na tela...")
            from .capture import ScreenCapture
            img = ScreenCapture().capture()
            return self.analyzer.find_objects(img)

        if intent == "find_objects_camera":
            self.ui_callback("🔎 Identificando elementos na câmera...")
            from .capture import CameraCapture
            img = CameraCapture().capture()
            return self.analyzer.find_objects(img)

        if intent == "ask_screen":
            self.ui_callback("🤔 Analisando tela para responder...")
            return self.analyzer.ask_about_screen(question)

        if intent == "ask_camera":
            self.ui_callback("🤔 Consultando câmera...")
            return self.analyzer.ask_about_camera(question)

        # Fallback
        return self.analyzer.describe_screen()
