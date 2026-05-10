"""Logger simples com arquivo e leitura recente."""

from datetime import datetime
from app.config import LOGS_DIR

LOG_FILE = LOGS_DIR / "nexus.log"


def _write(kind: str, message: str):
    LOGS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    LOG_FILE.open("a", encoding="utf-8").write(f"[{stamp}] [{kind}] {message}\n")


def log_action(message: str):
    _write("ACAO", message)


def log_command(message: str):
    _write("COMANDO", message)


def log_error(message: str):
    _write("ERRO", message)


def log_debug(message: str):
    _write("DEBUG", message)


def get_recent_logs(limit: int = 200) -> list[str]:
    try:
        lines = LOG_FILE.read_text(encoding="utf-8", errors="replace").splitlines()
        return lines[-limit:]
    except Exception:
        return []


class _Logger:
    def info(self, message: str):
        log_action(message)

    def debug(self, message: str):
        log_debug(message)

    def error(self, message: str):
        log_error(message)

    def exception(self, message: str):
        log_error(message)


logger = _Logger()
