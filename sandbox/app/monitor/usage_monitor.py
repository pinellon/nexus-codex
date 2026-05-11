
class UsageMonitor:
    def __init__(self, logger):
        self.logger = logger
        self.usage_data = []

    def log_command(self, command):
        self.usage_data.append(command)
        self.logger.info(f"Command executed: {command}")

    def report(self):
        return {
            "total_commands": len(self.usage_data),
            "last_command": self.usage_data[-1] if self.usage_data else None
        }

    def detect_abnormalities(self):
        # Placeholder: Implement logic to detect anomalies in usage patterns
        pass
