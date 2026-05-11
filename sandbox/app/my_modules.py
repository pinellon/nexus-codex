# my_modules.py

"""Módulo responsável por listar e gerenciar módulos do sistema NEXUS."""

import os


class ModuleManager:
    def __init__(self, base_path: str):
        self.base_path = base_path

    def list_modules(self) -> list[str]:
        """List all Python modules in the base path."""
        modules = []
        for root, _, files in os.walk(self.base_path):
            py_files = [f for f in files if f.endswith('.py')]
            for file in py_files:
                relative_path = os.path.relpath(root, self.base_path)
                if relative_path == '.':
                    module_name = file.replace('.py', '')
                else:
                    module_name = '.'.join([relative_path.replace(os.sep, '.'), file.replace('.py', '')])
                modules.append(module_name)
        return modules

# Exemplo de uso
if __name__ == "__main__":
    manager = ModuleManager(base_path=".")
    print("Modulos encontrados:", manager.list_modules())