# plugin_system.py

"""Sistema de plugin para o NEXUS permitir maior modularidade e personalização."""

from typing import Callable, Dict

class PluginSystem:
    """Sistema de gerenciamento de plugins."""

    def __init__(self):
        self.plugins: Dict[str, Callable] = {}

    def register_plugin(self, name: str, handler: Callable):
        """Registra um novo plugin no sistema."""
        if name in self.plugins:
            raise ValueError(f"Plugin {name} já está registrado.")
        self.plugins[name] = handler

    def execute_plugin(self, name: str, *args, **kwargs):
        """Executa o plugin registrado pelo nome."""
        if name not in self.plugins:
            raise ValueError(f"Plugin {name} não encontrado.")
        return self.plugins[name](*args, **kwargs)

plugin_system = PluginSystem()
