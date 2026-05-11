# app/utils/module_utils.py

import os


def list_modules(root_dir):
    """Lista todos os módulos disponíveis no projeto."""
    modules = []
    for root, dirs, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.py'):
                module_path = os.path.join(root, file)
                modules.append(os.path.relpath(module_path, start=root_dir))
    return modules


def print_modules(root_dir):
    """Imprime todos os módulos listados."""
    modules = list_modules(root_dir)
    print("Módulos disponíveis no projeto:")
    for module in sorted(modules):
        print(module)