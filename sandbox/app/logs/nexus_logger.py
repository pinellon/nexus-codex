import logging
from logging.handlers import RotatingFileHandler


def build_logger(log_file_path: str) -> logging.Logger:
    logger = logging.getLogger('nexus')
    logger.setLevel(logging.DEBUG)

    handler = RotatingFileHandler(log_file_path, maxBytes=1024*1024, backupCount=5)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger
