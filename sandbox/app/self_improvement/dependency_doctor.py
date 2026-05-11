import importlib.util
import json
import os

class NexusModuleLoader:
    """Carregador seguro de módulos com logging avançado de incompatibilidades."""
    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.compatibility_file = os.path.join(root_dir, "data", "compatibility_memory.json")
        self.memory = self._load_memory()
        
    def _load_memory(self):
        if os.path.exists(self.compatibility_file):
            with open(self.compatibility_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "pylint.epylint": {
                "status": "deprecated",
                "replacement": "pylint.lint.Run"
            }
        }
        
    def _save_memory(self):
        os.makedirs(os.path.dirname(self.compatibility_file), exist_ok=True)
        with open(self.compatibility_file, 'w', encoding='utf-8') as f:
            json.dump(self.memory, f, indent=2)

    def safe_import(self, module_name):
        try:
            # Check compatibility memory first
            if module_name in self.memory:
                record = self.memory[module_name]
                if record.get("status") == "deprecated":
                    raise ImportError(f"O módulo {module_name} foi deprecado. Use {record.get('replacement')} no lugar.")
            
            module = __import__(module_name)
            return module
        except Exception as e:
            self.log_error(module_name, e)
            return None
            
    def log_error(self, module_name, error):
        print(f"[NEXUS DIAGNOSTICS] Falha ao carregar o módulo: {module_name}. Erro: {error}")


class DependencyDoctor:
    """Analisa dependências quebradas e gerencia o ambiente."""
    def __init__(self, root_dir):
        self.root_dir = root_dir
        
    def check_dependencies(self, required_libs: list) -> dict:
        results = {}
        for lib in required_libs:
            # Algumas libs tem nomes diferentes do import (ex: pyqt5 -> PyQt5)
            # Vamos testar o import spec
            try:
                found = importlib.util.find_spec(lib) is not None
                results[lib] = found
            except Exception:
                results[lib] = False
        return results
        
    def generate_report(self, required_libs: list) -> dict:
        checks = self.check_dependencies(required_libs)
        broken = [lib for lib, ok in checks.items() if not ok]
        return {
            "checks": checks,
            "broken_count": len(broken),
            "broken_libs": broken
        }
