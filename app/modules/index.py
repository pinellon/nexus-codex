# app/modules/index.py

"""
Este módulo serve como um índice centralizado para todos os módulos disponíveis dentro do sistema Nexus.
Pode ser usado para gerenciar e acessar módulos dinamicamente.
"""

MODULES = {
    'voice_listener': 'app.voice.listener.VoiceListener',
    'voice_speaker': 'app.voice.speaker.VoiceSpeaker',
    'command_router': 'app.core.command_router.CommandRouter',
    # Adicione outros módulos conforme necessário
}

def list_modules() -> list[str]:
    """Retorna uma lista dos módulos atualmente disponíveis."""
    return list(MODULES.keys())


def get_module(module_name: str) -> str:
    """Retorna o caminho do módulo a partir do nome registrado."""
    return MODULES.get(module_name)
