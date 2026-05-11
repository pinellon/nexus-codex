import json
import os

class CommandMemory:
    def __init__(self, memory_file='data/command_memory.json'):
        self.memory_file = memory_file
        if not os.path.exists(self.memory_file):
            with open(self.memory_file, 'w') as f:
                json.dump([], f)

    def save_command(self, command, response):
        with open(self.memory_file, 'r+') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
            data.append({'command': command, 'response': response})
            f.seek(0)
            json.dump(data, f)

    def get_memory(self):
        with open(self.memory_file, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []