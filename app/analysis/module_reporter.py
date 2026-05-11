import os

class ModuleReporter:
    """Classe responsável por gerar relatórios sobre os módulos do sistema."""

    def __init__(self, base_path):
        self.base_path = base_path

    def list_modules(self):
        """Listar todos os módulos disponíveis na estrutura de diretórios."""
        modules = []
        for root, dirs, files in os.walk(self.base_path):
            for file in files:
                if file.endswith('.py'):
                    relative_path = os.path.relpath(os.path.join(root, file), self.base_path)
                    modules.append(relative_path)
        return modules

    def generate_report(self):
        """Gera um relatório descritivo dos módulos existentes."""
        modules = self.list_modules()
        report = f"Sistema contém {len(modules)} módulos:\n"
        for module in modules:
            report += f"- {module}\n"
        return report

# Exemplo de uso
if __name__ == "__main__":
    base_path = '.'  # Diretório atual
    reporter = ModuleReporter(base_path)
    print(reporter.generate_report())