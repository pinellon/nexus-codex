class ContextMemory:
    def __init__(self):
        self.memory = {}

    def remember(self, key: str, value: any) -> None:
        self.memory[key] = value

    def recall(self, key: str) -> any:
        return self.memory.get(key, None)

    def forget(self, key: str) -> None:
        if key in self.memory:
            del self.memory[key]

    def clear(self) -> None:
        self.memory.clear()