"""Terminal mais seguro: reduz shell=True e centraliza política de risco."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import os
import shlex
import shutil
import subprocess
import time

from app.action_policy import assess_terminal_command
from coding.file_manager import get_projeto

try:
    from app.logger import log_action
except ImportError:
    def log_action(text: str):  # type: ignore[override]
        print(text)


ALIASES = {
    "py": "python",
    "pip3": "pip",
    "ni": "npm install",
    "nr": "npm run",
    "nd": "npm run dev",
    "nb": "npm run build",
    "nt": "npm test",
    "gs": "git status",
    "ga": "git add .",
    "gp": "git push",
    "gl": "git pull",
    "glog": "git log --oneline -10",
    "gd": "git diff --stat",
    "ll": "dir",
    "pwd": "cd",
    "which": "where" if os.name == "nt" else "which",
}

_HISTORY: list[dict] = []
MAX_HISTORY = 100
_WINDOWS_BUILTINS = {"dir", "copy", "del", "erase", "type", "cls", "echo", "cd", "md", "mkdir", "rd", "rmdir", "ren", "move", "set", "start"}
_SHELL_OPERATORS = ["&&", "||", "|", ">", "<"]


@dataclass
class TermResult:
    success: bool
    output: str
    cmd: str
    elapsed: float = 0.0
    cwd: str = ""

    def format(self) -> str:
        status = "OK" if self.success else "ERRO"
        parts = [f"{status} {self.cmd}" + (f" ({self.elapsed:.2f}s)" if self.elapsed > 0.1 else "")]
        if self.output.strip():
            parts.append(self.output.strip())
        return "\n".join(parts)


def _add_history(cmd: str, success: bool, output: str):
    _HISTORY.append({"cmd": cmd, "success": success, "output": output, "time": datetime.now().strftime("%H:%M:%S")})
    if len(_HISTORY) > MAX_HISTORY:
        _HISTORY.pop(0)


def _expand_alias(command: str) -> str:
    parts = command.strip().split(maxsplit=1)
    if parts and parts[0] in ALIASES:
        return ALIASES[parts[0]] + (f" {parts[1]}" if len(parts) > 1 else "")
    return command


def _needs_shell(command: str) -> bool:
    lower = command.lower().strip()
    if any(token in command for token in _SHELL_OPERATORS):
        return True
    first = lower.split(maxsplit=1)[0] if lower else ""
    return os.name == "nt" and first in _WINDOWS_BUILTINS


def _build_command(command: str) -> list[str]:
    if _needs_shell(command):
        if os.name == "nt":
            return ["cmd", "/c", command]
        return ["bash", "-lc", command]
    return shlex.split(command, posix=(os.name != "nt"))


def executar(comando: str, cwd: str = "", timeout: int = 60, confirmar_callback=None) -> TermResult:
    comando = (comando or "").strip()
    if not comando:
        return TermResult(False, "Comando vazio.", comando)

    comando_final = _expand_alias(comando)
    decision = assess_terminal_command(comando_final)
    if not decision.allowed:
        return TermResult(False, f"Comando bloqueado: {decision.reason}", comando)
    if decision.requires_confirmation:
        confirmado = confirmar_callback(decision.message) if confirmar_callback else False
        if not confirmado:
            return TermResult(False, "Ação cancelada pelo usuário.", comando)

    work_dir = cwd or str(get_projeto() or Path.home())
    start = time.time()
    try:
        argv = _build_command(comando_final)
        proc = subprocess.run(
            argv,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=work_dir,
            errors="replace",
        )
        result = TermResult(proc.returncode == 0, (proc.stdout or "") + (proc.stderr or ""), comando, time.time() - start, work_dir)
        _add_history(comando, result.success, result.output[:200])
        log_action(f"Terminal: {comando_final}")
        return result
    except subprocess.TimeoutExpired:
        return TermResult(False, f"Timeout após {timeout}s", comando)
    except ValueError as error:
        return TermResult(False, f"Não consegui interpretar o comando: {error}", comando)
    except FileNotFoundError:
        return TermResult(False, "Executável não encontrado no PATH.", comando)
    except Exception as error:
        return TermResult(False, str(error), comando)


def executar_multiplos(comandos: list[str], cwd: str = "", confirmar_callback=None) -> list[TermResult]:
    results = []
    for command in comandos:
        result = executar(command, cwd=cwd, confirmar_callback=confirmar_callback)
        results.append(result)
        if not result.success:
            break
    return results


def sugerir_correcao(comando: str, erro: str) -> str:
    from coding.code_assistant import _call_ai

    return _call_ai(
        f"""Um comando falhou.
COMANDO: {comando}
ERRO: {erro[:800]}

Explique a causa e sugira o comando corrigido.""",
        max_tokens=350,
    )


def adicionar_alias(nome: str, comando: str) -> str:
    ALIASES[nome] = comando
    return f"Alias '{nome}' -> '{comando}' adicionado."


def listar_aliases() -> str:
    return "Aliases:\n" + "\n".join(f"{name:12s} -> {cmd}" for name, cmd in sorted(ALIASES.items()))


def get_history(n: int = 20) -> str:
    if not _HISTORY:
        return "Nenhum comando executado ainda."
    lines = [f"Últimos {min(n, len(_HISTORY))} comandos:"]
    for item in _HISTORY[-n:]:
        lines.append(f"{item['time']} {'OK' if item['success'] else 'ERRO'} {item['cmd']}")
    return "\n".join(lines)


def verificar_ambiente() -> str:
    tools = [
        ("Python", ["python", "--version"]),
        ("Node.js", ["node", "--version"]),
        ("npm", ["npm", "--version"]),
        ("Git", ["git", "--version"]),
        ("pip", ["pip", "--version"]),
        ("VS Code", ["code", "--version"]),
        ("Docker", ["docker", "--version"]),
        ("Go", ["go", "version"]),
        ("Rust/cargo", ["cargo", "--version"]),
    ]
    lines = ["Ambiente de desenvolvimento:"]
    for name, cmd in tools:
        if shutil.which(cmd[0]):
            try:
                proc = subprocess.run(cmd, shell=False, capture_output=True, text=True, timeout=5)
                version = (proc.stdout or proc.stderr).strip().splitlines()[0]
                lines.append(f"OK   {name:12s} {version}")
            except Exception:
                lines.append(f"OK   {name:12s} instalado")
        else:
            lines.append(f"MISS {name:12s} não encontrado")
    return "\n".join(lines)
