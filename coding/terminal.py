"""Terminal inteligente com aliases e historico."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import shutil
import subprocess
import time

from coding.file_manager import get_projeto

try:
    from app.logger import log_action
except ImportError:
    def log_action(text: str): print(text)


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
    "which": "where",
}

REQUIRES_CONFIRM = {"rmdir", "del ", "rd /s", "format", "shutdown", "taskkill /f", "rm -r", "drop table", "drop database"}
_history: list[dict] = []
MAX_HISTORY = 100


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


def executar(comando: str, cwd: str = "", timeout: int = 60, confirmar_callback=None) -> TermResult:
    cmd_lower = comando.lower()
    for danger in REQUIRES_CONFIRM:
        if danger in cmd_lower:
            if confirmar_callback and confirmar_callback(f"Comando perigoso: '{comando}'. Confirmar?"):
                break
            return TermResult(False, f"Comando bloqueado: {danger}", comando)
    parts = comando.strip().split(maxsplit=1)
    if parts and parts[0] in ALIASES:
        comando_final = ALIASES[parts[0]] + (f" {parts[1]}" if len(parts) > 1 else "")
    else:
        comando_final = comando
    work_dir = cwd or str(get_projeto() or Path.home())
    start = time.time()
    try:
        proc = subprocess.run(comando_final, shell=True, capture_output=True, text=True, timeout=timeout, cwd=work_dir, errors="replace")
        result = TermResult(proc.returncode == 0, proc.stdout + proc.stderr, comando, time.time() - start, work_dir)
        _add_history(comando, result.success, result.output[:200])
        log_action(f"Terminal: {comando}")
        return result
    except subprocess.TimeoutExpired:
        return TermResult(False, f"Timeout apos {timeout}s", comando)
    except Exception as error:
        return TermResult(False, str(error), comando)


def executar_multiplos(comandos: list[str], cwd: str = "") -> list[TermResult]:
    results = []
    for command in comandos:
        result = executar(command, cwd=cwd)
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


def _add_history(cmd: str, success: bool, output: str):
    _history.append({"cmd": cmd, "success": success, "output": output, "time": datetime.now().strftime("%H:%M:%S")})
    if len(_history) > MAX_HISTORY:
        _history.pop(0)


def get_history(n: int = 20) -> str:
    if not _history:
        return "Nenhum comando executado ainda."
    lines = [f"Ultimos {min(n, len(_history))} comandos:"]
    for item in _history[-n:]:
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
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                version = (proc.stdout or proc.stderr).strip().splitlines()[0]
                lines.append(f"OK   {name:12s} {version}")
            except Exception:
                lines.append(f"OK   {name:12s} instalado")
        else:
            lines.append(f"MISS {name:12s} nao encontrado")
    return "\n".join(lines)

