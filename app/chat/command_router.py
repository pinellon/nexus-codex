# command_router.py

from app.core.command_router import CommandRouter as BaseCommandRouter

class ChatCommandRouter(BaseCommandRouter):
    def route(self, text: str):
        """Roteia comandos de texto para respostas adequadas."""
        if 'ajuda' in text.lower():
            return self._create_command('ajuda', 'Fornecendo ajuda...', [])
        elif 'olá' in text.lower() or 'oi' in text.lower():
            return self._create_command('saudação', 'Olá! Como posso ajudar?', [])
        else:
            return self._create_command('desconhecido', 'Desculpe, não entendi.', [])

    def _create_command(self, intent, label, args):
        return type('Command', (), {'intent': intent, 'label': label, 'args': args})()