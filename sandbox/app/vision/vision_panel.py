"""VisionPanel — painel HUD de visão para a UI CustomTkinter do NEXUS.

Adiciona uma aba "👁️ Visão" com:
  - Preview ao vivo da câmera (atualizado a cada N ms)
  - Preview da tela capturada
  - Botões de análise rápida
  - Resultado da análise exibido em tempo real

Como usar na ui/desktop_app.py:
    from app.vision.vision_panel import VisionPanel
    vision_tab = self.tabview.add("👁️ Visão")
    self.vision_panel = VisionPanel(vision_tab, settings, on_result=self.append_message)
    self.vision_panel.pack(fill="both", expand=True)
"""
from __future__ import annotations

import base64
import io
import logging
import threading
import tkinter as tk
from typing import Callable

log = logging.getLogger("nexus.vision.panel")

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False

try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def _setting(settings, key: str, default):
    if isinstance(settings, dict):
        return settings.get(key, default)
    return getattr(settings, key, default)


class VisionPanel(ctk.CTkFrame if CTK_AVAILABLE else tk.Frame):  # type: ignore
    """Painel de visão computacional para a UI do NEXUS."""

    PREVIEW_W = 320
    PREVIEW_H = 180
    CAMERA_REFRESH_MS = 150   # intervalo de atualização do preview ao vivo

    def __init__(
        self,
        parent,
        settings,
        on_result: Callable[[str], None] | None = None,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self.settings = settings
        self.on_result = on_result or (lambda msg: None)
        self._camera_running = False
        self._camera_thread: threading.Thread | None = None
        self._after_id: str | None = None

        # Importações lazy para não quebrar se as libs não estiverem instaladas
        self._init_capture()
        self._build_ui()

    # ------------------------------------------------------------------
    # Inicialização
    # ------------------------------------------------------------------

    def _init_capture(self):
        try:
            from .capture import ScreenCapture, CameraCapture
            from .analyzer import VisionAnalyzer
            self.screen_cap = ScreenCapture()
            self.cam_cap = CameraCapture(
                camera_index=int(_setting(self.settings, "camera_index", 0) or 0)
            )
            self.analyzer = VisionAnalyzer(self.settings)
            self._vision_ok = True
        except Exception as exc:
            log.error("Vision init error: %s", exc)
            self._vision_ok = False

    def _build_ui(self):
        if not CTK_AVAILABLE:
            log.warning("CustomTkinter não disponível. VisionPanel desativado.")
            return

        # ── Coluna esquerda: previews ──────────────────────────────────
        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", fill="y", padx=8, pady=8)

        # Preview câmera
        cam_label = ctk.CTkLabel(left, text="📷 Câmera ao vivo",
                                 font=ctk.CTkFont(size=12, weight="bold"))
        cam_label.pack(anchor="w")

        self._cam_preview = ctk.CTkLabel(
            left, text="[câmera desativada]",
            width=self.PREVIEW_W, height=self.PREVIEW_H,
            fg_color=("#1a1a2e", "#0f0f1a"), corner_radius=8,
        )
        self._cam_preview.pack(pady=(4, 8))

        cam_btns = ctk.CTkFrame(left, fg_color="transparent")
        cam_btns.pack(fill="x")
        self._btn_cam_start = ctk.CTkButton(
            cam_btns, text="▶ Ligar câmera", width=120,
            command=self._start_camera,
            fg_color="#1565C0", hover_color="#0D47A1",
        )
        self._btn_cam_start.pack(side="left", padx=2)
        self._btn_cam_stop = ctk.CTkButton(
            cam_btns, text="⏹ Parar", width=90,
            command=self._stop_camera, state="disabled",
            fg_color="#37474F", hover_color="#263238",
        )
        self._btn_cam_stop.pack(side="left", padx=2)

        # Preview tela
        screen_label = ctk.CTkLabel(left, text="🖥️ Tela capturada",
                                    font=ctk.CTkFont(size=12, weight="bold"))
        screen_label.pack(anchor="w", pady=(12, 0))

        self._screen_preview = ctk.CTkLabel(
            left, text="[clique em Capturar Tela]",
            width=self.PREVIEW_W, height=self.PREVIEW_H,
            fg_color=("#1a1a2e", "#0f0f1a"), corner_radius=8,
        )
        self._screen_preview.pack(pady=(4, 8))

        ctk.CTkButton(
            left, text="📸 Capturar tela", width=150,
            command=self._capture_screen,
            fg_color="#1565C0", hover_color="#0D47A1",
        ).pack()

        # ── Coluna direita: botões + resultado ────────────────────────
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        ctk.CTkLabel(right, text="⚡ Análise rápida",
                     font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")

        btn_data = [
            ("🔍 Descrever tela",       self._analyze_describe),
            ("📝 Extrair texto",         self._analyze_read_text),
            ("💻 Analisar código",       self._analyze_code),
            ("👁️ Objetos na tela",      self._analyze_objects),
            ("🎥 Analisar câmera",       self._analyze_camera),
        ]
        for label, cmd in btn_data:
            ctk.CTkButton(
                right, text=label, anchor="w", height=36,
                command=cmd,
                fg_color="#0D2137", hover_color="#1565C0",
            ).pack(fill="x", pady=2)

        # Campo de pergunta customizada
        ctk.CTkLabel(right, text="💬 Pergunta sobre a tela:",
                     font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(12, 2))
        self._question_entry = ctk.CTkEntry(
            right, placeholder_text="ex: o que esse gráfico mostra?", height=36
        )
        self._question_entry.pack(fill="x")
        self._question_entry.bind("<Return>", lambda _: self._analyze_custom())

        ctk.CTkButton(
            right, text="Perguntar →", height=32,
            command=self._analyze_custom,
            fg_color="#1565C0", hover_color="#0D47A1",
        ).pack(fill="x", pady=4)

        # Resultado
        ctk.CTkLabel(right, text="📋 Resultado:",
                     font=ctk.CTkFont(size=11)).pack(anchor="w", pady=(10, 2))
        self._result_box = ctk.CTkTextbox(right, height=200, wrap="word",
                                          font=ctk.CTkFont(family="Consolas", size=12))
        self._result_box.pack(fill="both", expand=True)
        self._result_box.configure(state="disabled")

        # Status bar
        self._status_var = tk.StringVar(value="Sistema de visão pronto.")
        ctk.CTkLabel(right, textvariable=self._status_var,
                     font=ctk.CTkFont(size=10),
                     text_color=("gray50", "gray60")).pack(anchor="w", pady=(4, 0))

    # ------------------------------------------------------------------
    # Câmera ao vivo
    # ------------------------------------------------------------------

    def _start_camera(self):
        if self._camera_running or not self._vision_ok:
            return
        self._camera_running = True
        self._btn_cam_start.configure(state="disabled")
        self._btn_cam_stop.configure(state="normal")
        self._update_camera_preview()

    def _stop_camera(self):
        self._camera_running = False
        self._btn_cam_start.configure(state="normal")
        self._btn_cam_stop.configure(state="disabled")
        if self._after_id:
            self.after_cancel(self._after_id)

    def _update_camera_preview(self):
        """Atualiza o preview da câmera a cada CAMERA_REFRESH_MS ms."""
        if not self._camera_running:
            return
        try:
            img_data = self.cam_cap.capture(warmup_frames=0)
            self._set_preview(self._cam_preview, img_data.base64_data)
        except Exception as exc:
            log.debug("Camera preview error: %s", exc)
        self._after_id = self.after(self.CAMERA_REFRESH_MS, self._update_camera_preview)

    # ------------------------------------------------------------------
    # Captura e análise
    # ------------------------------------------------------------------

    def _capture_screen(self):
        self._set_status("Capturando tela...")
        def _do():
            try:
                img = self.screen_cap.capture()
                self._set_preview(self._screen_preview, img.base64_data)
                self._set_status("Tela capturada.")
            except Exception as exc:
                self._set_status(f"Erro: {exc}")
        threading.Thread(target=_do, daemon=True).start()

    def _analyze_describe(self):
        self._run_analysis("Descrevendo tela...", lambda: self.analyzer.describe_screen())

    def _analyze_read_text(self):
        self._run_analysis("Extraindo texto...", lambda: self.analyzer.read_screen_text())

    def _analyze_code(self):
        self._run_analysis("Analisando código...", lambda: self.analyzer.analyze_screen_code())

    def _analyze_objects(self):
        def _fn():
            img = self.screen_cap.capture()
            return self.analyzer.find_objects(img)
        self._run_analysis("Identificando objetos...", _fn)

    def _analyze_camera(self):
        self._run_analysis("Analisando câmera...", lambda: self.analyzer.describe_camera())

    def _analyze_custom(self):
        question = self._question_entry.get().strip()
        if not question:
            return
        self._run_analysis(
            f"Analisando: \"{question[:40]}...\"",
            lambda: self.analyzer.ask_about_screen(question),
        )

    def _run_analysis(self, status_msg: str, fn):
        """Roda fn() em thread, atualiza status e exibe resultado."""
        if not self._vision_ok:
            self._set_result("⚠️ Sistema de visão não inicializado corretamente.")
            return
        self._set_status(f"👁️ {status_msg}")
        self._set_result("Analisando...")

        def _worker():
            try:
                result = fn()
                self._set_result(result)
                self._set_status("✅ Análise concluída.")
                self.on_result(f"👁️ **NEXUS Vision:**\n\n{result}")
            except Exception as exc:
                self._set_result(f"Erro: {exc}")
                self._set_status(f"⚠️ Erro: {exc}")

        threading.Thread(target=_worker, daemon=True).start()

    # ------------------------------------------------------------------
    # Utilitários de UI
    # ------------------------------------------------------------------

    def _set_preview(self, label_widget, b64_data: str):
        """Atualiza um label com imagem base64 redimensionada."""
        if not PIL_AVAILABLE:
            return
        try:
            raw = base64.b64decode(b64_data)
            pil_img = Image.open(io.BytesIO(raw))
            pil_img.thumbnail((self.PREVIEW_W, self.PREVIEW_H))
            tk_img = ImageTk.PhotoImage(pil_img)
            # Precisa rodar na thread principal
            label_widget.after(0, lambda: self._apply_image(label_widget, tk_img))
        except Exception as exc:
            log.debug("Preview update error: %s", exc)

    @staticmethod
    def _apply_image(label, img):
        label.configure(image=img, text="")
        label._image_ref = img   # evita garbage collection

    def _set_result(self, text: str):
        def _do():
            self._result_box.configure(state="normal")
            self._result_box.delete("1.0", "end")
            self._result_box.insert("end", text)
            self._result_box.configure(state="disabled")
        self.after(0, _do)

    def _set_status(self, msg: str):
        self.after(0, lambda: self._status_var.set(msg))

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def destroy(self):
        self._stop_camera()
        super().destroy()
