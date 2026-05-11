import customtkinter as ctk
import os
import importlib
import sys
import subprocess
import tkinter.messagebox as messagebox

class NexusPluginsPanel(ctk.CTkFrame):
    def __init__(self, master, settings, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.settings = settings
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.app_dir = os.path.join(self.project_root, "app")
        self._build_ui()
        self._load_plugins()

    def _build_ui(self):
        # Título
        ctk.CTkLabel(self, text="MÓDULOS INSTALADOS",
                     font=("Courier", 16, "bold"), text_color="#00FFFF").pack(anchor="w", padx=16, pady=(16,4))
        
        ctk.CTkLabel(self, text="Módulos autônomos criados pelo Nexus e instalados no sistema.",
                     font=("Courier", 11), text_color="#A6ACCD").pack(anchor="w", padx=16, pady=(0,8))

        # Lista de plugins
        self.plugins_frame = ctk.CTkScrollableFrame(self)
        self.plugins_frame.pack(fill="both", expand=True, padx=16, pady=8)
        
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.pack(fill="x", padx=16, pady=(0, 16))
        
        ctk.CTkButton(
            btn_row, text="Atualizar Lista",
            command=self._load_plugins,
            font=("Courier", 12), width=120,
            fg_color="transparent", border_width=1, border_color="#A6ACCD", text_color="#A6ACCD"
        ).pack(side="left")

    def _load_plugins(self):
        for w in self.plugins_frame.winfo_children():
            w.destroy()
            
        if not os.path.exists(self.app_dir):
            return
            
        plugins_found = False
        
        for item in os.listdir(self.app_dir):
            if item in ["__pycache__", "core", "voice", "self_improvement"]:
                continue
                
            module_path = os.path.join(self.app_dir, item)
            if not os.path.isdir(module_path):
                continue
                
            # Verifica se é um módulo criado (tem __init__.py)
            init_file = os.path.join(module_path, "__init__.py")
            if not os.path.exists(init_file):
                continue
                
            plugins_found = True
            
            card = ctk.CTkFrame(self.plugins_frame, fg_color="#1E1E2E", corner_radius=8)
            card.pack(fill="x", pady=6, padx=4)
            
            row = ctk.CTkFrame(card, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=12)
            
            ctk.CTkLabel(row, text=f"📦 {item}", font=("Courier", 14, "bold"), text_color="#A6E3A1").pack(side="left")
            
            # Action row
            ctk.CTkButton(row, text="Iniciar Módulo", width=120, height=28, font=("Courier", 12, "bold"),
                          fg_color="#00FFFF", text_color="#11111B", hover_color="#00CCCC",
                          command=lambda m=item, p=module_path: self._run_plugin(m, p)).pack(side="right", padx=(8, 0))
                          
            ctk.CTkButton(row, text="Abrir Pasta", width=100, height=28, font=("Courier", 12),
                          fg_color="transparent", text_color="#A6ACCD", hover_color="#181825",
                          border_width=1, border_color="#A6ACCD",
                          command=lambda p=module_path: self._open_folder(p)).pack(side="right")
                          
        if not plugins_found:
            ctk.CTkLabel(self.plugins_frame, text="Nenhum módulo autônomo instalado ainda.",
                         font=("Courier", 12), text_color="gray").pack(pady=20)

    def _open_folder(self, path):
        subprocess.Popen(f'explorer "{os.path.abspath(path)}"')
        
    def _run_plugin(self, module_name, module_path):
        main_file = os.path.join(module_path, f"{module_name}.py")
        if not os.path.exists(main_file):
            messagebox.showerror("Erro", f"Arquivo principal '{module_name}.py' não encontrado.")
            return
            
        try:
            # Roda o arquivo em um processo separado para não travar o Nexus
            subprocess.Popen([sys.executable, main_file], cwd=self.project_root)
            messagebox.showinfo("Sucesso", f"Módulo '{module_name}' iniciado em segundo plano!")
        except Exception as e:
            messagebox.showerror("Erro ao iniciar", f"Falha ao executar o módulo:\n{e}")
