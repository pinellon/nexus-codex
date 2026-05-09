"""Módulo de automação residencial do NEXUS."""
from .home_assistant import HomeAssistantClient
from .spotify import SpotifyClient
from .home_commands import HomeCommandHandler, is_home_command

__all__ = ["HomeAssistantClient", "SpotifyClient", "HomeCommandHandler", "is_home_command"]
