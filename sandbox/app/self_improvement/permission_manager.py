import customtkinter as ctk

class PermissionManager:
    def ask_permission(self, title: str, message: str, parent=None) -> bool:
        """Exibe um dialog solicitando permissão ao usuário."""
        # Podemos usar CTkMessagebox se estiver instalado, senão criamos um dialog customizado
        dialog = ctk.CTkToplevel(parent)
        dialog.title("NEXUS — PERMISSÃO NECESSÁRIA")
        dialog.geometry("400x250")
        
        # Manter sempre acima
        dialog.attributes("-topmost", True)
        # Focar
        dialog.focus_force()
        # Modal
        dialog.grab_set()
        
        # Centralizar na tela
        dialog.update_idletasks()
        if parent:
            x = parent.winfo_x() + (parent.winfo_width() // 2) - 200
            y = parent.winfo_y() + (parent.winfo_height() // 2) - 125
            dialog.geometry(f"+{x}+{y}")
            
        dialog.configure(fg_color="#11111B")
        
        ctk.CTkLabel(dialog, text=title, font=("Courier", 14, "bold"), text_color="#F9E2AF").pack(pady=(20, 10), padx=20)
        
        ctk.CTkLabel(dialog, text=message, font=("Courier", 12), text_color="#A6ACCD", justify="left").pack(pady=10, padx=20, fill="both", expand=True)
        
        self.result = False
        
        def on_allow():
            self.result = True
            dialog.destroy()
            
        def on_deny():
            self.result = False
            dialog.destroy()
            
        btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20, padx=20)
        
        ctk.CTkButton(btn_frame, text="Permitir", command=on_allow, fg_color="#A6E3A1", text_color="#11111B", hover_color="#94CC90", font=("Courier", 12, "bold")).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(btn_frame, text="Ver Plano", command=lambda: print("Mostrando plano..."), fg_color="transparent", border_width=1, border_color="#89B4FA", text_color="#89B4FA", hover_color="#1E1E2E", font=("Courier", 12)).pack(side="left", padx=10, expand=True)
        ctk.CTkButton(btn_frame, text="Cancelar", command=on_deny, fg_color="transparent", text_color="#F38BA8", hover_color="#1E1E2E", font=("Courier", 12)).pack(side="left", padx=10, expand=True)
        
        dialog.wait_window()
        return self.result
