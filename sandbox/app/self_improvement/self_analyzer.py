# SelfAnalyzer implementation

class SelfAnalyzer:
    def __init__(self, config, logger=None):
        self.config = config
        self.logger = logger

    # ---------------------------------------------------------------------
    # Project snapshot utilities (required by NexusMind)
    # ---------------------------------------------------------------------
    def get_project_snapshot(self) -> dict:
        """Return a simple snapshot of the project files (path -> content)."""
        import os
        snapshot = {}
        # Project root is two levels up from this file (app/self_improvement)
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        for dirpath, _, filenames in os.walk(root):
            for fname in filenames:
                if fname.startswith('.'):
                    continue
                fpath = os.path.join(dirpath, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        snapshot[os.path.relpath(fpath, root)] = f.read()
                except Exception:
                    continue
        return snapshot

    def get_structure_summary(self, snapshot: dict) -> str:
        """Generate a brief summary of the project structure from the snapshot."""
        total_files = len(snapshot)
        total_size = sum(len(content) for content in snapshot.values())
        return f"Projeto contém {total_files} arquivos, ~{total_size // 1024}KB de código."

    def find_weak_points(self, snapshot: dict) -> str:
        """Identify simple weak points (e.g., large files over 200KB)."""
        weak = []
        for path, content in snapshot.items():
            if len(content) > 200 * 1024:
                weak.append(path)
        if not weak:
            return "Nenhum ponto fraco evidente encontrado."
        return "Arquivos grandes: " + ", ".join(weak)

    # ---------------------------------------------------------------------
    # Analysis helpers used by NexusMind
    # ---------------------------------------------------------------------
    def analyze_codebase_structure(self):
        issues = {}
        issues['large_files'] = self._detect_large_files()
        issues['pending_improvements'] = self._find_pending_improvements()
        if self.logger:
            self.logger.info('Analysis Complete')
        return issues

    def get_cpu_usage(self) -> float:
        """Retorna o uso de CPU em percentual usando ``psutil`` quando disponível."""
        try:
            import psutil
            return psutil.cpu_percent(interval=0.1)
        except Exception:
            if self.logger:
                self.logger.warning('psutil não encontrado, usando valor placeholder para CPU')
            return 0.0

    def get_memory_usage(self) -> float:
        """Retorna o uso de memória em MB usando ``psutil`` quando disponível."""
        try:
            import psutil
            mem = psutil.virtual_memory().used
            return mem / (1024 * 1024)
        except Exception:
            if self.logger:
                self.logger.warning('psutil não encontrado, usando valor placeholder para memória')
            return 0.0

    def _detect_large_files(self):
        # Placeholder implementation – real logic could scan for files > 1 MB
        return ['./app/home/home_commands.py', './coding/scaffolder.py']

    def _find_pending_improvements(self):
        # Placeholder implementation – could look for TODO comments
        return ['./app/vision/analyzer.py', './coding/code_assistant.py']

    def suggest_refactorings(self, issues):
        suggestions = []
        for issue, files in issues.items():
            for file in files:
                suggestions.append(f'Suggested refactoring for {file} due to {issue}')
        return suggestions

# Convenience wrapper used by external scripts
def perform_analysis_and_improvement(config, logger=None):
    analyzer = SelfAnalyzer(config, logger)
    issues = analyzer.analyze_codebase_structure()
    suggestions = analyzer.suggest_refactorings(issues)
    if logger:
        for suggestion in suggestions:
            logger.info(suggestion)
    return suggestions