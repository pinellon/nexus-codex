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
                          hover_color="#181825").pack(side="left", padx=(0, 8))
                          
            ctk.CTkButton(action_row, text="Criar agora", width=100, height=24, font=("Courier", 11, "bold"),
                          fg_color="#00FFFF", text_color="#11111B", hover_color="#00CCCC",
                          command=lambda t=idea["title"]: self._create_module(t)).pack(side="left", padx=8)
                          
            ctk.CTkButton(action_row, text="Ignorar", width=80, height=24, font=("Courier", 11),
                          fg_color="transparent", text_color="#6C7086", hover_color="#181825").pack(side="right")

    def _create_module(self, title):
        from app.self_improvement.permission_manager import PermissionManager
        
        pm = PermissionManager()
        pm.ask_permission(
            title=f"Criar {title}?",
            message=f"Posso criar esse módulo agora em modo sandbox?\nArquivos afetados previstos: ~5\nRisco: Médio",
            parent=self.winfo_toplevel()
        )
