"""VisionAnalyzer — analisa imagens via GPT-4o Vision.

Modos disponíveis:
  - describe()       → descrição geral do que está na imagem
  - read_text()      → extrai todo o texto visível (OCR inteligente)
  - analyze_code()   → lê e explica código visível na tela
  - find_objects()   → lista objetos/pessoas detectados
  - custom()         → pergunta qualquer coisa sobre a imagem

Todos os métodos aceitam CapturedImage (câmera ou tela) ou path de arquivo.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Union

from openai import OpenAI

from .capture import CapturedImage, CameraCapture, ScreenCapture, load_image_file

log = logging.getLogger("nexus.vision.analyzer")

ImageInput = Union[CapturedImage, str, Path]

# Prompts do JARVIS — respostas diretas, sem enrolação
_PROMPTS = {
    "describe": (
        "Você é o NEXUS, assistente de IA do usuário. "
        "Descreva o que está nesta imagem de forma clara e objetiva, "
        "como um relatório de inteligência. Seja direto. Português brasileiro."
    ),
    "read_text": (
        "Você é o NEXUS. Extraia TODO o texto visível nesta imagem, "
        "preservando a estrutura original (listas, colunas, hierarquia). "
        "Retorne apenas o texto extraído, nada mais. Português brasileiro."
    ),
    "analyze_code": (
        "Você é o NEXUS, especialista em código. "
        "Leia o código visível nesta imagem e: "
        "1. Identifique a linguagem. "
        "2. Explique o que o código faz. "
        "3. Aponte problemas, bugs ou melhorias se houver. "
        "Seja técnico e direto. Português brasileiro."
    ),
    "find_objects": (
        "Você é o NEXUS. Liste todos os objetos, pessoas, elementos de interface "
        "ou itens notáveis visíveis nesta imagem. "
        "Formato: uma linha por item, começando com '-'. Português brasileiro."
    ),
    "watch_camera": (
        "Você é o NEXUS com sistema de visão ativo. "
        "Analise este frame da câmera e relate: "
        "1. O que está acontecendo na cena. "
        "2. Quantas pessoas (se houver) e o que estão fazendo. "
        "3. Algo que mereça atenção do usuário. "
        "Tom de briefing de segurança, direto ao ponto. Português brasileiro."
    ),
}


def _setting(settings, key: str, default):
    if isinstance(settings, dict):
        return settings.get(key, default)
    return getattr(settings, key, default)


class VisionAnalyzer:
    """Analisa imagens usando GPT-4o Vision."""

    def __init__(self, settings, logger: logging.Logger | None = None):
        """
        Args:
            settings: Objeto com:
                - openai_api_key (str)
                - vision_model (str, opcional) — default: gpt-4o
                - vision_max_tokens (int, opcional) — default: 1024
        """
        self.settings = settings
        self.log = logger or log
        self.client = OpenAI(api_key=str(_setting(settings, "openai_api_key", "") or ""))
        self.model: str = str(_setting(settings, "vision_model", "gpt-4o") or "gpt-4o")
        self.max_tokens: int = int(_setting(settings, "vision_max_tokens", 1024) or 1024)

    # ------------------------------------------------------------------
    # Métodos de análise
    # ------------------------------------------------------------------

    def describe(self, source: ImageInput) -> str:
        """Descreve o que está na imagem."""
        return self._analyze(source, _PROMPTS["describe"])

    def read_text(self, source: ImageInput) -> str:
        """Extrai texto da imagem (OCR inteligente)."""
        return self._analyze(source, _PROMPTS["read_text"])

    def analyze_code(self, source: ImageInput) -> str:
        """Lê e explica código visível na tela."""
        return self._analyze(source, _PROMPTS["analyze_code"])

    def find_objects(self, source: ImageInput) -> str:
        """Lista objetos e elementos detectados na imagem."""
        return self._analyze(source, _PROMPTS["find_objects"])

    def watch_camera(self, source: ImageInput) -> str:
        """Analisa frame da câmera como câmera de segurança/situacional."""
        return self._analyze(source, _PROMPTS["watch_camera"])

    def custom(self, source: ImageInput, question: str) -> str:
        """Pergunta qualquer coisa sobre a imagem.

        Args:
            source: Imagem para analisar.
            question: Pergunta em linguagem natural.
        """
        system = (
            "Você é o NEXUS, assistente de IA do usuário. "
            "Responda em português brasileiro com base na imagem fornecida. "
            "Seja direto e objetivo."
        )
        return self._analyze(source, system, question=question)

    # ------------------------------------------------------------------
    # Helpers de captura + análise (atalhos convenientes)
    # ------------------------------------------------------------------

    def describe_screen(self, region=None) -> str:
        """Captura a tela e descreve o que está nela."""
        img = ScreenCapture().capture(region=region)
        return self.describe(img)

    def read_screen_text(self, region=None) -> str:
        """Captura a tela e extrai o texto visível."""
        img = ScreenCapture().capture(region=region)
        return self.read_text(img)

    def analyze_screen_code(self, region=None) -> str:
        """Captura a tela e analisa o código visível."""
        img = ScreenCapture().capture(region=region)
        return self.analyze_code(img)

    def describe_camera(self, camera_index: int = 0) -> str:
        """Captura a câmera e descreve a cena."""
        camera_index = int(_setting(self.settings, "camera_index", camera_index) or camera_index)
        img = CameraCapture(camera_index).capture()
        return self.watch_camera(img)

    def ask_about_screen(self, question: str, region=None) -> str:
        """Captura a tela e responde uma pergunta sobre ela."""
        img = ScreenCapture().capture(region=region)
        return self.custom(img, question)

    def ask_about_camera(self, question: str, camera_index: int = 0) -> str:
        """Captura a câmera e responde uma pergunta sobre ela."""
        camera_index = int(_setting(self.settings, "camera_index", camera_index) or camera_index)
        img = CameraCapture(camera_index).capture()
        return self.custom(img, question)

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------

    def _analyze(
        self,
        source: ImageInput,
        system_prompt: str,
        question: str | None = None,
    ) -> str:
        """Envia imagem + prompt para o GPT-4o Vision e retorna o texto."""
        img = self._resolve_image(source)

        user_content = [img.to_openai_content()]
        if question:
            user_content.append({"type": "text", "text": question})
        else:
            user_content.append({"type": "text", "text": "Analise esta imagem."})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                max_tokens=self.max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content},
                ],
            )
            result = response.choices[0].message.content or ""
            self.log.debug("Vision analysis done: %d chars", len(result))
            return result.strip()

        except Exception as exc:
            self.log.error("Vision API error: %s", exc)
            return f"[NEXUS Vision] Erro ao analisar imagem: {exc}"

    def _resolve_image(self, source: ImageInput) -> CapturedImage:
        """Converte qualquer tipo de entrada em CapturedImage."""
        if isinstance(source, CapturedImage):
            return source
        return load_image_file(source)
