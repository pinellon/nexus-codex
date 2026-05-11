import os

class ModuleLister:
    def __init__(self, directory):
        self.directory = directory

    def list_modules(self):
        imported_modules = set()
        for root, _, files in os.walk(self.directory):
            for file in files:
                if file.endswith('.py'):
                    with open(os.path.join(root, file), 'r') as f:
                        for line in f:
                            if line.startswith('import') or line.startswith('from'):
                                module_name = line.split()[1]
                                if module_name and module_name not in imported_modules:
                                    imported_modules.add(module_name)
        return imported_modules