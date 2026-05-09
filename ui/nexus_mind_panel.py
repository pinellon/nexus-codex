import customtkinter as ctk
import threading
from app.self_improvement.nexus_mind import NexusMind

class NexusMindPanel(ctk.CTkFrame):
    def __init__(self, master, settings, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.settings = settings
        self.mind = NexusMind(
            api_key=settings.get("openai_api_key", ""),
            auto_mode=False
        )
        self._build_ui()

    def _build_ui(self):
        # Título
        ctk.CTkLabel(self, text="NEXUS MIND — AUTO-MELHORIA",
                     font=("Courier", 16, "bold"), text_color="#00FFFF").pack(anchor="w", padx=16, pady=(16,4))

        # Toggle principal
        self.toggle_var = ctk.BooleanVar(value=False)
        self.toggle_btn = ctk.CTkSwitch(
            self, text="Ativar auto-melhoria",
            variable=self.toggle_var,
            command=self._on_toggle,
            font=("Courier", 13),
            progress_color="#00FFFF"
        )
        self.toggle_btn.pack(anchor="w", padx=16, pady=8)

        # Modo de operação
        ctk.CTkLabel(self, text="Modo:", font=("Courier", 11)).pack(anchor="w", padx=16)
        self.mode_var = ctk.StringVar(value="supervisionado")
        mode_frame = ctk.CTkFrame(self, fg_color="transparent")
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
        ctk.CTkLabel(self, text="Diretriz / Foco de melhoria:", font=("Courier", 11)).pack(anchor="w", padx=16, pady=(8,0))
        self.directive_entry = ctk.CTkEntry(self, font=("Courier", 12), fg_color="#1E1E2E", placeholder_text="Ex: Melhore sua inteligência...", text_color="#A6ACCD")
        self.directive_entry.pack(fill="x", padx=16, pady=4)
        self.directive_entry.bind("<KeyRelease>", self._update_directive)

        # Intervalo
        ctk.CTkLabel(self, text="Intervalo entre ciclos (min):",
                     font=("Courier", 11)).pack(anchor="w", padx=16, pady=(8,0))
        self.interval_slider = ctk.CTkSlider(
            self, from_=1, to=60, number_of_steps=59,
            command=self._on_interval_change,
            button_color="#00FFFF", button_hover_color="#00CCCC"
        )
        self.interval_slider.set(5)
        self.interval_slider.pack(fill="x", padx=16)

        # Log
        ctk.CTkLabel(self, text="LOG:", font=("Courier", 11), text_color="#00FFFF").pack(anchor="w", padx=16, pady=(12,2))
        self.log_box = ctk.CTkTextbox(self, height=180, font=("Courier", 11), fg_color="#1E1E2E", text_color="#A6ACCD")
        self.log_box.pack(fill="x", padx=16)
        self.log_box.configure(state="disabled")

        # Botões
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=16, pady=8)
        ctk.CTkButton(btn_frame, text="Ciclo Manual", command=self._manual_cycle,
                      font=("Courier", 12), fg_color="#00FFFF", text_color="#11111B", hover_color="#00CCCC").pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Rollback Git", command=self._rollback,
                      font=("Courier", 12), fg_color="transparent", text_color="#F38BA8",
                      border_width=1, border_color="#F38BA8", hover_color="#583640").pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text="Ver Evidências", command=self._show_evidence,
                      font=("Courier", 12), fg_color="transparent", text_color="#A6ACCD",
                      border_width=1, border_color="#A6ACCD", hover_color="#2E2E3E").pack(side="left", padx=4)

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

    def _on_mode_change(self):
        mode = self.mode_var.get()
        self.mind.auto_mode = (mode != "supervisionado")
        if mode == "agressivo":
            self.mind.cycle_interval = 60
        else:
            self.mind.cycle_interval = int(self.interval_slider.get()) * 60
        self._log(f"→ Modo: {mode}")

    def _on_interval_change(self, val):
        self.mind.cycle_interval = int(val) * 60

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
