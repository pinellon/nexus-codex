from typing import Any, Dict

class TextCommand:
    def __init__(self, label: str, args: Dict[str, Any], intent: str):
        self.label = label
        self.args = args
        self.intent = intent

class TextRouter:
    def __init__(self, settings, logger):
        self.settings = settings
        self.logger = logger

    def route(self, text: str) -> TextCommand:
        # Simulação de roteamento simples para o comando de texto
        self.logger.info(f"Processando texto: {text}")
        if text.lower() in {'parar', 'sair', 'pausar'}:
            return TextCommand(label='comando_parada', args={}, intent='parar')
        else:
            return TextCommand(label='comando_generico', args={'texto': text}, intent='comando')