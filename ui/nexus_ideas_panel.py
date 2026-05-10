import customtkinter as ctk

class NexusIdeasPanel(ctk.CTkFrame):
    def __init__(self, master, settings, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.settings = settings
        self._build_ui()
        self._load_ideas()

    def _build_ui(self):
        # Título
        ctk.CTkLabel(self, text="NEXUS IDEAS",
                     font=("Courier", 16, "bold"), text_color="#00FFFF").pack(anchor="w", padx=16, pady=(16,4))
        
        ctk.CTkLabel(self, text="Sugestões de novos módulos geradas autonomamente pelo Nexus.",
                     font=("Courier", 11), text_color="#A6ACCD").pack(anchor="w", padx=16, pady=(0,8))

        # Lista de ideias
        self.ideas_frame = ctk.CTkScrollableFrame(self)
        self.ideas_frame.pack(fill="both", expand=True, padx=16, pady=8)

    def _load_ideas(self):
        # Limpar existentes
        for w in self.ideas_frame.winfo_children():
            w.destroy()
            
        ideas = [
            {
                "title": "SiteForge — Criador de sites HTML/CSS/JS",
                "impact": "Alto", "risk": "Médio", "time": "8 min", "confidence": "91%"
            },
            {
                "title": "Voice Core — Assistente de Voz",
                "impact": "Alto", "risk": "Baixo", "time": "5 min", "confidence": "85%"
            },
            {
                "title": "Task Agent — Automações de Rotina",
                "impact": "Médio", "risk": "Baixo", "time": "3 min", "confidence": "95%"
            },
            {
                "title": "AI Doc Generator — Documentação automática",
                "impact": "Alto", "risk": "Baixo", "time": "6 min", "confidence": "88%"
            },
            {
                "title": "Code Refactorer — Refatoração inteligente",
                "impact": "Alto", "risk": "Médio", "time": "7 min", "confidence": "84%"
            },
            {
                "title": "Data Visualizer — Dashboards interativos",
                "impact": "Médio", "risk": "Baixo", "time": "5 min", "confidence": "90%"
            },
            {
                "title": "Plugin System — Arquitetura extensível",
                "impact": "Alto", "risk": "Alto", "time": "10 min", "confidence": "80%"
            }
        ]
        
        for idea in ideas:
            card = ctk.CTkFrame(self.ideas_frame, fg_color="#1E1E2E", corner_radius=8)
            card.pack(fill="x", pady=6, padx=4)
            
            # Top row
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=12, pady=(12, 4))
            ctk.CTkLabel(top_row, text=idea["title"], font=("Courier", 13, "bold"), text_color="#00FFFF").pack(side="left")
            
            # Meta row
            meta_row = ctk.CTkFrame(card, fg_color="transparent")
            meta_row.pack(fill="x", padx=12, pady=4)
            
            def meta_label(parent, label, value, color):
                lbl = ctk.CTkLabel(parent, text=f"{label}: {value} | ", font=("Courier", 11), text_color=color)
                lbl.pack(side="left")
                
            meta_label(meta_row, "Impacto", idea["impact"], "#A6ACCD")
            meta_label(meta_row, "Risco", idea["risk"], "#F38BA8" if idea["risk"] == "Alto" else "#F9E2AF")
            meta_label(meta_row, "Tempo", idea["time"], "#A6ACCD")
            meta_label(meta_row, "Confiança", idea["confidence"], "#A6E3A1")
            
            # Action row
            action_row = ctk.CTkFrame(card, fg_color="transparent")
            action_row.pack(fill="x", padx=12, pady=(4, 12))
            
            ctk.CTkButton(action_row, text="Analisar", width=80, height=24, font=("Courier", 11),
                              fg_color="transparent", border_width=1, text_color="#00FFFF", border_color="#00FFFF",
                              hover_color="#181825",
                              command=lambda i=idea, c=card: self._analyze_idea(i, c)).pack(side="left", padx=(0, 8))

            ctk.CTkButton(action_row, text="Criar agora", width=100, height=24, font=("Courier", 11, "bold"),
                              fg_color="#00FFFF", text_color="#11111B", hover_color="#00CCCC",
                              command=lambda i=idea, c=card: self._create_module(i, c)).pack(side="left", padx=8)

            ctk.CTkButton(action_row, text="Ignorar", width=80, height=24, font=("Courier", 11),
                              fg_color="transparent", text_color="#6C7086", hover_color="#181825",
                              command=lambda c=card: self._ignore_idea(c)).pack(side="right")

    def _analyze_idea(self, idea, card):
        # Show a simple modal with the plan details (placeholder)
        from customtkinter import CTkToplevel, CTkLabel, CTkButton
        dlg = CTkToplevel(self)
        dlg.title("Plano da Ideia")
        dlg.geometry("400x300")
        CTkLabel(dlg, text=idea["title"], font=("Courier", 14, "bold"), text_color="#00FFFF").pack(pady=(10, 5))
        # Placeholder plan details
        CTkLabel(dlg, text="[Plano sugerido]\n\nImpacto: {}\nRisco: {}\nTempo: {}\nConfiança: {}".format(
            idea["impact"], idea["risk"], idea["time"], idea["confidence"]),
            font=("Courier", 11), text_color="#A6ACCD", justify="left").pack(pady=5, padx=10)
        CTkButton(dlg, text="Fechar", command=dlg.destroy,
                  fg_color="#00FFFF", text_color="#11111B").pack(pady=10)
        dlg.grab_set()
        dlg.wait_window()

    def _create_module(self, idea, card):
        from app.self_improvement.permission_manager import PermissionManager
        from app.self_improvement.sandbox_manager import SandboxManager
        from app.self_improvement.score_engine import ScoreEngine
        from CTkMessagebox import CTkMessagebox
        import os, uuid, shutil
        pm = PermissionManager()
        ok = pm.ask_permission(
            title=f"Criar {idea['title']}?",
            message=f"Posso criar esse módulo agora em modo sandbox?\nArquivos afetados previstos: ~5\nRisco: {idea['risk']}",
            parent=self.winfo_toplevel()
        )
        if not ok:
            return
        # 1. criar sandbox
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        sandbox_mgr = SandboxManager(project_root)
        sandbox_dir = sandbox_mgr.create_sandbox()
        # 2. gerar arquivos de módulo dentro do sandbox
        module_name = idea['title'].lower().replace(' ', '_').replace('—', '').replace('-', '_')
        module_path = os.path.join(sandbox_dir, "app", module_name)
        os.makedirs(module_path, exist_ok=True)
        init_file = os.path.join(module_path, "__init__.py")
        with open(init_file, "w", encoding="utf-8") as f:
            f.write(f"# Auto‑gerado por Nexus – {idea['title']}\n\n")
        # exemplo de arquivo principal
        main_file = os.path.join(module_path, f"{module_name}.py")
        with open(main_file, "w", encoding="utf-8") as f:
            f.write("def main():\n    print('Módulo criado com sucesso')\n\nif __name__ == '__main__':\n    main()\n")
        # 3. validar no sandbox (rodar pytest)
        if not sandbox_mgr.validate_sandbox():
            sandbox_mgr.discard_sandbox()
            CTkMessagebox(self, title="Falha nos testes", message="Os testes falharam no sandbox. Operação abortada.", icon="cancel")
            return
        # 4. aplicar ao live
        sandbox_mgr.apply_to_live()
        # 5. atualizar score (optional)
        ScoreEngine(project_root).evaluate_system()
        CTkMessagebox(self, title="Sucesso", message=f"Módulo '{idea['title']}' criado e aplicado.", icon="check")
        # opcional: remover card
        card.destroy()

    def _ignore_idea(self, card):
        card.destroy()
