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
                "name": "Dependency Doctor",
                "subtitle": "Reparador de dependências e imports quebrados",
                "impact": "Alto",
                "risk": "Baixo",
                "time": "4 min",
                "confidence": "96%",
                "description": "Detecta módulos ausentes, versões incompatíveis e sugere correções automáticas."
            },
            {
                "name": "AutoFix Engine",
                "subtitle": "Correção automática de erros",
                "impact": "Muito Alto",
                "risk": "Médio",
                "time": "6 min",
                "confidence": "90%",
                "description": "Analisa tracebacks, localiza arquivos com erro e aplica correções em modo sandbox."
            },
            {
                "name": "Backup Guardian",
                "subtitle": "Backup, snapshot e rollback avançado",
                "impact": "Muito Alto",
                "risk": "Baixo",
                "time": "6 min",
                "confidence": "98%",
                "description": "Cria cópias de segurança antes de qualquer alteração importante."
            },
            {
                "name": "Log Intelligence",
                "subtitle": "Diagnóstico inteligente de logs",
                "impact": "Alto",
                "risk": "Baixo",
                "time": "5 min",
                "confidence": "96%",
                "description": "Transforma erros em diagnósticos claros com causa provável e solução sugerida."
            },
            {
                "name": "SiteForge",
                "subtitle": "Criador de sites HTML/CSS/JS",
                "impact": "Alto",
                "risk": "Médio",
                "time": "8 min",
                "confidence": "91%",
                "description": "Gera sites completos, landing pages, preview ao vivo e exportação ZIP."
            },
            {
                "name": "Plugin Hub",
                "subtitle": "Sistema de plugins do Nexus",
                "impact": "Muito Alto",
                "risk": "Médio",
                "time": "15 min",
                "confidence": "84%",
                "description": "Permite instalar, ativar, desativar e criar novos módulos independentes."
            },
            {
                "name": "UI Forge",
                "subtitle": "Criador de interfaces internas",
                "impact": "Alto",
                "risk": "Médio",
                "time": "7 min",
                "confidence": "89%",
                "description": "Cria novas telas, painéis e componentes visuais para o próprio Nexus."
            },
            {
                "name": "Theme Lab",
                "subtitle": "Criador de temas visuais",
                "impact": "Médio",
                "risk": "Baixo",
                "time": "5 min",
                "confidence": "97%",
                "description": "Permite criar e aplicar temas como Cyberpunk, Matrix, Deep Space e Red Alert."
            },
            {
                "name": "Voice Core",
                "subtitle": "Assistente de voz",
                "impact": "Alto",
                "risk": "Baixo",
                "time": "8 min",
                "confidence": "85%",
                "description": "Permite controlar o Nexus por comandos de voz."
            },
            {
                "name": "Agent Council",
                "subtitle": "Conselho de agentes IA",
                "impact": "Muito Alto",
                "risk": "Médio",
                "time": "12 min",
                "confidence": "86%",
                "description": "Faz vários agentes analisarem uma melhoria antes dela ser aplicada."
            },
            {
                "name": "AppForge",
                "subtitle": "Criador de aplicativos simples",
                "impact": "Alto",
                "risk": "Médio",
                "time": "12 min",
                "confidence": "87%",
                "description": "Cria mini apps com interface (ex.: calculadora, dashboard, contrato)."
            },
            {
                "name": "Code Surgeon",
                "subtitle": "Cirurgião de código",
                "impact": "Alto",
                "risk": "Médio",
                "time": "10 min",
                "confidence": "88%",
                "description": "Dividir arquivos grandes, refatorar, remover código morto, organizar imports."
            },
            {
                "name": "Project Architect",
                "subtitle": "Arquitetura do sistema",
                "impact": "Muito Alto",
                "risk": "Alto",
                "time": "15 min",
                "confidence": "82%",
                "description": "Sugere nova estrutura de pastas, padrões de projeto, separação UI/lógica."
            },
            {
                "name": "Memory Map",
                "subtitle": "Mapa da memória do Nexus",
                "impact": "Alto",
                "risk": "Baixo",
                "time": "6 min",
                "confidence": "93%",
                "description": "Mostra aprendizados, erros corrigidos, módulos criados, decisões tomadas."
            },
            {
                "name": "Command Studio",
                "subtitle": "Criador de comandos personalizados",
                "impact": "Alto",
                "risk": "Baixo",
                "time": "6 min",
                "confidence": "92%",
                "description": "Define novos comandos que acionam módulos como SiteForge."
            },
            {
                "name": "Task Agent",
                "subtitle": "Automações de rotina",
                "impact": "Médio",
                "risk": "Baixo",
                "time": "5 min",
                "confidence": "95%",
                "description": "Limpar cache, gerar relatórios, backup, organizar arquivos."
            },
            {
                "name": "Watchtower",
                "subtitle": "Monitoramento avançado",
                "impact": "Alto",
                "risk": "Baixo",
                "time": "7 min",
                "confidence": "94%",
                "description": "Mostra CPU, RAM, disco, processos, erros recentes, módulos carregados."
            },
            {
                "name": "IconSmith",
                "subtitle": "Criador de ícones internos",
                "impact": "Médio",
                "risk": "Baixo",
                "time": "4 min",
                "confidence": "95%",
                "description": "Gera ícones SVG, aplica estilo neon, salva temas de ícones."
            },
            {
                "name": "Prompt Forge",
                "subtitle": "Criador de prompts internos",
                "impact": "Alto",
                "risk": "Médio",
                "time": "7 min",
                "confidence": "89%",
                "description": "Cria e otimiza prompts para agentes, salva versões aprovadas."
            },
            {
                "name": "Deploy Pilot",
                "subtitle": "Publicador de projetos",
                "impact": "Alto",
                "risk": "Médio",
                "time": "9 min",
                "confidence": "86%",
                "description": "Prepara build, gera ZIP, valida arquivos e prepara deploy."
            }
        ]
        
        for idea in ideas:
            card = ctk.CTkFrame(self.ideas_frame, fg_color="#1E1E2E", corner_radius=8)
            card.pack(fill="x", pady=6, padx=4)
            
            # Top row
            top_row = ctk.CTkFrame(card, fg_color="transparent")
            top_row.pack(fill="x", padx=12, pady=(12, 4))
            ctk.CTkLabel(top_row, text=idea["name"] + " — " + idea["subtitle"], font=("Courier", 13, "bold"), text_color="#00FFFF").pack(side="left")
            
            # Descrição row
            desc_row = ctk.CTkFrame(card, fg_color="transparent")
            desc_row.pack(fill="x", padx=12, pady=4)
            ctk.CTkLabel(desc_row, text=idea["description"], font=("Courier", 11), text_color="#A6ACCD", justify="left").pack(side="left")
            
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
        dlg.geometry("450x350")
        CTkLabel(dlg, text=idea["name"], font=("Courier", 14, "bold"), text_color="#00FFFF").pack(pady=(10, 5))
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
        import tkinter.messagebox as messagebox
        import os, uuid, shutil
        pm = PermissionManager()
        ok = pm.ask_permission(
            title=f"Criar {idea['name']}?",
            message=f"Posso criar esse módulo agora em modo sandbox?\nArquivos afetados previstos: ~5\nRisco: {idea['risk']}",
            parent=self.winfo_toplevel()
        )
        if not ok:
            return

        # 1. criar sandbox
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        sandbox_mgr = SandboxManager(project_root)
        sandbox_dir = sandbox_mgr.create_sandbox()

        # 2. gerar arquivos de módulo dentro do sandbox
        module_name = idea['name'].lower().replace(' ', '_').replace('—', '').replace('-', '_')
        module_path = os.path.join(sandbox_dir, "app", module_name)
        os.makedirs(module_path, exist_ok=True)
        init_file = os.path.join(module_path, "__init__.py")
        with open(init_file, "w", encoding="utf-8") as f:
            f.write(f"# Auto‑gerado por Nexus – {idea['name']}\n\n")
        # exemplo de arquivo principal
        main_file = os.path.join(module_path, f"{module_name}.py")
        with open(main_file, "w", encoding="utf-8") as f:
            f.write("def main():\n    print('Módulo criado com sucesso')\n\nif __name__ == '__main__':\n    main()\n")
        # 3. validar no sandbox (rodar pytest)
        if not sandbox_mgr.validate_sandbox():
            sandbox_mgr.discard_sandbox()
            messagebox.showerror("Falha nos testes", "Os testes falharam no sandbox. Operação abortada.")
            return
            
        # 4. aplicar ao live
        try:
            sandbox_mgr.apply_to_live()
        except Exception as e:
            messagebox.showerror("Erro ao aplicar", f"Falha ao mover sandbox para live: {e}")
            return
            
        # 5. atualizar score (optional)
        ScoreEngine(project_root).evaluate_system()
        messagebox.showinfo("Sucesso", f"Módulo '{idea['name']}' criado e aplicado.")
        # opcional: remover card
        card.destroy()

    def _ignore_idea(self, card):
        card.destroy()
