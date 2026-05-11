import customtkinter as ctk
import threading
import os
from app.self_improvement.nexus_mind import NexusMind
from app.self_improvement.file_tracker import FileTracker
from app.self_improvement.restart_manager import RestartManager

class NexusMindPanel(ctk.CTkFrame):
    def __init__(self, master, settings, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.settings = settings
        self.tracker = FileTracker()
        self.restart_mgr = RestartManager(on_confirm_callback=self._ask_restart)
        self.mind = NexusMind(
            api_key=settings.get("openai_api_key", ""),
            auto_mode=False,
            restart_mgr=self.restart_mgr
        )
        self._build_ui()
        self._refresh_files()


    def _build_ui(self):
        self.mind_settings = self._load_mind_settings()

        # Tabview
        self.tabview = ctk.CTkTabview(self, fg_color="transparent", text_color="#A6ACCD", segmented_button_selected_color="#1E1E2E", segmented_button_selected_hover_color="#313244")
        self.tabview.pack(fill="both", expand=True, padx=4, pady=4)
        
        self.tab_mind = self.tabview.add("Mente & Log")
        self.tab_ideas = self.tabview.add("Ideias & Módulos")
        self.tab_plugins = self.tabview.add("Meus Módulos")
        
        from ui.nexus_ideas_panel import NexusIdeasPanel
        self.ideas_panel = NexusIdeasPanel(self.tab_ideas, self.settings)
        self.ideas_panel.pack(fill="both", expand=True)

        from ui.nexus_plugins_panel import NexusPluginsPanel
        self.plugins_panel = NexusPluginsPanel(self.tab_plugins, self.settings)
        self.plugins_panel.pack(fill="both", expand=True)
        
        self._build_mind_tab(self.tab_mind)

    def _build_mind_tab(self, parent):
        # Título
        ctk.CTkLabel(parent, text="NEXUS MIND — AUTO-MELHORIA",
                     font=("Courier", 16, "bold"), text_color="#00FFFF").pack(anchor="w", padx=16, pady=(16,4))

        # Toggle principal
        self.toggle_var = ctk.BooleanVar(value=self.mind_settings.get("active", False))
        self.toggle_btn = ctk.CTkSwitch(
            parent, text="Ativar auto-melhoria",
            variable=self.toggle_var,
            command=self._on_toggle,
            font=("Courier", 13),
            progress_color="#00FFFF"
        )
        self.toggle_btn.pack(anchor="w", padx=16, pady=8)
        
        # Auto-Restart Switch
        self.auto_restart_var = ctk.BooleanVar(value=self.mind_settings.get("auto_restart", False))
        self.auto_restart_btn = ctk.CTkSwitch(
            parent, text="Auto-Restart após mudanças críticas",
            variable=self.auto_restart_var,
            command=self._save_mind_settings,
            font=("Courier", 11),
            progress_color="#F9E2AF"
        )
        self.auto_restart_btn.pack(anchor="w", padx=16, pady=(0, 8))

        # Modo de operação
        ctk.CTkLabel(parent, text="Modo:", font=("Courier", 11)).pack(anchor="w", padx=16)
        self.mode_var = ctk.StringVar(value=self.mind_settings.get("mode", "supervisionado"))
        mode_frame = ctk.CTkFrame(parent, fg_color="transparent")
        mode_frame.pack(fill="x", padx=16, pady=4)
        for mode in ["supervisionado", "autônomo", "agressivo"]:
            ctk.CTkRadioButton(
                mode_frame, text=mode,
                variable=self.mode_var, value=mode,
                command=self._on_mode_change,
                font=("Courier", 12),
                hover_color="#00FFFF",
            ).pack(side="left", padx=8)

        # Diretriz
        ctk.CTkLabel(parent, text="Diretriz / Foco de melhoria:", font=("Courier", 11)).pack(anchor="w", padx=16, pady=(8,0))
        self.directive_entry = ctk.CTkEntry(parent, font=("Courier", 12), fg_color="#1E1E2E", placeholder_text="Ex: Melhore sua inteligência...", text_color="#A6ACCD")
        self.directive_entry.pack(fill="x", padx=16, pady=4)
        if self.mind_settings.get("directive"):
            self.directive_entry.insert(0, self.mind_settings["directive"])
            self.mind.user_directive = self.mind_settings["directive"]
            
        self.directive_entry.bind("<KeyRelease>", self._on_directive_change)

        # Intervalo
        ctk.CTkLabel(parent, text="Intervalo entre ciclos (min):",
                     font=("Courier", 11)).pack(anchor="w", padx=16, pady=(8,0))
        self.interval_slider = ctk.CTkSlider(
            parent, from_=1, to=60, number_of_steps=59,
            command=self._on_interval_change,
            button_color="#00FFFF", button_hover_color="#00CCCC"
        )
        self.interval_slider.set(self.mind_settings.get("interval", 5))
        self.interval_slider.pack(fill="x", padx=16)


        # Log
        ctk.CTkLabel(parent, text="LOG:", font=("Courier", 11), text_color="#00FFFF").pack(anchor="w", padx=16, pady=(12,2))
        self.log_box = ctk.CTkTextbox(parent, height=180, font=("Courier", 11), fg_color="#1E1E2E", text_color="#A6ACCD")
        self.log_box.pack(fill="x", padx=16)
        self.log_box.configure(state="disabled")

        # Botões
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=8)
        ctk.CTkButton(btn_frame, text="Ciclo Manual", command=self._manual_cycle,
                      font=("Courier", 12), fg_color="#00FFFF", text_color="#11111B", hover_color="#00CCCC").pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Rollback Git", command=self._rollback,
                      font=("Courier", 12), fg_color="transparent", text_color="#F38BA8",
                      border_width=1, border_color="#F38BA8", hover_color="#583640").pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Ver Melhorias", command=self._show_evidence,
                      font=("Courier", 12), fg_color="transparent", text_color="#A6ACCD",
                      border_width=1, border_color="#A6ACCD", hover_color="#2E2E3E").pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Abrir Modificado", command=self._open_modified_file,
                      font=("Courier", 12), fg_color="transparent", text_color="#A6ACCD",
                      border_width=1, border_color="#A6ACCD", hover_color="#2E2E3E").pack(side="left", padx=4)

        # ── DIVISOR ──────────────────────────────────────
        ctk.CTkLabel(parent, text="ARQUIVOS MODIFICADOS",
                     font=("Courier", 11),
                     text_color="#00BFBF").pack(anchor="w", padx=16, pady=(16, 4))

        # Frame dos arquivos (lista scrollável)
        self.files_frame = ctk.CTkScrollableFrame(parent, height=180)
        self.files_frame.pack(fill="x", padx=16, pady=(0, 8))

        # Botões do painel de arquivos
        btn_row_files = ctk.CTkFrame(parent, fg_color="transparent")
        btn_row_files.pack(fill="x", padx=16, pady=(0, 8))

        ctk.CTkButton(
            btn_row_files, text="Abrir Pasta do Projeto",
            command=self._open_project_folder,
            font=("Courier", 12), width=180
        ).pack(side="left", padx=(0, 6))

        ctk.CTkButton(
            btn_row_files, text="Atualizar Lista",
            command=self._refresh_files,
            font=("Courier", 12), width=120,
            fg_color="transparent", border_width=1
        ).pack(side="left")
        
        # Apply mode logic
        self._on_mode_change()
        
        if self.toggle_var.get():
            self.after(1000, self._on_toggle)

    def _refresh_files(self):
        """Atualiza a lista de arquivos modificados"""
        for w in self.files_frame.winfo_children():
            w.destroy()

        files = self.tracker.get_git_changed_files()
        history = self.tracker.history

        if not files and not history:
            ctk.CTkLabel(
                self.files_frame,
                text="Nenhuma modificacao registrada ainda.",
                font=("Courier", 11),
                text_color="gray"
            ).pack(anchor="w", padx=8, pady=4)
            return

        for f in files:
            self._add_file_row(f["path"], f["action"])

        if history:
            ctk.CTkLabel(
                self.files_frame,
                text=f"-- ciclos anteriores ({len(history)}) --",
                font=("Courier", 10),
                text_color="gray"
            ).pack(anchor="w", padx=8, pady=(8, 2))

            for entry in history[:5]:
                ts = entry["timestamp"][11:16]
                summary = entry["summary"][:60]
                ctk.CTkLabel(
                    self.files_frame,
                    text=f"[{ts}] {summary}",
                    font=("Courier", 10),
                    text_color="gray"
                ).pack(anchor="w", padx=8)

    def _add_file_row(self, filepath: str, action: str):
        colors = {"edit": "#00BFBF", "create": "#1D9E75", "delete": "#E24B4A"}
        labels = {"edit": "EDIT", "create": "NEW", "delete": "DEL"}
        color = colors.get(action, "gray")
        label = labels.get(action, "?")

        row = ctk.CTkFrame(self.files_frame, fg_color="transparent")
        row.pack(fill="x", pady=2)

        ctk.CTkLabel(row, text=label, font=("Courier", 10),
                     text_color=color, width=36).pack(side="left")

        ctk.CTkLabel(row, text=filepath, font=("Courier", 11),
                     anchor="w").pack(side="left", fill="x", expand=True)

        if os.path.exists(filepath):
            ctk.CTkButton(
                row, text="abrir", width=50,
                font=("Courier", 10),
                command=lambda p=filepath: self.tracker.open_file(p)
            ).pack(side="right", padx=2)

            ctk.CTkButton(
                row, text="pasta", width=50,
                font=("Courier", 10),
                fg_color="transparent", border_width=1,
                command=lambda p=filepath: self.tracker.open_in_explorer(p)
            ).pack(side="right", padx=2)

    def _open_project_folder(self):
        import subprocess
        subprocess.Popen(f'explorer "{os.path.abspath(".")}"')

    def _load_mind_settings(self):
        import json, os
        path = "data/mind_settings.json"
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"directive": "", "auto_restart": False}

    def _save_mind_settings(self, event=None):
        import json, os
        path = "data/mind_settings.json"
        os.makedirs("data", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({
                "directive": self.directive_entry.get(),
                "auto_restart": self.auto_restart_var.get(),
                "active": self.toggle_var.get(),
                "mode": self.mode_var.get(),
                "interval": self.interval_slider.get()
            }, f, ensure_ascii=False)

    def _on_directive_change(self, event):
        self._update_directive(event)
        self._save_mind_settings()

    def _ask_restart(self, reason: str) -> bool:
        if hasattr(self, 'auto_restart_var') and self.auto_restart_var.get():
            self._log("🔄 Auto-Restart ativado. Reiniciando sem perguntar...")
            return True
            
        dialog = ctk.CTkToplevel(self)
        dialog.title("Nexus — Reinicialização Necessária")
        dialog.geometry("420x200")
        dialog.grab_set()

        ctk.CTkLabel(
            dialog,
            text="REINICIALIZACAO NECESSARIA",
            font=("Courier", 13, "bold"),
            text_color="#00BFBF"
        ).pack(pady=(20, 8))

        ctk.CTkLabel(
            dialog,
            text=f"Motivo: {reason[:80]}",
            font=("Courier", 11),
            wraplength=380
        ).pack(padx=16)

        ctk.CTkLabel(
            dialog,
            text="O Nexus precisa reiniciar para aplicar as mudancas.\nDeseja reiniciar agora?",
            font=("Courier", 11),
            text_color="gray"
        ).pack(pady=8, padx=16)

        result = {"confirmed": False}
        btn_row = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_row.pack(pady=8)

        def confirm():
            result["confirmed"] = True
            dialog.destroy()

        def cancel():
            dialog.destroy()

        ctk.CTkButton(btn_row, text="Reiniciar Agora",
                      command=confirm, font=("Courier", 12)).pack(side="left", padx=8)
        ctk.CTkButton(btn_row, text="Depois",
                      command=cancel, font=("Courier", 12),
                      fg_color="transparent", border_width=1).pack(side="left")

        dialog.wait_window()
        return result["confirmed"]



    def _show_evidence(self):
        import os
        import json
        path = "data/nexus_proof.json"
        if not os.path.exists(path):
            self._log("❌ Nenhum relatório de evidências encontrado ainda.")
            return
            
        try:
            with open(path, "r", encoding="utf-8") as f:
                report = json.load(f)
            
            top = ctk.CTkToplevel(self)
            top.title("Evidências do NexusMind")
            top.geometry("600x500")
            top.configure(fg_color="#07070f")
            
            # Formatar o texto
            texto = f"=== RELATÓRIO DE EVIDÊNCIAS ===\nGerado em: {report.get('generated_at', '')}\n\n"
            
            texto += "--- VERIFICAÇÕES DE INTEGRIDADE ---\n"
            for v in report.get("verifications", []):
                icone = "✅" if v.get("status") == "ok" else "❌" if v.get("status") == "fail" else "⚠️"
                texto += f"{icone} {v.get('label')}: {v.get('detail')}\n"
                
            texto += "\n--- ÚLTIMOS COMMITS ---\n"
            for c in report.get("commits", []):
                if "error" in c: continue
                marca = "🤖" if c.get("is_nexus") else "👤"
                texto += f"{marca} [{c.get('hash')}] {c.get('date')} - {c.get('msg')}\n"
                
            tb = ctk.CTkTextbox(top, font=("Courier", 11), fg_color="#1E1E2E", text_color="#A6ACCD")
            tb.pack(fill="both", expand=True, padx=16, pady=16)
            tb.insert("0.0", texto)
            tb.configure(state="disabled")
            
        except Exception as e:
            self._log(f"❌ Erro ao ler evidências: {e}")

    def _log(self, msg):
        self._custom_log(msg)

    def _custom_log(self, msg):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", msg + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        try:
            print(msg)
        except UnicodeEncodeError:
            print(msg.encode('ascii', errors='replace').decode('ascii'))

    def _on_toggle(self):
        self._update_directive()
        self.mind._log = lambda m: self._custom_log(m)
        if self.toggle_var.get():
            self.mind.start()
            self._log("✅ NexusMind ativado")
        else:
            self.mind.stop()
            self._log("⏸ NexusMind pausado")
        self._save_mind_settings()

    def _on_mode_change(self):
        mode = self.mode_var.get()
        self.mind.auto_mode = (mode != "supervisionado")
        if mode == "agressivo":
            self.mind.cycle_interval = 60
        else:
            self.mind.cycle_interval = int(self.interval_slider.get()) * 60
        self._log(f"→ Modo: {mode}")
        self._save_mind_settings()

    def _on_interval_change(self, val):
        self.mind.cycle_interval = int(val) * 60
        self._save_mind_settings()

    def _update_directive(self, event=None):
        texto = self.directive_entry.get().strip()
        self.mind.user_directive = texto if texto else None

    def _manual_cycle(self):
        self._update_directive()
        self.mind._log = lambda m: self._custom_log(m)
        directive = self.directive_entry.get().strip() or None
        threading.Thread(target=self.mind._run_one_cycle, args=(directive,), daemon=True).start()

    def _rollback(self):
        if self.mind.guard.rollback():
            self._log("⏪ Rollback executado")
        else:
            self._log("❌ Erro ao executar rollback")

    def _open_modified_file(self):
        import os
        path = getattr(self.mind, "last_modified_path", None)
        if not path:
            self._log("⚠️ Nenhum arquivo foi modificado recentemente neste ciclo.")
            return
            
        full_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", path))
        if os.path.exists(full_path):
            self._log(f"📂 Abrindo {path}...")
            try:
                os.startfile(full_path)
            except Exception as e:
                self._log(f"❌ Erro ao abrir arquivo: {e}")
        else:
            self._log("❌ Arquivo não encontrado.")
