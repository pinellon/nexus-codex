# app/meus_modulos.py

"""
Este módulo fornece uma visão geral dos principais módulos e funcionalidades da aplicação Nexus-Mind.
"""

MODULES_DESCRIPTION = {
    'config': 'Carrega e processa as configurações da aplicação.',
    'logs': 'Gerencia o sistema de logging para as operações do Nexus-Mind.',
    'voice.listener': 'Responsável por escutar comandos de voz do usuário.',
    'voice.speaker': 'Responsável pela síntese de voz, emitindo respostas ao usuário.',
    'core.command_router': 'Roteia os comandos de entrada para os módulos apropriados.',
    'chat.chat_engine': 'Processa entradas de chat e gerencia diálogos.',
    'theme': 'Gerencia a execução em modo temático.',
    'main': 'Ponto de entrada do sistema, orquestrando modos de operação.'
}

def listar_modulos():
    """Imprime uma lista dos módulos e suas descrições."""
    for module, description in MODULES_DESCRIPTION.items():
        print(f"{module}: {description}")

if __name__ == "__main__":
    listar_modulos()