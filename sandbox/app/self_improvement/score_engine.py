import os
import json
from radon.complexity import cc_visit
import pylint.lint as lint
from io import StringIO
import sys

class ScoreEngine:
    def __init__(self, project_root: str):
        self.root = project_root
        self.score_file = os.path.join(self.root, "data", "system_score.json")

    def calculate_radon_score(self) -> float:
        """Calcula uma pontuação baseada na complexidade ciclomática do projeto."""
        scores = []
        for dirpath, _, files in os.walk(self.root):
            if "sandbox" in dirpath or "venv" in dirpath or ".git" in dirpath:
                continue
            for f in files:
                if f.endswith('.py'):
                    path = os.path.join(dirpath, f)
                    try:
                        with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                            blocks = cc_visit(fp.read())
                            scores.extend([b.complexity for b in blocks])
                    except Exception:
                        continue
        # Média da complexidade (quanto menor, melhor) -> converter para 0-100
        avg_complexity = (sum(scores) / len(scores)) if scores else 1.0
        # Formula heuristica: se complexidade media é 1, score é 100. Se for 10, score é 50.
        score = max(0, min(100, 100 - (avg_complexity - 1) * 5))
        return round(score, 2)

    def calculate_pylint_score(self) -> float:
        """Executa o pylint e retorna o score (0-100)."""
        # Para evitar lentidão, vamos analisar apenas pastas principais
        target_dir = os.path.join(self.root, "app")
        if not os.path.exists(target_dir):
            return 80.0
            
        old_stdout = sys.stdout
        sys.stdout = mystdout = StringIO()
        
        try:
            # We use Run with exit=False to prevent pylint from exiting the process
            lint.Run([target_dir, '--reports=y', '-s', 'y'], exit=False)
        except Exception as e:
            pass
        finally:
            sys.stdout = old_stdout
            
        output = mystdout.getvalue()
        
        # Procura por "Your code has been rated at X/10"
        score = 80.0
        for line in output.split('\n'):
            if "Your code has been rated at" in line:
                try:
                    parts = line.split("rated at ")[1].split("/10")
                    score = float(parts[0].strip()) * 10  # converte para 0-100
                except:
                    pass
                break
        return score

    def evaluate_system(self) -> dict:
        """Avalia todo o sistema e consolida as métricas."""
        radon = self.calculate_radon_score()
        plint = self.calculate_pylint_score()
        
        # Para simular métricas que ainda não temos (performance, memoria):
        system_score = {
            "maintainability": radon,
            "code_quality": plint,
            "performance": 85.0,   # Placeholder
            "memory_usage": 80.0,  # Placeholder
        }
        
        # Calcular média final
        total = sum(system_score.values()) / len(system_score)
        system_score["overall"] = round(total, 2)
        
        os.makedirs(os.path.dirname(self.score_file), exist_ok=True)
        with open(self.score_file, 'w', encoding='utf-8') as f:
            json.dump(system_score, f, indent=2)
            
        return system_score
        
    def get_last_score(self) -> dict:
        if os.path.exists(self.score_file):
            with open(self.score_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return self.evaluate_system()
