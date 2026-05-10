# Histórico de comandos para o NEXUS

from datetime import datetime

class CommandHistory:
    def __init__(self):
        self.history = []
    
    def add_command(self, command, response):
        """Adiciona um comando ao histórico."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.history.append({'timestamp': timestamp, 'command': command, 'response': response})
    
    def get_history(self):
        """Retorna o histórico completo de comandos."""
        return self.history

# Exemplo de uso
if __name__ == '__main__':
    ch = CommandHistory()
    ch.add_command('ligar luz', 'comando executado')
    ch.add_command('aumentar volume', 'comando executado')
    print(ch.get_history())
