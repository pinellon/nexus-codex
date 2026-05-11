# app/module_lister.py

import os


def list_modules(base_path: str):
    """Lista os módulos do sistema."""
    print("Modulos no sistema:")
    for root, dirs, files in os.walk(base_path):
        for file in files:
            if file.endswith('.py'):
                module_path = os.path.join(root, file)
                relative_path = os.path.relpath(module_path, base_path)
                print(relative_path.replace(os.sep, '.')[:-3])

if __name__ == '__main__':
    list_modules(os.path.dirname(os.path.abspath(__file__)))