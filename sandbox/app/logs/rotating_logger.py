import logging
from logging.handlers import RotatingFileHandler

class RotatingLogger:
    def __init__(self, log_file, max_bytes=1024*1024, backup_count=3):
        self.logger = logging.getLogger('nexus')
        self.logger.setLevel(logging.DEBUG)
        
        handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)

        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def log(self, level, message):
        if level == 'debug':
            self.logger.debug(message)
        elif level == 'info':
            self.logger.info(message)
        elif level == 'warning':
            self.logger.warning(message)
        elif level == 'error':
            self.logger.error(message)
        elif level == 'critical':
            self.logger.critical(message)

# Uso:
# from app.logs.rotating_logger import RotatingLogger
# logger = RotatingLogger('logs/nexus.log')
# logger.log('info', 'Este é um exemplo de log rotacional')
