import subprocess
import sys
import os
import threading
import time

class RestartManager:
    def __init__(self, on_confirm_callback):
        """
        on_confirm_callback: função que mostra diálogo pro usuário
        deve retornar True se usuário confirmar, False se cancelar
        """
        self.on_confirm = on_confirm_callback
        self.pending = False

    def request_restart(self, reason: str):
        """NexusMind chama isso quando precisa reiniciar"""
        if self.pending:
            return  # já tem um pedido pendente
        self.pending = True
        # Roda em thread pra não travar o loop
        threading.Thread(
            target=self._ask_and_restart,
            args=(reason,),
            daemon=True
        ).start()

    def _ask_and_restart(self, reason: str):
        confirmed = self.on_confirm(reason)
        self.pending = False
        if confirmed:
            time.sleep(1)  # dá tempo pro diálogo fechar
            self._do_restart()

    def _do_restart(self):
        """Reinicia o processo Python atual"""
        python = sys.executable
        args = sys.argv[:]
        # Fecha o processo atual e abre um novo
        subprocess.Popen([python] + args)
        os._exit(0)

    def needs_restart_after(self, changed_files: list) -> bool:
        """Decide se precisa reiniciar baseado nos arquivos mudados"""
        critical = ["main.py", "app/core/", "app/voice/", "ui/"]
        for f in changed_files:
            path = f.get("path", "")
            if any(c in path for c in critical):
                return True
        return False
