import subprocess
import os
import json
from datetime import datetime

class FileTracker:
    HISTORY_PATH = "data/nexus_file_history.json"

    def __init__(self):
        os.makedirs("data", exist_ok=True)
        self._load()

    def _load(self):
        try:
            with open(self.HISTORY_PATH, "r", encoding="utf-8") as f:
                self.history = json.load(f)
        except:
            self.history = []

    def _save(self):
        with open(self.HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def record_cycle(self, files_changed: list, summary: str):
        """Registra um ciclo com os arquivos que foram tocados"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "files": files_changed  # lista de {"path": ..., "action": "edit/create/delete"}
        }
        self.history.insert(0, entry)
        self.history = self.history[:50]  # guarda últimos 50 ciclos
        self._save()

    def get_git_changed_files(self) -> list:
        """Pega arquivos realmente modificados no último commit"""
        try:
            r = subprocess.run(
                ["git", "show", "--name-status", "--format=", "HEAD"],
                capture_output=True, text=True, encoding="utf-8"
            )
            files = []
            for line in r.stdout.strip().split("\n"):
                if not line.strip():
                    continue
                parts = line.split("\t")
                if len(parts) >= 2:
                    status_map = {"M": "edit", "A": "create", "D": "delete"}
                    status = status_map.get(parts[0], "edit")
                    files.append({"path": parts[1], "action": status})
            return files
        except Exception as e:
            return []

    def open_in_explorer(self, filepath: str):
        """Abre a pasta do arquivo no explorador do Windows"""
        import subprocess
        folder = os.path.dirname(os.path.abspath(filepath))
        subprocess.Popen(f'explorer "{folder}"')

    def open_file(self, filepath: str):
        """Abre o arquivo no editor padrão"""
        os.startfile(os.path.abspath(filepath))
