from datetime import datetime
import logging
import os
from typing import List, Dict

class SelfAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger('nexus.self_analyzer')
        self.performance_metrics = {}
    
    # ---------- Performance ----------
    def analyze_performance(self):
        """Analisa métricas de desempenho e atualiza o banco de dados interno."""
        try:
            current_time = datetime.now()
            cpu_usage = self.get_cpu_usage()
            memory_usage = self.get_memory_usage()
            self.update_metrics(current_time, cpu_usage, memory_usage)
            self.generate_insights()
        except Exception as e:
            self.logger.error(f'Erro durante a análise de desempenho: {e}')
    
    def get_cpu_usage(self):
        # TODO: implement real CPU usage (e.g., psutil)
        return 42
    
    def get_memory_usage(self):
        # TODO: implement real memory usage
        return 1234
    
    def update_metrics(self, timestamp, cpu_usage, memory_usage):
        """Atualiza o dicionário de métricas com os valores atuais."""
        self.performance_metrics[timestamp] = {'cpu': cpu_usage, 'memory': memory_usage}
        self.logger.info(f'Métricas atualizadas: tempo={timestamp}, cpu={cpu_usage}, memória={memory_usage}')
    
    def generate_insights(self):
        """Gera insights baseados em métricas coletadas."""
        if not self.performance_metrics:
            return
        average_cpu = sum(m['cpu'] for m in self.performance_metrics.values()) / len(self.performance_metrics)
        if average_cpu > 50:
            self.logger.warning('O uso médio de CPU está alto. Considerando otimizações de processo.')
    
    # ---------- Code analysis ----------
    def get_project_snapshot(self, root: str = ".", extensions: List[str] = None) -> Dict[str, str]:
        """Varre o diretório do projeto e devolve {caminho: conteúdo} para arquivos .py."""
        if extensions is None:
            extensions = [".py"]
        snapshot = {}
        for dirpath, _, files in os.walk(root):
            if any(skip in dirpath for skip in [".git", "__pycache__", "venv", ".env", "data", "assets"]):
                continue
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    path = os.path.join(dirpath, file)
                    try:
                        with open(path, "r", encoding="utf-8") as f:
                            snapshot[path] = f.read()
                    except Exception as exc:
                        self.logger.warning(f"Não foi possível ler {path}: {exc}")
        return snapshot
    
    def get_structure_summary(self, snapshot: Dict[str, str]) -> str:
        """Resumo legível da arquitetura para uso no prompt da IA."""
        lines = ["ESTRUTURA DO PROJETO NEXUS:"]
        for path, content in snapshot.items():
            lines.append(f"- {path} ({len(content.splitlines())} linhas)")
        return "\n".join(lines)
    
    def find_weak_points(self, snapshot: Dict[str, str]) -> List[str]:
        """Detecta problemas simples: arquivos grandes ou TODO/FIXME."""
        issues = []
        for path, code in snapshot.items():
            if len(code.splitlines()) > 300:
                issues.append(f"ARQUIVO_GRANDE: {path}")
            if "TODO" in code or "FIXME" in code:
                issues.append(f"PENDENCIA: {path} contém notas de melhoria")
        return issues

# Example usage
complexity = self_analyzer.analyze_module_complexity(module)
print(f"Complexity of {module}: {complexity}")
print(f"Improvement suggestions: {self_analyzer.suggest_improvements(module)}")