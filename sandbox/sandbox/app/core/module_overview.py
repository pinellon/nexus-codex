
# module_overview.py

import pkgutil
import importlib


def list_modules(package_name):
    """Lista todos os módulos dentro de um pacote específico."""
    package = importlib.import_module(package_name)
    for importer, modname, ispkg in pkgutil.iter_modules(package.__path__):
        print(f"{package_name}.{modname} (Pacote: {ispkg})")


def main():
    """Função principal para listar módulos."""
    print("Módulos no sistema:")
    list_modules('app.voice')
    list_modules('app.logs')
    list_modules('app.core')
    list_modules('app.chat')


if __name__ == "__main__":
    main()
