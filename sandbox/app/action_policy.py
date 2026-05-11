"""Política central de segurança para ações do NEXUS."""

from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    requires_confirmation: bool = False
    message: str = ""
    reason: str = ""


_ALWAYS_CONFIRM = {
    "desligar_pc": "Desligar o computador agora?",
    "reiniciar_pc": "Reiniciar o computador agora?",
    "suspender_pc": "Suspender o computador agora?",
    "bloquear_tela": "Bloquear a tela agora?",
    "git_push": "Enviar alterações para o repositório remoto agora?",
    "git_pull": "Baixar alterações do repositório remoto agora?",
    "git_branch": "Criar ou trocar de branch agora?",
    "instalar_pacote": "Instalar este pacote agora?",
}

_BLOCKED_TERMINAL_PATTERNS = [
    r"\bformat\b",
    r"\bmkfs\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r"\bhalt\b",
    r"\bdiskpart\b",
    r"\bbcdedit\b",
    r"\bcipher\s+/w\b",
    r"\bdel\s+/f\s+/s\b",
    r"\brm\s+-rf\s+/(?:\s|$)",
    r"\breg\s+delete\b",
    r"\bsc\s+delete\b",
]

_CONFIRM_TERMINAL_PATTERNS = [
    r"\bdel\b",
    r"\berase\b",
    r"\brmdir\b",
    r"\brd\b",
    r"\brm\s+-r\b",
    r"\brm\s+-rf\b",
    r"\btaskkill\b",
    r"\bpip\s+install\b",
    r"\bnpm\s+install\b",
    r"\bwinget\s+install\b",
    r"\bchoco\s+install\b",
]

_SENSITIVE_APPS = {
    "cmd",
    "prompt de comando",
    "powershell",
    "terminal",
    "windows terminal",
    "regedit",
    "editor de registro",
    "services",
    "services.msc",
    "gpedit",
    "task scheduler",
    "agendador de tarefas",
}


def _normalize(text: str) -> str:
    base = unicodedata.normalize("NFKD", text or "")
    return "".join(ch for ch in base if not unicodedata.combining(ch)).lower().strip()


_SAFE = PolicyDecision(True, False, "", "")


def assess_terminal_command(command: str) -> PolicyDecision:
    text = _normalize(command)
    if not text:
        return PolicyDecision(False, False, reason="comando vazio")

    for pattern in _BLOCKED_TERMINAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return PolicyDecision(False, False, reason=f"comando bloqueado pela política: {pattern}")

    for pattern in _CONFIRM_TERMINAL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return PolicyDecision(True, True, f"Executar comando potencialmente destrutivo?\n\n{command}")

    if any(token in command for token in ["&&", "||", "|", ">", "<"]):
        return PolicyDecision(True, True, f"Executar comando shell composto?\n\n{command}")

    return _SAFE


def assess_app_launch(app_name: str) -> PolicyDecision:
    name = _normalize(app_name)
    if not name:
        return PolicyDecision(False, False, reason="nome do app vazio")
    if name in _SENSITIVE_APPS:
        return PolicyDecision(True, True, f"Abrir aplicativo sensível '{app_name}'?")
    return _SAFE


def assess_intent(intent_name: str, params: dict | None = None) -> PolicyDecision:
    params = params or {}
    if intent_name in _ALWAYS_CONFIRM:
        return PolicyDecision(True, True, _ALWAYS_CONFIRM[intent_name])

    if intent_name in {"abrir_app", "abrir_programa", "registrar_app"}:
        return assess_app_launch(params.get("app") or params.get("nome") or params.get("alias") or "")

    if intent_name == "terminal_exec":
        return assess_terminal_command(params.get("comando", ""))

    return _SAFE
