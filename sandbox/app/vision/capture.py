"""Captura de imagens: tela e câmera.

- ScreenCapture  → captura a tela inteira ou uma região usando PIL/pyautogui
- CameraCapture  → captura frame da webcam usando OpenCV
"""
from __future__ import annotations

import base64
import io
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

log = logging.getLogger("nexus.vision.capture")


# ---------------------------------------------------------------------------
# Tipo de retorno comum
# ---------------------------------------------------------------------------

@dataclass
class CapturedImage:
    """Imagem capturada pronta para enviar à API de visão."""
    base64_data: str          # Imagem em base64 (JPEG)
    media_type: str = "image/jpeg"
    width: int = 0
    height: int = 0
    source: str = ""          # "screen" | "camera" | "file"

    def to_openai_content(self) -> dict:
        """Formata para o campo content da API OpenAI (vision)."""
        return {
            "type": "image_url",
            "image_url": {
                "url": f"data:{self.media_type};base64,{self.base64_data}",
                "detail": "high",
            },
        }


# ---------------------------------------------------------------------------
# Captura de tela
# ---------------------------------------------------------------------------

class ScreenCapture:
    """Captura a tela usando PIL (via mss ou pyautogui, ambos já no projeto)."""

    def __init__(self, quality: int = 85, max_dimension: int = 1920):
        """
        Args:
            quality: Qualidade JPEG 1-95 (menor = menor payload).
            max_dimension: Redimensiona se maior que este valor.
        """
        self.quality = quality
        self.max_dimension = max_dimension

    def capture(self, region: Tuple[int, int, int, int] | None = None) -> CapturedImage:
        """Captura a tela inteira ou uma região.

        Args:
            region: (left, top, width, height) em pixels. None = tela inteira.

        Returns:
            CapturedImage pronta para análise.
        """
        try:
            from PIL import ImageGrab
        except ImportError:
            raise RuntimeError("Pillow não instalado. Execute: pip install Pillow")

        img = ImageGrab.grab(bbox=region)   # bbox=None → tela inteira

        # Redimensiona se necessário para não explodir o payload
        img = self._resize_if_needed(img)

        # Converte para base64 JPEG
        buf = io.BytesIO()
        img.convert("RGB").save(buf, format="JPEG", quality=self.quality)
        b64 = base64.b64encode(buf.getvalue()).decode()

        log.debug("Screen captured: %dx%d → %d bytes b64", img.width, img.height, len(b64))
        return CapturedImage(
            base64_data=b64,
            width=img.width,
            height=img.height,
            source="screen",
        )

    def capture_window(self, title_contains: str) -> CapturedImage:
        """Captura a janela cujo título contém `title_contains`."""
        try:
            import pygetwindow as gw
        except ImportError:
            log.warning("pygetwindow não disponível, capturando tela inteira.")
            return self.capture()

        wins = gw.getWindowsWithTitle(title_contains)
        if not wins:
            log.warning("Janela '%s' não encontrada. Capturando tela inteira.", title_contains)
            return self.capture()

        win = wins[0]
        region = (win.left, win.top, win.width, win.height)
        return self.capture(region=(win.left, win.top, win.left + win.width, win.top + win.height))

    # ------------------------------------------------------------------
    def _resize_if_needed(self, img):
        from PIL import Image
        w, h = img.size
        if max(w, h) <= self.max_dimension:
            return img
        ratio = self.max_dimension / max(w, h)
        new_w, new_h = int(w * ratio), int(h * ratio)
        return img.resize((new_w, new_h), Image.LANCZOS)


# ---------------------------------------------------------------------------
# Captura de câmera
# ---------------------------------------------------------------------------

class CameraCapture:
    """Captura frames da webcam usando OpenCV."""

    def __init__(self, camera_index: int = 0, quality: int = 85):
        """
        Args:
            camera_index: Índice da câmera (0 = câmera padrão).
            quality: Qualidade JPEG 1-95.
        """
        self.camera_index = camera_index
        self.quality = quality

    def capture(self, warmup_frames: int = 3) -> CapturedImage:
        """Abre a câmera, captura um frame e fecha.

        Args:
            warmup_frames: Frames descartados antes de capturar (estabilização).

        Returns:
            CapturedImage pronta para análise.

        Raises:
            RuntimeError: Se a câmera não puder ser acessada.
        """
        try:
            import cv2
        except ImportError:
            raise RuntimeError(
                "OpenCV não instalado. Execute: pip install opencv-python"
            )

        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError(
                f"Câmera {self.camera_index} não encontrada ou está em uso."
            )

        try:
            # Descarta frames iniciais (câmera ainda ajustando exposição)
            for _ in range(warmup_frames):
                cap.read()

            ret, frame = cap.read()
            if not ret or frame is None:
                raise RuntimeError("Não foi possível capturar frame da câmera.")

            # Converte BGR → JPEG em memória
            encode_params = [cv2.IMWRITE_JPEG_QUALITY, self.quality]
            _, buf = cv2.imencode(".jpg", frame, encode_params)
            b64 = base64.b64encode(buf.tobytes()).decode()

            h, w = frame.shape[:2]
            log.debug("Camera frame captured: %dx%d → %d bytes b64", w, h, len(b64))
            return CapturedImage(
                base64_data=b64,
                width=w,
                height=h,
                source="camera",
            )
        finally:
            cap.release()

    def list_cameras(self) -> list[int]:
        """Retorna índices das câmeras disponíveis no sistema."""
        try:
            import cv2
        except ImportError:
            return []

        available = []
        for i in range(5):  # testa até 5 câmeras
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                available.append(i)
                cap.release()
        return available

    def save_snapshot(self, path: str | Path, warmup_frames: int = 3) -> Path:
        """Captura e salva um snapshot em disco.

        Args:
            path: Caminho do arquivo de saída (.jpg).
            warmup_frames: Frames de aquecimento.

        Returns:
            Path do arquivo salvo.
        """
        img = self.capture(warmup_frames=warmup_frames)
        out = Path(path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(base64.b64decode(img.base64_data))
        log.info("Snapshot salvo: %s", out)
        return out


# ---------------------------------------------------------------------------
# Utilitário: carregar imagem de arquivo
# ---------------------------------------------------------------------------

def load_image_file(path: str | Path, quality: int = 85) -> CapturedImage:
    """Carrega uma imagem de disco e converte para CapturedImage."""
    try:
        from PIL import Image
    except ImportError:
        raise RuntimeError("Pillow não instalado.")

    img = Image.open(path).convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return CapturedImage(
        base64_data=b64,
        width=img.width,
        height=img.height,
        source=str(path),
    )
