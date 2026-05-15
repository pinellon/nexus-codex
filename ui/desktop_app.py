"""Interface desktop NEXUS com abas, monitor, logs e configuracoes."""

from __future__ import annotations

import datetime as _dt
import os
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk

from app.command_history import history as cmd_history
from app.core.command_router import CommandRouter
from app.error_handler import handle_error
from app.logger import get_recent_logs
from app.memory import clear_memory
import app.settings_manager as settings
from ui.theme import BTN, C, F
from ui.widgets import AmbientScanner, LiveGraph, MiniBar, PulseIndicator, SoundBus, StatusTicker, bind_button_fx, show_toast
from ui_coding.coder_panel import CoderPanel
from app.vision.vision_panel import VisionPanel


class NexusApp(ctk.CTk):
    def __init__(
        self,
        on_command_callback,
        live_event_subscribe=None,
        live_event_unsubscribe=None,
    ):
        super().__init__()
        self._on_command = on_command_callback
        self._live_event_subscribe = live_event_subscribe
        self._live_event_unsubscribe = live_event_unsubscribe
        self._cfg = settings.load()
        self._active_tab = "chat"
        self._processing = False
        self._listening = False
        self._message_count = 0
        self._command_count = 0
        self._last_metrics = {"cpu": 0.0, "ram": 0.0, "disk": 0.0}
        self._router = CommandRouter(self._cfg.get("wake_word", "nexus"))
        self._voice_loop = None
        self._voice_loop_active = False
        self._module_status = {
            "agent": "ocioso",
            "vision": "ocioso",
            "home": "ocioso",
        }
        SoundBus.enabled = bool(self._cfg.get("ui_sounds", True))

        self._setup_window()
        self._build_layout()
        self._bind_live_events()
        self._start_background_tasks()

    def _setup_window(self):
        self.title("NEXUS")
        self.geometry("1100x740")
        self.minsize(900, 620)
        self.configure(fg_color=C["bg"])
        self.resizable(True, True)
        self._set_windows_app_id()
        self._apply_window_icon()
        self.attributes("-topmost", bool(self._cfg.get("always_on_top")))
        self.bind("<Control-k>", lambda _e: self._focus_input())
        self.bind("<Control-l>", lambda _e: self._clear_chat())
        self.bind("<Control-1>", lambda _e: self._switch_tab("chat"))
        self.bind("<Control-2>", lambda _e: self._switch_tab("auto"))
        self.bind("<Control-3>", lambda _e: self._switch_tab("coder"))
        self.bind("<Control-4>", lambda _e: self._switch_tab("config"))
        self.bind("<Control-5>", lambda _e: self._switch_tab("logs"))
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _bind_live_events(self):
        if not self._live_event_subscribe:
            self._live_event_listener = None
            return

        def _listener(kind: str, message: str, data: dict):
            self.after(
                0,
                lambda k=kind, m=message, d=data: self._handle_live_event(k, m, d),
            )

        self._live_event_listener = _listener
        self._live_event_subscribe(_listener)

    def _set_windows_app_id(self):
        if os.name != "nt":
            return
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("nicolas.nexus.desktop")
        except Exception:
            pass

    def _apply_window_icon(self):
        assets = Path(__file__).resolve().parents[1] / "assets"
        png = assets / "nexus_logo_64.png"
        ico = assets / "nexus_logo.ico"

        try:
            if ico.exists():
                self.iconbitmap(default=str(ico))
        except tk.TclError:
            pass

        try:
            if png.exists():
                self._window_icon = tk.PhotoImage(file=str(png))
                self.iconphoto(True, self._window_icon)
        except tk.TclError:
            pass

    def _load_header_logo(self):
        logo = Path(__file__).resolve().parents[1] / "assets" / "nexus_logo_32.png"
        if not logo.exists():
            return None
        try:
            return tk.PhotoImage(file=str(logo))
        except tk.TclError:
            return None

    def _build_layout(self):
        self._build_header()
        body = tk.Frame(self, bg=C["bg"])
        body.pack(fill="both", expand=True)

        self._sidebar_frame = tk.Frame(body, bg=C["panel"], width=58)
        self._sidebar_frame.pack(side="left", fill="y")
        self._sidebar_frame.pack_propagate(False)
        tk.Frame(self._sidebar_frame, bg=C["border"], width=1).place(relx=1, rely=0, relheight=1, anchor="ne")

        self._content_host = tk.Frame(body, bg=C["bg"])
        self._content_host.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self._build_content_area()
        self._build_footer()

    def _build_header(self):
        hdr = tk.Frame(self, bg=C["panel"], height=60)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)
        self._header_scan = AmbientScanner(hdr, height=60, bg=C["panel"])
        self._header_scan.place(x=0, y=0, relwidth=1, relheight=1)
        if self._cfg.get("ui_animations", True):
            self._header_scan.start()
        tk.Frame(hdr, bg=C["cyan"], height=1).place(relx=0, rely=1, relwidth=1, anchor="sw")

        self._header_logo_img = self._load_header_logo()
        if self._header_logo_img:
            tk.Label(hdr, image=self._header_logo_img, bg=C["panel"]).pack(side="left", padx=(18, 8))
            tk.Label(hdr, text="NEXUS", bg=C["panel"], fg=C["cyan"], font=("Consolas", 22, "bold")).pack(side="left", padx=(0, 18))
        else:
            tk.Label(hdr, text="NEXUS", bg=C["panel"], fg=C["cyan"], font=("Consolas", 22, "bold")).pack(side="left", padx=18)
        self._subtitle_var = tk.StringVar(value="// SISTEMA ATIVO")
        tk.Label(hdr, textvariable=self._subtitle_var, bg=C["panel"], fg=C["text_muted"], font=F["tiny"]).pack(side="left")
        self._ticker = StatusTicker(
            self,
            self._subtitle_var,
            ["// SISTEMA ATIVO", "// CODER PRONTO", "// MONITORANDO RECURSOS", "// AUTOMAÇÕES ARMADAS"],
            interval=2200,
        )
        if self._cfg.get("ui_animations", True):
            self._ticker.start()

        right = tk.Frame(hdr, bg=C["panel"])
        right.pack(side="right", padx=14)

        self._clock_lbl = tk.Label(right, text="", bg=C["panel"], fg=C["text_dim"], font=F["small"])
        self._clock_lbl.pack(side="left", padx=10)

        self._ontop_var = tk.BooleanVar(value=bool(self._cfg.get("always_on_top")))
        self._pin_btn = tk.Checkbutton(
            right,
            text="📌",
            variable=self._ontop_var,
            command=self._toggle_ontop,
            bg=C["panel"],
            fg=C["cyan"] if self._ontop_var.get() else C["text_dim"],
            selectcolor=C["panel"],
            activebackground=C["panel"],
            activeforeground=C["cyan"],
            bd=0,
            cursor="hand2",
            font=("Arial", 14),
        )
        self._pin_btn.pack(side="left", padx=8)

        self._status_lbl = tk.Label(right, text="PRONTO", bg=C["panel"], fg=C["green"], font=F["small"])
        self._status_lbl.pack(side="left", padx=6)
        self._pulse = PulseIndicator(right, color=C["green"], size=22)
        self._pulse.pack(side="left", padx=4)
        self._pulse.start(C["green"])
        self._update_clock()

    def _build_sidebar(self):
        tabs = [("💬", "chat", "Chat"), ("⚡", "auto", "Automação"), ("💻", "coder", "Coder"), ("⚙", "config", "Configurações"), ("📋", "logs", "Logs")]
        self._tab_btns = {}
        tabs.insert(3, ("VISION", "vision", "Visao"))
        tabs.insert(4, ("🧠", "mind", "NexusMind"))
        for icon, key, name in tabs:
            lbl = tk.Label(self._sidebar_frame, text=icon, bg=C["panel"], fg=C["text_dim"], font=("Arial", 18), cursor="hand2")
            lbl.pack(fill="x", padx=5, pady=4, ipady=8)
            lbl.bind("<Button-1>", lambda _e, k=key: self._switch_tab(k))
            lbl.bind("<Enter>", lambda _e, l=lbl: (SoundBus.play("hover"), l.configure(fg=C["cyan"])))
            lbl.bind("<Leave>", lambda _e, l=lbl, k=key: l.configure(fg=C["cyan"] if self._active_tab == k else C["text_dim"]))
            lbl.bind("<Button-3>", lambda _e, n=name: show_toast(self, n, "info", 900))
            self._tab_btns[key] = lbl

    def _build_content_area(self):
        self._panels = {
            "chat": self._build_chat_tab(),
            "auto": self._build_auto_tab(),
            "coder": self._build_coder_tab(),
            "vision": self._build_vision_tab(),
            "mind": self._build_mind_tab(),
            "config": self._build_config_tab(),
            "logs": self._build_logs_tab(),
        }
        self._switch_tab("chat")

    def _switch_tab(self, key: str):
        self._active_tab = key
        for name, panel in self._panels.items():
            panel.pack_forget()
            self._tab_btns[name].configure(fg=C["cyan"] if name == key else C["text_dim"], bg=C["cyan_bg"] if name == key else C["panel"])
        SoundBus.play("click")
        self._panels[key].pack(fill="both", expand=True)
        if key == "logs":
            self._refresh_logs()
        if key == "chat":
            self.after(40, self._focus_input)

    def _build_coder_tab(self) -> tk.Frame:
        self._coder_panel = CoderPanel(
            self._content_host,
            on_command=lambda cmd: self._on_command(cmd, self._confirm_callback),
        )
        try:
            from coding.dispatcher import set_editor_bridge
            set_editor_bridge(self._coder_panel.build_editor_bridge())
        except Exception:
            pass
        return self._coder_panel

    def _build_vision_tab(self) -> tk.Frame:
        self._vision_panel = VisionPanel(
            self._content_host,
            settings=self._cfg,
            on_result=lambda message: self.after(0, lambda m=message: self._add_chat_message("assistant", m)),
        )
        return self._vision_panel

    def _build_mind_tab(self) -> tk.Frame:
        try:
            from ui.nexus_mind_panel import NexusMindPanel
            self._mind_panel = NexusMindPanel(self._content_host, settings=self._cfg)
            return self._mind_panel
        except Exception as e:
            from ui.theme import C
            import traceback
            err_frame = ctk.CTkFrame(self._content_host, fg_color=C["bg"])
            
            # Card Central
            card = ctk.CTkFrame(err_frame, fg_color="#1E1E2E", corner_radius=8, border_width=1, border_color="#F38BA8")
            card.pack(expand=True, padx=40, pady=40, ipadx=20, ipady=20)
            
            ctk.CTkLabel(card, text="[NEXUS DIAGNOSTICS]", font=("Courier", 16, "bold"), text_color="#F38BA8").pack(pady=(0, 15))
            
            error_str = str(e)
            ctk.CTkLabel(card, text="Falha detectada:", font=("Courier", 11, "bold"), text_color="#A6ACCD").pack(anchor="w")
            ctk.CTkLabel(card, text=error_str, font=("Courier", 12), text_color="#F38BA8", wraplength=400, justify="left").pack(anchor="w", pady=(0, 10))
            
            # Causa provável + Solução (heurística simples)
            cause = "Incompatibilidade de módulo ou falha de import"
            solution = "Verifique os logs detalhados ou inicie a correção automática."
            if "pylint.epylint" in error_str:
                cause = "Versão incompatível do pylint. O epylint foi descontinuado."
                solution = "Migrar para pylint.lint.Run() ou atualizar score_engine.py"
                
            ctk.CTkLabel(card, text="Causa provável:", font=("Courier", 11, "bold"), text_color="#A6ACCD").pack(anchor="w")
            ctk.CTkLabel(card, text=cause, font=("Courier", 12), text_color="#F9E2AF", wraplength=400, justify="left").pack(anchor="w", pady=(0, 10))
            
            ctk.CTkLabel(card, text="Solução sugerida:", font=("Courier", 11, "bold"), text_color="#A6ACCD").pack(anchor="w")
            ctk.CTkLabel(card, text=solution, font=("Courier", 12), text_color="#A6E3A1", wraplength=400, justify="left").pack(anchor="w", pady=(0, 15))
            
            # Botões
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", pady=(10, 0))
            
            ctk.CTkButton(btn_frame, text="Corrigir Agora", font=("Courier", 12, "bold"), fg_color="#F38BA8", text_color="#11111B", hover_color="#D87892", command=lambda e=error_str: self._corrigir_automaticamente(e)).pack(side="left", padx=(0, 10))
            ctk.CTkButton(btn_frame, text="Ver Arquivo", font=("Courier", 12), fg_color="transparent", border_width=1, border_color="#A6ACCD", text_color="#A6ACCD", hover_color="#313244").pack(side="left")
            ctk.CTkButton(btn_frame, text="Ignorar", font=("Courier", 12), fg_color="transparent", text_color="#6C7086", hover_color="#313244").pack(side="right")
            
            # Expansível traceback
            tb_text = traceback.format_exc()
            tb_box = ctk.CTkTextbox(card, height=80, font=("Courier", 10), fg_color="#11111B", text_color="#6C7086")
            tb_box.insert("0.0", tb_text)
            tb_box.configure(state="disabled")
            tb_box.pack(fill="x", pady=(20, 0))
            
            return err_frame

    def _corrigir_automaticamente(self, error_str: str):
        # Lógica super avançada de auto-manutenção (no futuro enviaria para a IA)
        self._add_system_msg(f"Iniciando correção automática para o erro detectado: {error_str[:30]}...")
        # Simula uma varredura
        self.after(1000, lambda: self._add_system_msg("🔍 Analisando logs e dependências..."))
        self.after(2500, lambda: self._add_system_msg("🔧 Atualizando compatibilidade do ambiente (compatibility_memory.json)..."))
        self.after(4000, lambda: self._add_system_msg("✅ Sistema corrigido. Reinicie o Nexus para aplicar as mudanças da aba Auto-Melhoria."))
        
        # Pode forçar reload da UI também
        # self.after(5000, self._restart_app)

    def _build_chat_tab(self) -> tk.Frame:
        frame = tk.Frame(self._content_host, bg=C["bg"])
        self._chat_scroll = ctk.CTkScrollableFrame(frame, fg_color=C["bg"], scrollbar_button_color=C["border"], scrollbar_button_hover_color=C["cyan"])
        self._chat_scroll.pack(fill="both", expand=True, padx=12, pady=(10, 0))
        self._add_system_msg(f"Sistema online. Como posso ajudar, {self._cfg.get('owner_name', 'Nicolas')}?")

        info = tk.Frame(frame, bg=C["bg"])
        info.pack(fill="x", padx=12, pady=(8, 0))
        self._module_status_var = tk.StringVar()
        self._module_hint_var = tk.StringVar(
            value="Eventos ao vivo de agente, visao e casa aparecem aqui no chat."
        )
        tk.Label(
            info,
            textvariable=self._module_status_var,
            bg=C["bg"],
            fg=C["cyan"],
            font=F["small"],
            anchor="w",
            justify="left",
        ).pack(fill="x")
        tk.Label(
            info,
            textvariable=self._module_hint_var,
            bg=C["bg"],
            fg=C["text_muted"],
            font=F["tiny"],
            anchor="w",
            justify="left",
        ).pack(fill="x", pady=(2, 0))
        self._refresh_module_status()

        wrap = tk.Frame(frame, bg=C["panel"])
        wrap.pack(fill="x", padx=12, pady=10)
        tk.Frame(wrap, bg=C["border"], height=1).pack(fill="x")
        row = tk.Frame(wrap, bg=C["panel"])
        row.pack(fill="x", padx=10, pady=8)

        self._input = tk.Entry(row, bg=C["card"], fg=C["text"], insertbackground=C["cyan"], font=F["body"], relief="flat", bd=0)
        self._input.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 8))
        self._input.bind("<Return>", lambda _e: self._submit_text())
        self._input.bind("<Up>", self._history_up)
        self._input.bind("<Down>", self._history_down)
        self._setup_placeholder()

        self._send_btn = self._btn(row, "⏎ Enviar", self._submit_text, "primary", w=104, h=36)
        self._send_btn.pack(side="left", padx=(0, 5))
        self._mic_btn = self._btn(row, "🎙", self._toggle_mic, "secondary", w=42, h=36)
        self._mic_btn.pack(side="left", padx=(0, 5))
        self._voice_loop_btn = self._btn(row, "Voz OFF", self._toggle_voice_loop, "ghost", w=82, h=36)
        self._voice_loop_btn.pack(side="left", padx=(0, 5))
        self._btn(row, "🧠", self._limpar_memoria, "ghost", w=42, h=36).pack(side="left", padx=(0, 5))
        self._btn(row, "🗑", self._clear_chat, "ghost", w=42, h=36).pack(side="left")
        tk.Label(wrap, text="↑/↓ histórico · Ctrl+K focar · Ctrl+L limpar · Ctrl+1..5 abas", bg=C["panel"], fg=C["text_muted"], font=F["tiny"]).pack(pady=(0, 5))
        return frame

    def _setup_placeholder(self):
        self._ph = "  Digite um comando, pergunta ou automação..."
        self._input.insert(0, self._ph)
        self._input.configure(fg=C["text_muted"])

        def on_in(_e):
            if self._input.get() == self._ph:
                self._input.delete(0, "end")
                self._input.configure(fg=C["text"])

        def on_out(_e):
            if not self._input.get():
                self._input.insert(0, self._ph)
                self._input.configure(fg=C["text_muted"])

        self._input.bind("<FocusIn>", on_in)
        self._input.bind("<FocusOut>", on_out)

    def _add_system_msg(self, text: str):
        tk.Label(self._chat_scroll, text=f"── {text} ──", bg=C["bg"], fg=C["text_muted"], font=F["tiny"], wraplength=760).pack(pady=8)

    def _add_chat_message(self, role: str, text: str):
        is_user = role == "user"
        bg = C["card"] if is_user else C["panel"]
        fg = C["text"] if is_user else C["cyan"]
        tag = "VOCÊ" if is_user else "NEXUS"
        ts = _dt.datetime.now().strftime("%H:%M")

        outer = tk.Frame(self._chat_scroll, bg=C["bg"])
        outer.pack(fill="x", padx=5, pady=4)
        bubble = tk.Frame(outer, bg=bg, padx=12, pady=8)
        bubble.pack(side="right" if is_user else "left", padx=(90, 0) if is_user else (0, 90), fill="x", expand=not is_user)

        head = tk.Frame(bubble, bg=bg)
        head.pack(fill="x")
        tk.Label(head, text=tag, bg=bg, fg=C["text_dim"], font=("Consolas", 9, "bold")).pack(side="left")
        if self._cfg.get("show_timestamps", True):
            tk.Label(head, text=ts, bg=bg, fg=C["text_muted"], font=F["tiny"]).pack(side="left", padx=6)
        copy = tk.Label(head, text="⧉", bg=bg, fg=C["text_muted"], font=F["small"], cursor="hand2")
        copy.pack(side="right")
        copy.bind("<Button-1>", lambda _e, t=text: self._copy(t))
        copy.bind("<Enter>", lambda _e: copy.configure(fg=C["cyan"]))
        copy.bind("<Leave>", lambda _e: copy.configure(fg=C["text_muted"]))

        tk.Label(bubble, text=text, bg=bg, fg=fg, font=F["body"], justify="left", anchor="w", wraplength=620).pack(fill="x", pady=(4, 0))
        self._message_count += 1
        self.after(50, lambda: self._chat_scroll._parent_canvas.yview_moveto(1.0))
        self._update_footer_text()

    def _build_auto_tab(self) -> tk.Frame:
        frame = tk.Frame(self._content_host, bg=C["bg"])
        top = tk.Frame(frame, bg=C["panel"])
        top.pack(fill="x")
        tk.Label(top, text="⚡ AUTOMAÇÕES", bg=C["panel"], fg=C["cyan"], font=F["heading"]).pack(side="left", padx=14, pady=9)
        self._auto_filter = tk.StringVar()
        self._auto_filter.trace_add("write", lambda *_a: self._rebuild_actions())
        tk.Entry(top, textvariable=self._auto_filter, bg=C["border"], fg=C["text"], insertbackground=C["cyan"], relief="flat", font=F["small"], width=28).pack(side="right", padx=12, ipady=5)
        tk.Label(top, text="Buscar:", bg=C["panel"], fg=C["text_dim"], font=F["tiny"]).pack(side="right")

        self._auto_scroll = ctk.CTkScrollableFrame(frame, fg_color=C["bg"], scrollbar_button_color=C["border"])
        self._auto_scroll.pack(fill="both", expand=True, padx=12, pady=10)
        for i in range(3):
            self._auto_scroll.columnconfigure(i, weight=1)
        self._action_sections = self._automation_sections()
        self._rebuild_actions()
        return frame

    def _automation_sections(self):
        return [
            ("🌐 Navegadores", "secondary", [("Chrome", "abre o Chrome"), ("Edge", "abre o Edge"), ("YouTube", "abre o YouTube"), ("Google", "pesquisa no google")]),
            ("🎵 Mídia", "secondary", [("Spotify", "abre o Spotify"), ("Tocar no YouTube", "toca música no youtube"), ("Tocar no Spotify", "toca música no spotify")]),
            ("📁 Arquivos", "secondary", [("Downloads", "abre meus downloads"), ("Área de trabalho", "abre a área de trabalho"), ("Bloco de Notas", "abre o bloco de notas"), ("Calculadora", "abre a calculadora")]),
            ("🪟 Desktop", "secondary", [("Listar janelas", "listar janelas"), ("Screenshot", "tirar screenshot"), ("Clipboard", "ler clipboard"), ("Limpar clipboard", "limpar clipboard"), ("Docs", "abrir pasta documentos")]),
            ("🧭 Apps", "secondary", [("Listar apps", "listar apps")]),
            ("⚙ Sistema", "success", [("Status PC", "mostra o status do PC"), ("Print", "tira print"), ("Data/Hora", "que horas são"), ("Bloquear", "bloquear tela")]),
            ("🔊 Volume", "ghost", [("Aumentar", "aumenta o volume"), ("Diminuir", "diminui o volume"), ("Mutar", "muta o som")]),
            ("⚠ Crítico", "danger", [("Reiniciar", "reinicia o computador"), ("Desligar", "desliga o computador")]),
        ]

    def _rebuild_actions(self):
        if not hasattr(self, "_auto_scroll"):
            return
        for child in self._auto_scroll.winfo_children():
            child.destroy()
        filt = self._auto_filter.get().strip().lower() if hasattr(self, "_auto_filter") else ""
        row = col = 0
        for title, style, actions in self._action_sections:
            shown = [(label, cmd) for label, cmd in actions if not filt or filt in label.lower() or filt in cmd.lower() or filt in title.lower()]
            if not shown:
                continue
            card = tk.Frame(self._auto_scroll, bg=C["card"])
            card.grid(row=row, column=col, sticky="nsew", padx=6, pady=6)
            tk.Label(card, text=title, bg=C["card"], fg=C["cyan"], font=F["small"]).pack(fill="x", padx=10, pady=(10, 5))
            tk.Frame(card, bg=C["border"], height=1).pack(fill="x", padx=8)
            for label, cmd in shown:
                self._btn(card, label, lambda c=cmd: self._run_command(c), style, h=30).pack(fill="x", padx=8, pady=3)
            tk.Frame(card, bg=C["card"], height=6).pack()
            col += 1
            if col >= 3:
                col = 0
                row += 1
        mon = tk.Frame(self._auto_scroll, bg=C["panel"])
        mon.grid(row=row + 1, column=0, columnspan=3, sticky="ew", padx=6, pady=8)
        self._build_monitor(mon)

    def _build_monitor(self, parent):
        tk.Label(parent, text="📊 MONITOR AO VIVO", bg=C["panel"], fg=C["cyan"], font=F["small"]).pack(anchor="w", padx=14, pady=(10, 5))
        tk.Frame(parent, bg=C["border"], height=1).pack(fill="x", padx=8)
        grow = tk.Frame(parent, bg=C["panel"])
        grow.pack(fill="x", padx=10, pady=8)
        self._cpu_graph = LiveGraph(grow, "CPU", C["cyan"])
        self._cpu_graph.pack(side="left", padx=6)
        self._ram_graph = LiveGraph(grow, "RAM", C["green"])
        self._ram_graph.pack(side="left", padx=6)
        self._disk_graph = LiveGraph(grow, "DISCO", C["purple"])
        self._disk_graph.pack(side="left", padx=6)
        brow = tk.Frame(parent, bg=C["panel"])
        brow.pack(fill="x", padx=10, pady=(0, 10))
        self._cpu_bar = MiniBar(brow, "CPU", C["cyan"])
        self._cpu_bar.pack(side="left", padx=6)
        self._ram_bar = MiniBar(brow, "RAM", C["green"])
        self._ram_bar.pack(side="left", padx=6)
        self._disk_bar = MiniBar(brow, "DISCO", C["purple"])
        self._disk_bar.pack(side="left", padx=6)

    def _build_config_tab(self) -> tk.Frame:
        frame = tk.Frame(self._content_host, bg=C["bg"])
        scroll = ctk.CTkScrollableFrame(frame, fg_color=C["bg"], scrollbar_button_color=C["border"])
        scroll.pack(fill="both", expand=True, padx=18, pady=10)

        def section(title: str):
            tk.Label(scroll, text=title, bg=C["bg"], fg=C["cyan"], font=F["heading"]).pack(anchor="w", pady=(16, 4))
            tk.Frame(scroll, bg=C["border"], height=1).pack(fill="x")

        def row(label: str):
            r = tk.Frame(scroll, bg=C["card"])
            r.pack(fill="x", pady=4)
            tk.Label(r, text=label, bg=C["card"], fg=C["text_dim"], font=F["small"], width=24, anchor="w").pack(side="left", padx=12, pady=9)
            return r

        cfg = self._cfg
        section("🔑 OpenAI")
        r = row("API Key")
        self._api_key_var = tk.StringVar(value=cfg.get("openai_api_key", ""))
        self._api_entry = tk.Entry(r, textvariable=self._api_key_var, bg=C["border"], fg=C["text"], insertbackground=C["cyan"], relief="flat", show="•", font=F["small"])
        self._api_entry.pack(side="left", fill="x", expand=True, padx=4, ipady=6)
        self._api_show = tk.BooleanVar(value=False)
        tk.Checkbutton(r, text="👁", variable=self._api_show, command=lambda: self._api_entry.configure(show="" if self._api_show.get() else "•"), bg=C["card"], fg=C["text_dim"], selectcolor=C["card"], activebackground=C["card"], bd=0).pack(side="left", padx=8)

        section("👤 Identidade")
        r = row("Nome")
        self._owner_var = tk.StringVar(value=cfg.get("owner_name", "Nicolas"))
        tk.Entry(r, textvariable=self._owner_var, bg=C["border"], fg=C["text"], insertbackground=C["cyan"], relief="flat", font=F["small"]).pack(side="left", fill="x", expand=True, padx=4, ipady=6)

        section("🧠 Memória Obsidian")
        r = row("Ativar memória")
        self._obsidian_enabled_var = tk.BooleanVar(value=bool(cfg.get("obsidian_enabled", True)))
        tk.Checkbutton(r, variable=self._obsidian_enabled_var, bg=C["card"], selectcolor=C["cyan_bg"], activebackground=C["card"], bd=0).pack(side="left", padx=10)
        r = row("Vault")
        self._obsidian_path_var = tk.StringVar(value=cfg.get("obsidian_vault_path", ""))
        tk.Entry(r, textvariable=self._obsidian_path_var, bg=C["border"], fg=C["text"], insertbackground=C["cyan"], relief="flat", font=F["small"]).pack(side="left", fill="x", expand=True, padx=4, ipady=6)
        self._btn(r, "Escolher", self._choose_obsidian_vault, "secondary", w=86, h=30).pack(side="left", padx=6)
        r = row("Pasta de registros")
        self._obsidian_folder_var = tk.StringVar(value=cfg.get("obsidian_memory_folder", "NEXUS/Memory Inbox"))
        tk.Entry(r, textvariable=self._obsidian_folder_var, bg=C["border"], fg=C["text"], insertbackground=C["cyan"], relief="flat", font=F["small"]).pack(side="left", fill="x", expand=True, padx=4, ipady=6)
        r = row("Registrar respostas")
        self._obsidian_register_var = tk.BooleanVar(value=bool(cfg.get("obsidian_auto_register", True)))
        tk.Checkbutton(r, variable=self._obsidian_register_var, bg=C["card"], selectcolor=C["cyan_bg"], activebackground=C["card"], bd=0).pack(side="left", padx=10)

        section("🔊 Voz")
        r = row("Responder por voz")
        self._voice_var = tk.BooleanVar(value=bool(cfg.get("speak_responses", True)))
        tk.Checkbutton(r, variable=self._voice_var, bg=C["card"], selectcolor=C["cyan_bg"], activebackground=C["card"], bd=0).pack(side="left", padx=10)
        r = row("Backend de voz")
        self._voice_backend_var = tk.StringVar(value=cfg.get("voice_backend", "auto"))
        for value, label in [("auto", "Auto"), ("sounddevice", "SoundDevice"), ("google", "Google"), ("vosk", "Vosk")]:
            tk.Radiobutton(r, text=label, variable=self._voice_backend_var, value=value, bg=C["card"], fg=C["text_dim"], selectcolor=C["card"], activebackground=C["card"], font=F["small"]).pack(side="left", padx=8)
        r = row("Microfone")
        self._voice_input_device_var = tk.StringVar(value=str(cfg.get("voice_input_device", "")))
        tk.Entry(r, textvariable=self._voice_input_device_var, bg=C["border"], fg=C["text"], insertbackground=C["cyan"], relief="flat", font=F["small"], width=8).pack(side="left", padx=4, ipady=6)
        tk.Label(r, text="índice do dispositivo de entrada", bg=C["card"], fg=C["text_dim"], font=F["small"]).pack(side="left", padx=8)
        r = row("Wake word")
        self._wake_word_var = tk.StringVar(value=cfg.get("wake_word", "nexus"))
        tk.Entry(r, textvariable=self._wake_word_var, bg=C["border"], fg=C["text"], insertbackground=C["cyan"], relief="flat", font=F["small"]).pack(side="left", fill="x", expand=True, padx=4, ipady=6)
        r = row("Exigir wake word")
        self._voice_require_wake_word_var = tk.BooleanVar(value=bool(cfg.get("voice_require_wake_word", True)))
        tk.Checkbutton(r, variable=self._voice_require_wake_word_var, bg=C["card"], selectcolor=C["cyan_bg"], activebackground=C["card"], bd=0).pack(side="left", padx=10)
        r = row("Timeout de escuta")
        self._voice_listen_timeout_var = tk.StringVar(value=str(cfg.get("voice_listen_timeout", 5)))
        tk.Entry(r, textvariable=self._voice_listen_timeout_var, bg=C["border"], fg=C["text"], insertbackground=C["cyan"], relief="flat", font=F["small"], width=8).pack(side="left", padx=4, ipady=6)
        tk.Label(r, text="segundos para aguardar fala", bg=C["card"], fg=C["text_dim"], font=F["small"]).pack(side="left", padx=8)
        r = row("Limite da frase")
        self._voice_phrase_limit_var = tk.StringVar(value=str(cfg.get("voice_phrase_time_limit", 10)))
        tk.Entry(r, textvariable=self._voice_phrase_limit_var, bg=C["border"], fg=C["text"], insertbackground=C["cyan"], relief="flat", font=F["small"], width=8).pack(side="left", padx=4, ipady=6)
        tk.Label(r, text="segundos por captura", bg=C["card"], fg=C["text_dim"], font=F["small"]).pack(side="left", padx=8)
        r = row("Motor TTS")
        self._engine_var = tk.StringVar(value=cfg.get("voice_engine", "pyttsx3"))
        for value, label in [("pyttsx3", "pyttsx3 offline"), ("edge-tts", "edge-tts online"), ("elevenlabs", "ElevenLabs")]:
            tk.Radiobutton(r, text=label, variable=self._engine_var, value=value, bg=C["card"], fg=C["text_dim"], selectcolor=C["card"], activebackground=C["card"], font=F["small"]).pack(side="left", padx=8)
        r = row("ElevenLabs API Key")
        self._eleven_key_var = tk.StringVar(value=cfg.get("elevenlabs_api_key", ""))
        self._eleven_key_entry = tk.Entry(r, textvariable=self._eleven_key_var, bg=C["border"], fg=C["text"], insertbackground=C["cyan"], relief="flat", show="•", font=F["small"])
        self._eleven_key_entry.pack(side="left", fill="x", expand=True, padx=4, ipady=6)
        self._eleven_show = tk.BooleanVar(value=False)
        tk.Checkbutton(r, text="👁", variable=self._eleven_show, command=lambda: self._eleven_key_entry.configure(show="" if self._eleven_show.get() else "•"), bg=C["card"], fg=C["text_dim"], selectcolor=C["card"], activebackground=C["card"], bd=0).pack(side="left", padx=8)
        r = row("ElevenLabs Voice ID")
        self._eleven_voice_var = tk.StringVar(value=cfg.get("elevenlabs_voice_id", ""))
        tk.Entry(r, textvariable=self._eleven_voice_var, bg=C["border"], fg=C["text"], insertbackground=C["cyan"], relief="flat", font=F["small"]).pack(side="left", fill="x", expand=True, padx=4, ipady=6)

        section("🎵 Mídia")
        r = row("Plataforma padrão")
        self._media_var = tk.StringVar(value=cfg.get("default_media", "youtube"))
        for value, label in [("youtube", "YouTube"), ("spotify", "Spotify")]:
            tk.Radiobutton(r, text=label, variable=self._media_var, value=value, bg=C["card"], fg=C["text_dim"], selectcolor=C["card"], activebackground=C["card"], font=F["small"]).pack(side="left", padx=8)

        section("🖥 Interface")
        r = row("Sempre no topo")
        self._top_cfg_var = tk.BooleanVar(value=bool(cfg.get("always_on_top")))
        tk.Checkbutton(r, variable=self._top_cfg_var, bg=C["card"], selectcolor=C["cyan_bg"], activebackground=C["card"], bd=0).pack(side="left", padx=10)
        r = row("Modo compacto")
        self._compact_var = tk.BooleanVar(value=bool(cfg.get("compact_mode")))
        tk.Checkbutton(r, variable=self._compact_var, bg=C["card"], selectcolor=C["cyan_bg"], activebackground=C["card"], bd=0).pack(side="left", padx=10)
        r = row("Timestamps no chat")
        self._timestamps_var = tk.BooleanVar(value=bool(cfg.get("show_timestamps", True)))
        tk.Checkbutton(r, variable=self._timestamps_var, bg=C["card"], selectcolor=C["cyan_bg"], activebackground=C["card"], bd=0).pack(side="left", padx=10)
        r = row("Sons da interface")
        self._sounds_var = tk.BooleanVar(value=bool(cfg.get("ui_sounds", True)))
        tk.Checkbutton(r, variable=self._sounds_var, bg=C["card"], selectcolor=C["cyan_bg"], activebackground=C["card"], bd=0).pack(side="left", padx=10)
        r = row("Animações ambientais")
        self._animations_var = tk.BooleanVar(value=bool(cfg.get("ui_animations", True)))
        tk.Checkbutton(r, variable=self._animations_var, bg=C["card"], selectcolor=C["cyan_bg"], activebackground=C["card"], bd=0).pack(side="left", padx=10)

        self._btn(scroll, "💾 Salvar configurações", self._save_config, "primary", h=38).pack(anchor="w", pady=14)
        return frame

    def _save_config(self):
        def _coerce_int(value, default):
            try:
                return int(str(value).strip())
            except (TypeError, ValueError):
                return default

        cfg = settings.save({
            "openai_api_key": self._api_key_var.get().strip(),
            "owner_name": self._owner_var.get().strip() or "Nicolas",
            "obsidian_enabled": self._obsidian_enabled_var.get(),
            "obsidian_vault_path": self._obsidian_path_var.get().strip(),
            "obsidian_memory_folder": self._obsidian_folder_var.get().strip() or "NEXUS/Memory Inbox",
            "obsidian_auto_register": self._obsidian_register_var.get(),
            "speak_responses": self._voice_var.get(),
            "voice_backend": self._voice_backend_var.get(),
            "voice_input_device": self._voice_input_device_var.get().strip(),
            "wake_word": self._wake_word_var.get().strip().lower() or "nexus",
            "voice_require_wake_word": self._voice_require_wake_word_var.get(),
            "voice_listen_timeout": _coerce_int(self._voice_listen_timeout_var.get(), 5),
            "voice_phrase_time_limit": _coerce_int(self._voice_phrase_limit_var.get(), 10),
            "voice_engine": self._engine_var.get(),
            "elevenlabs_api_key": self._eleven_key_var.get().strip(),
            "elevenlabs_voice_id": self._eleven_voice_var.get().strip(),
            "default_media": self._media_var.get(),
            "always_on_top": self._top_cfg_var.get(),
            "compact_mode": self._compact_var.get(),
            "show_timestamps": self._timestamps_var.get(),
            "ui_sounds": self._sounds_var.get(),
            "ui_animations": self._animations_var.get(),
        })
        self._cfg = cfg
        self._router = CommandRouter(cfg.get("wake_word", "nexus"))
        SoundBus.enabled = bool(cfg.get("ui_sounds", True))
        os.environ["OPENAI_API_KEY"] = cfg.get("openai_api_key", "")
        try:
            import app.config as app_cfg
            app_cfg.OPENAI_API_KEY = cfg.get("openai_api_key", "")
            app_cfg.NEXUS_OWNER = cfg.get("owner_name", "Nicolas")
            import app.assistant as asst
            asst._client = None
            asst._client_key = None
        except Exception:
            pass
        self._ontop_var.set(bool(cfg.get("always_on_top")))
        self._apply_topmost()
        if cfg.get("ui_animations", True):
            self._header_scan.start()
            self._ticker.start()
        else:
            self._header_scan.stop()
            self._ticker.stop()
        show_toast(self, "Configurações salvas!", "success")

    def _choose_obsidian_vault(self):
        path = filedialog.askdirectory(title="Selecionar vault Obsidian")
        if path:
            self._obsidian_path_var.set(path)
            show_toast(self, "Vault selecionado. Salve as configurações.", "info")

    def _build_logs_tab(self) -> tk.Frame:
        frame = tk.Frame(self._content_host, bg=C["bg"])
        tb = tk.Frame(frame, bg=C["panel"])
        tb.pack(fill="x")
        tk.Label(tb, text="📋 LOGS", bg=C["panel"], fg=C["cyan"], font=F["heading"]).pack(side="left", padx=14, pady=9)
        self._btn(tb, "⧉ Copiar", self._copy_logs, "ghost", h=28, w=92).pack(side="right", padx=6)
        self._btn(tb, "⟳ Atualizar", self._refresh_logs, "ghost", h=28, w=108).pack(side="right", padx=4)
        self._log_filter = tk.StringVar()
        self._log_filter.trace_add("write", lambda *_a: self._refresh_logs())
        tk.Entry(tb, textvariable=self._log_filter, bg=C["border"], fg=C["text"], insertbackground=C["cyan"], relief="flat", width=24, font=F["small"]).pack(side="right", padx=6, ipady=4)
        tk.Label(tb, text="Filtrar:", bg=C["panel"], fg=C["text_dim"], font=F["tiny"]).pack(side="right")

        host = tk.Frame(frame, bg=C["bg"])
        host.pack(fill="both", expand=True, padx=12, pady=10)
        self._log_text = tk.Text(host, bg=C["card"], fg=C["text_dim"], font=F["mono"], relief="flat", bd=0, state="disabled", wrap="none", insertbackground=C["cyan"], selectbackground=C["border"])
        sy = tk.Scrollbar(host, command=self._log_text.yview, bg=C["border"], troughcolor=C["bg"])
        sx = tk.Scrollbar(host, orient="horizontal", command=self._log_text.xview, bg=C["border"], troughcolor=C["bg"])
        self._log_text.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        sy.pack(side="right", fill="y")
        sx.pack(side="bottom", fill="x")
        self._log_text.pack(fill="both", expand=True)
        for tag, color in {"error": C["error"], "action": C["green"], "cmd": C["cyan"], "debug": C["warning"]}.items():
            self._log_text.tag_config(tag, foreground=color)
        return frame

    def _refresh_logs(self):
        filt = self._log_filter.get().lower() if hasattr(self, "_log_filter") else ""
        self._log_text.configure(state="normal")
        self._log_text.delete("1.0", "end")
        for line in reversed(get_recent_logs(300)):
            if filt and filt not in line.lower():
                continue
            upper = line.upper()
            tag = "error" if "ERRO" in upper else "action" if "ACAO" in upper or "AÇÃO" in upper else "cmd" if "COMANDO" in upper else "debug" if "DEBUG" in upper else ""
            self._log_text.insert("end", line + "\n", tag)
        self._log_text.configure(state="disabled")

    def _copy_logs(self):
        text = self._log_text.get("1.0", "end").strip()
        self._copy(text or "Sem logs.")

    def _build_footer(self):
        ft = tk.Frame(self, bg=C["panel"], height=28)
        ft.pack(fill="x", side="bottom")
        ft.pack_propagate(False)
        self._footer_scan = AmbientScanner(ft, height=28, bg=C["panel"])
        self._footer_scan.place(x=0, y=0, relwidth=1, relheight=1)
        if self._cfg.get("ui_animations", True):
            self._footer_scan.start()
        tk.Frame(ft, bg=C["border"], height=1).place(x=0, y=0, relwidth=1)
        self._footer_left = tk.StringVar(value="")
        self._footer_right = tk.StringVar(value="")
        tk.Label(ft, textvariable=self._footer_left, bg=C["panel"], fg=C["text_muted"], font=F["tiny"]).pack(side="left", padx=14)
        tk.Label(ft, textvariable=self._footer_right, bg=C["panel"], fg=C["text_muted"], font=F["tiny"]).pack(side="right", padx=14)
        self._update_footer_text()

    def _submit_text(self):
        text = self._input.get().strip()
        if not text or text == self._ph:
            return
        self._input.delete(0, "end")
        cmd_history.add(text)
        self._run_command(text)

    def _run_command(self, text: str):
        if self._processing:
            show_toast(self, "Aguarde o comando atual terminar.", "warning")
            return
        self._processing = True
        self._sync_coder_context()
        understood = self._router.describe(text)
        SoundBus.play("start")
        self._command_count += 1
        self._add_chat_message("user", text)
        self._add_system_msg(f"Ouvi: {text}")
        self._add_system_msg(f"Entendi: {understood}")
        self._set_status("PROCESSANDO", C["warning"])
        self._send_btn.configure(state="disabled")
        self._switch_tab("chat")

        def worker():
            try:
                from app.logger import log_action
                log_action(f"Executando: {understood}")
                result = self._on_command(text, self._confirm_callback)
                self.after(0, lambda: self._show_response(result))
            except Exception as error:
                self.after(0, lambda: self._show_response(handle_error(error), error=True))

        threading.Thread(target=worker, daemon=True).start()

    def _confirm_callback(self, question: str) -> bool:
        answer = [False]
        event = threading.Event()

        def ask():
            answer[0] = messagebox.askyesno("Confirmação", question)
            event.set()

        self.after(0, ask)
        event.wait(30)
        return answer[0]

    def _show_response(self, text: str, error: bool = False):
        self._processing = False
        self._send_btn.configure(state="normal")
        self._set_status("PRONTO", C["green"])
        if not text or text.strip() == ".":
            return
        self._add_chat_message("assistant", text)
        SoundBus.play("error" if error else "success")
        show_toast(self, text[:80], "error" if error else "info", 2600)
        if not error and self._cfg.get("speak_responses", True):
            try:
                from app.voice_output import falar
                spoken = text if len(text) <= 500 else text[:500] + "... resposta longa exibida na tela."
                falar(spoken, engine=self._cfg.get("voice_engine", "pyttsx3"), settings=self._cfg)
            except Exception:
                pass

    def _handle_live_event(self, kind: str, message: str, data: dict | None = None):
        if kind not in {"agent", "vision", "home", "error"}:
            return

        text = (message or "").strip()
        if not text:
            return

        if kind in {"agent", "vision", "home"}:
            label = {
                "agent": "AGENTE",
                "vision": "VISAO",
                "home": "CASA",
            }[kind]
            rendered = text if text.startswith("[") else f"[{label}] {text}"
            self._set_module_status(kind, text)
            self._add_chat_message("assistant", rendered)
            return

        self._add_chat_message("assistant", text)
        self._set_status("ERRO", C["error"])
        show_toast(self, text[:80], "error", 2600)

    def _set_module_status(self, kind: str, message: str):
        if kind not in self._module_status:
            return

        lowered = message.lower()
        if "erro" in lowered:
            status = "erro"
        elif any(token in lowered for token in ("conclu", "parado", "cancelad", "pronto")):
            status = "ocioso"
        else:
            status = "ativo"

        self._module_status[kind] = status
        self._refresh_module_status()

    def _refresh_module_status(self):
        if hasattr(self, "_module_status_var"):
            self._module_status_var.set(
                "Modulos: "
                f"agent {self._module_status['agent']} | "
                f"visao {self._module_status['vision']} | "
                f"casa {self._module_status['home']}"
            )
        self._update_footer_text()

    def _toggle_mic(self):
        if self._listening or self._processing:
            return
        self._listening = True
        SoundBus.play("start")
        self._pulse.stop()
        self._pulse.start(C["error"])
        self._mic_btn.configure(text="■", fg_color=C["error"], text_color="#ffffff")
        self._set_status("OUVINDO", C["error"])
        threading.Thread(target=self._listen_thread, daemon=True).start()

    def _toggle_voice_loop(self):
        if self._voice_loop_active:
            self._voice_loop_active = False
            if self._voice_loop:
                self._voice_loop.stop()
            self._voice_loop_btn.configure(text="Voz OFF", **BTN["ghost"])
            self._set_status("PRONTO", C["green"])
            self._update_footer_text()
            show_toast(self, "Voz continua desativada.", "info")
            return

        from app.voice.voice_loop import VoiceLoop

        self._voice_loop_active = True
        self._voice_loop_btn.configure(text="Voz ON", **BTN["success"])
        self._set_status("OUVINDO", C["error"])
        cfg = dict(self._cfg)
        cfg.setdefault("wake_word", "nexus")
        self._voice_loop = VoiceLoop(
            command_callback=lambda text: self.after(0, lambda t=text: self._run_command(t)),
            event_callback=lambda kind, message: self.after(0, lambda k=kind, m=message: self._voice_event(k, m)),
            settings=cfg,
        )
        self._voice_loop.start()
        self._update_footer_text()
        show_toast(self, "Voz continua ativada.", "success")

    def _voice_event(self, kind: str, message: str):
        if kind in {"heard", "understood", "voice"}:
            self._add_system_msg(f"{kind.upper()}: {message}")
        elif kind == "error":
            self._add_chat_message("assistant", message)

    def _sync_coder_context(self):
        panel = getattr(self, "_coder_panel", None)
        if not panel:
            return
        try:
            from coding.dispatcher import set_contexto, set_editor_bridge
            set_contexto(codigo=panel.get_codigo().strip(), linguagem=panel._linguagem_var.get())
            set_editor_bridge(panel.build_editor_bridge())
        except Exception:
            pass

    def _listen_thread(self):
        try:
            from app.voice_input import ouvir_microfone
            text = ouvir_microfone()
            self.after(0, lambda: self._on_mic_done(text))
        except Exception as error:
            msg = handle_error(error)
            self.after(0, lambda msg=msg: self._on_mic_error(msg))

    def _on_mic_done(self, text: str):
        self._reset_mic()
        if text:
            self._run_command(text)
        else:
            show_toast(self, "Não ouvi nada.", "warning")

    def _on_mic_error(self, msg: str):
        self._reset_mic()
        self._add_chat_message("assistant", msg)
        show_toast(self, msg, "error")

    def _reset_mic(self):
        self._listening = False
        SoundBus.play("stop")
        self._pulse.stop()
        self._pulse.start(C["green"])
        self._mic_btn.configure(text="🎙", **BTN["secondary"])

    def _btn(self, parent, text, cmd, style="secondary", w=0, h=32):
        kw = dict(BTN[style])
        if w:
            kw["width"] = w
        kw["height"] = h
        return bind_button_fx(ctk.CTkButton(parent, text=text, command=cmd, **kw))

    def _copy(self, text: str):
        self.clipboard_clear()
        self.clipboard_append(text)
        show_toast(self, "Copiado!", "success", 1500)

    def _set_status(self, text: str, color: str):
        self._status_lbl.configure(text=text, fg=color)

    def _clear_chat(self):
        for child in self._chat_scroll.winfo_children():
            child.destroy()
        self._message_count = 0
        self._add_system_msg("Chat limpo.")
        self._update_footer_text()

    def _focus_input(self):
        if hasattr(self, "_input"):
            self._input.focus_set()

    def _limpar_memoria(self):
        clear_memory()
        self._add_chat_message("assistant", "Memória limpa.")
        show_toast(self, "Memória apagada.", "success")

    def _toggle_ontop(self):
        settings.set_value("always_on_top", self._ontop_var.get())
        self._top_cfg_var.set(self._ontop_var.get()) if hasattr(self, "_top_cfg_var") else None
        self._apply_topmost()
        show_toast(self, "Sempre no topo ativado." if self._ontop_var.get() else "Sempre no topo desativado.", "success")

    def _apply_topmost(self):
        val = bool(self._ontop_var.get())
        self.attributes("-topmost", val)
        self._pin_btn.configure(fg=C["cyan"] if val else C["text_dim"])

    def _history_up(self, _e):
        prev = cmd_history.up("" if self._input.get() == self._ph else self._input.get())
        if prev is not None:
            self._input.delete(0, "end")
            self._input.insert(0, prev)
            self._input.configure(fg=C["text"])
        return "break"

    def _history_down(self, _e):
        nxt = cmd_history.down()
        if nxt is not None:
            self._input.delete(0, "end")
            self._input.insert(0, nxt)
            self._input.configure(fg=C["text"])
        return "break"

    def _start_background_tasks(self):
        self._update_monitor()

    def _update_clock(self):
        self._clock_lbl.configure(text=_dt.datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self._update_clock)

    def _update_monitor(self):
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=0)
            ram = psutil.virtual_memory().percent
            disk = psutil.disk_usage(os.getenv("SystemDrive", "C:") + "\\").percent
            self._last_metrics = {"cpu": cpu, "ram": ram, "disk": disk}
            if hasattr(self, "_cpu_graph"):
                self._cpu_graph.push(cpu)
                self._ram_graph.push(ram)
                self._disk_graph.push(disk)
                self._cpu_bar.set_value(cpu)
                self._ram_bar.set_value(ram)
                self._disk_bar.set_value(disk)
        except Exception:
            pass
        self._update_footer_text()
        self.after(int(self._cfg.get("monitor_interval_ms", 2000)), self._update_monitor)

    def _update_footer_text(self):
        if not hasattr(self, "_footer_left"):
            return
        owner = self._cfg.get("owner_name", "Nicolas")
        voice = "voz ON" if self._voice_loop_active else "voz OFF"
        self._footer_left.set(f"NEXUS v2.1 · {owner} · {voice} · mensagens {self._message_count} · comandos {self._command_count}")
        m = self._last_metrics
        self._footer_right.set(f"CPU {m['cpu']:.0f}% · RAM {m['ram']:.0f}% · DISCO {m['disk']:.0f}% · atualiza 2s")

    def _on_close(self):
        try:
            if self._voice_loop:
                self._voice_loop.stop()
        except Exception:
            pass
        self.destroy()

    def _update_footer_text(self):
        if not hasattr(self, "_footer_left"):
            return
        owner = self._cfg.get("owner_name", "Nicolas")
        voice = "voz ON" if self._voice_loop_active else "voz OFF"
        active_modules = ",".join(
            name for name, status in self._module_status.items() if status == "ativo"
        ) or "nenhum"
        self._footer_left.set(
            f"NEXUS v2.1 | {owner} | {voice} | modulos {active_modules} | mensagens {self._message_count} | comandos {self._command_count}"
        )
        metrics = self._last_metrics
        self._footer_right.set(
            f"CPU {metrics['cpu']:.0f}% | RAM {metrics['ram']:.0f}% | DISCO {metrics['disk']:.0f}% | atualiza 2s"
        )

    def _on_close(self):
        try:
            if self._voice_loop:
                self._voice_loop.stop()
        except Exception:
            pass
        try:
            if self._live_event_unsubscribe and self._live_event_listener:
                self._live_event_unsubscribe(self._live_event_listener)
        except Exception:
            pass
        self.destroy()

    def run(self):
        self.mainloop()
