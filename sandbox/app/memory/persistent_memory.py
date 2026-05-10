class PersistentMemory:
    def __init__(self, storage_file='memory.json'):
        self.storage_file = storage_file
        self.memory = self.load_memory()

    def load_memory(self):
        """Carrega a memória do arquivo de armazenamento."""
        try:
            with open(self.storage_file, 'r') as file:
                import json
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}

    def save_memory(self):
        """Salva a memória no arquivo de armazenamento."""
        with open(self.storage_file, 'w') as file:
            import json
            json.dump(self.memory, file, indent=4)

    def update_memory(self, key, value):
        """Atualiza ou adiciona um valor à memória com base na chave fornecida."""
        self.memory[key] = value
        self.save_memory()

    def get_memory(self, key, default=None):
        """Recupera um valor da memória com base na chave fornecida."""
        return self.memory.get(key, default)
