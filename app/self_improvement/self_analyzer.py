from datetime import datetime
import logging
import os
from typing import List, Dict

class SelfAnalyzer:
    def __init__(self):
        self.logger = logging.getLogger('nexus.self_analyzer')
        self.performance_metrics = {}

    # ------------------------------------------------------------
    # Funções essenciais para análise de código (restauradas)
    # ------------------------------------------------------------
    def get_project_snapshot(self, root: str = ".", extensions: List[str] = None) -> Dict[str, str]:
        """Varre o diretório do projeto e retorna um dicionário {caminho: conteúdo}.
        Apenas arquivos com extensões listadas são incluídos (por padrão .py)."""
        if extensions is None:
            extensions = [".py"]
        snapshot = {}
        for dirpath, _, files in os.walk(root):
            # Ignora pastas que não contêm código fonte
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
        """Cria um resumo legível da arquitetura do projeto para ser usado no prompt da IA."""
        lines = ["ESTRUTURA DO PROJETO NEXUS:"]
        for path, content in snapshot.items():
            lines.append(f"- {path} ({len(content.splitlines())} linhas)")
        return "\n".join(lines)

    def find_weak_points(self, snapshot: Dict[str, str]) -> List[str]:
        """Detecta problemas simples: arquivos muito grandes ou que contenham TODO/FIXME."""
        issues = []
        for path, code in snapshot.items():
            if len(code.splitlines()) > 300:
                issues.append(f"ARQUIVO_GRANDE: {path}")
            if "TODO" in code or "FIXME" in code:
                issues.append(f"PENDENCIA: {path} contém notas de melhoria")
        return issues

    # ------------------------------------------------------------
    # Métricas de performance (mantidas) -----------------------
    # ------------------------------------------------------------
    def analyze_performance(self):
        """
        Analisa métricas de desempenho e atualiza o banco de dados interno.
        """
        try:
            current_time = datetime.now()
            # Suponha que temos funções para obter uso de CPU e de memória
            cpu_usage = self.get_cpu_usage()
            memory_usage = self.get_memory_usage()

            self.update_metrics(current_time, cpu_usage, memory_usage)
            self.generate_insights()
        except Exception as e:
            self.logger.error(f'Erro durante a análise de desempenho: {e}')

    def get_cpu_usage(self):
        # Implemente a lógica real de obtenção do uso de CPU
        return 42 # Exemplo de valor estático

    def get_memory_usage(self):
        # Implemente a lógica real de obtenção do uso de memória
        return 1234 # Exemplo de valor estático

    def update_metrics(self, timestamp, cpu_usage, memory_usage):
        """
        Atualiza o dicionário de métricas com os valores atuais.
        """
        self.performance_metrics[timestamp] = {'cpu': cpu_usage, 'memory': memory_usage}
        self.logger.info(f'Métricas atualizadas: tempo={timestamp}, cpu={cpu_usage}, memória={memory_usage}')

    def generate_insights(self):
        """
        Gera insights baseados em métricas coletadas e ajusta processos conforme necessário.
        """
        # Exemplo simplificado para análise
        average_cpu_usage = sum(item['cpu'] for item in self.performance_metrics.values()) / len(self.performance_metrics)
        if average_cpu_usage > 50:  # Threshold de exemplo
            self.logger.warning('O uso médio de CPU está alto. Considerando otimizações de processo.')