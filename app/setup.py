# app/setup.py

from app.config import load_settings
from app.logs.nexus_logger import build_logger


def setup_environment():
    """Configura o ambiente carregando as configurações e o logger."""
    settings = load_settings()
    logger = build_logger(settings.log_file)
    return settings, logger
