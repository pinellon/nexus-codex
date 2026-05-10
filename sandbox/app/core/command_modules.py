class CommandModule:
    def __init__(self, settings, logger):
        self.settings = settings
        self.logger = logger

    def execute(self, command):
        raise NotImplementedError("Execute deve ser implementado por subclasses")


class SleepCommandModule(CommandModule):
    def execute(self, command):
        if command.intent == "sleep":
            print("Sistema indo dormir...")
            return True
        return False


# Outros módulos de comando podem ser adicionados aqui
