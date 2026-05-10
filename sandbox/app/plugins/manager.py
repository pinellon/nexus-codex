"""Plugin manager leve para comandos novos sem mexer no nucleo."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import importlib.util


@dataclass(frozen=True)
class PluginCommand:
    name: str
    description: str
    handler: object


class PluginManager:
    def __init__(self, plugins_dir: str | Path = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self.commands: dict[str, PluginCommand] = {}

    def register(self, name: str, description: str, handler):
        self.commands[name] = PluginCommand(name, description, handler)

    def discover(self):
        if not self.plugins_dir.exists():
            return
        for file in self.plugins_dir.glob("*.py"):
            if file.name.startswith("_"):
                continue
            self._load_file(file)

    def execute(self, name: str, *args, **kwargs):
        command = self.commands.get(name)
        if not command:
            return f"Plugin nao encontrado: {name}"
        return command.handler(*args, **kwargs)

    def list_commands(self) -> str:
        if not self.commands:
            return "Nenhum plugin carregado."
        return "\n".join(f"- {cmd.name}: {cmd.description}" for cmd in self.commands.values())

    def _load_file(self, file: Path):
        spec = importlib.util.spec_from_file_location(f"nexus_plugin_{file.stem}", file)
        if not spec or not spec.loader:
            return
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        register = getattr(module, "register", None)
        if callable(register):
            register(self)
