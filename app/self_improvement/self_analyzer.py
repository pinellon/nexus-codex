import os
import ast

class SelfAnalyzer:
    """Lê e entende o próprio código"""
    
    def get_project_snapshot(self, root=".", extensions=[".py"]) -> dict:
        snapshot = {}
        for dirpath, _, files in os.walk(root):
            # Ignora pastas do sistema
            if any(skip in dirpath for skip in [".git", "__pycache__", "venv", ".env", "data", "assets"]):
                continue
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    path = os.path.join(dirpath, file)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            snapshot[path] = f.read()
                    except:
                        pass
        return snapshot
    
    def get_structure_summary(self, snapshot: dict) -> str:
        """Cria um resumo da arquitetura para a IA decidir o que melhorar"""
        summary = "ESTRUTURA DO PROJETO NEXUS:\n"
        for path in snapshot.keys():
            size = len(snapshot[path].split("\n"))
            summary += f"- {path} ({size} linhas)\n"
        return summary

    def find_weak_points(self, snapshot: dict) -> list:
        """Agora retorna apenas dicas estruturais, deixando a decisão real para o NexusMind"""
        issues = []
        for path, code in snapshot.items():
            if len(code.split("\n")) > 300:
                issues.append(f"ARQUIVO_GRANDE: {path}")
            if "TODO" in code or "FIXME" in code:
                issues.append(f"PENDENCIA: {path} contém notas de melhoria pendente")
        return issues
