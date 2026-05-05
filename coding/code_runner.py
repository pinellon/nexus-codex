"""Executor seguro para snippets Python, JavaScript e shell."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re
import subprocess
import tempfile
import time


@dataclass
class RunResult:
    success: bool
    stdout: str
    stderr: str
    elapsed: float
    exit_code: int
    language: str

    def format(self) -> str:
        status = "Sucesso" if self.success else "Erro"
        parts = [f"{status} ({self.language}) - {self.elapsed:.2f}s"]
        if self.stdout.strip():
            parts += ["--- Output ---", self.stdout.strip()]
        if self.stderr.strip():
            parts += ["--- Stderr ---", self.stderr.strip()]
        if not self.stdout.strip() and not self.stderr.strip():
            parts.append("(sem output)")
        return "\n".join(parts)


_BLOCKED_PATTERNS = [
    r"os\.system",
    r"subprocess\.(call|Popen|run)",
    r"shutil\.rmtree",
    r"import\s+socket",
    r"__import__\s*\(",
    r"rm\s+-rf",
    r"del\s+/f\s+/s",
    r"format\s+c:",
    r"mkfs",
]

_BLOCKED_COMMANDS = ["rm -rf", "del /f /s", "format c:", "mkfs", "shutdown", "reboot", "halt"]


def _is_safe(code: str) -> tuple[bool, str]:
    text = code or ""
    for pattern in _BLOCKED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return False, f"padrao bloqueado: {pattern}"
    for command in _BLOCKED_COMMANDS:
        if command in text.lower():
            return False, f"comando bloqueado: {command}"
    return True, ""


def executar_python(codigo: str, timeout: int = 15) -> RunResult:
    safe, reason = _is_safe(codigo)
    if not safe:
        return RunResult(False, "", f"Bloqueado: {reason}", 0.0, -1, "Python")
    with tempfile.TemporaryDirectory() as tmpdir:
        script = Path(tmpdir) / "snippet.py"
        script.write_text(codigo, encoding="utf-8")
        start = time.time()
        try:
            proc = subprocess.run(
                ["python", str(script)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            )
            return RunResult(proc.returncode == 0, proc.stdout, proc.stderr, time.time() - start, proc.returncode, "Python")
        except subprocess.TimeoutExpired:
            return RunResult(False, "", f"Timeout apos {timeout}s", timeout, -1, "Python")
        except FileNotFoundError:
            return RunResult(False, "", "Python nao encontrado no PATH.", 0.0, -1, "Python")


def executar_javascript(codigo: str, timeout: int = 15) -> RunResult:
    safe, reason = _is_safe(codigo)
    if not safe:
        return RunResult(False, "", f"Bloqueado: {reason}", 0.0, -1, "JavaScript")
    with tempfile.TemporaryDirectory() as tmpdir:
        script = Path(tmpdir) / "snippet.js"
        script.write_text(codigo, encoding="utf-8")
        start = time.time()
        try:
            proc = subprocess.run(["node", str(script)], capture_output=True, text=True, timeout=timeout, cwd=tmpdir)
            return RunResult(proc.returncode == 0, proc.stdout, proc.stderr, time.time() - start, proc.returncode, "JavaScript")
        except subprocess.TimeoutExpired:
            return RunResult(False, "", f"Timeout apos {timeout}s", timeout, -1, "JavaScript")
        except FileNotFoundError:
            return RunResult(False, "", "Node.js nao encontrado no PATH.", 0.0, -1, "JavaScript")


def executar_shell(comando: str, cwd: str = "", timeout: int = 30) -> RunResult:
    safe, reason = _is_safe(comando)
    if not safe:
        return RunResult(False, "", f"Bloqueado: {reason}", 0.0, -1, "Shell")
    start = time.time()
    try:
        proc = subprocess.run(
            comando,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or str(Path.home()),
        )
        return RunResult(proc.returncode == 0, proc.stdout, proc.stderr, time.time() - start, proc.returncode, "Shell")
    except subprocess.TimeoutExpired:
        return RunResult(False, "", f"Timeout apos {timeout}s", timeout, -1, "Shell")
    except Exception as error:
        return RunResult(False, "", str(error), 0.0, -1, "Shell")


def executar_auto(codigo: str, linguagem: str = "auto", timeout: int = 15) -> RunResult:
    lang = (linguagem or "auto").lower().strip()
    if lang == "auto":
        if re.search(r"\bconsole\.log\b|\bconst\b|\blet\b|\bfunction\b|=>", codigo):
            lang = "javascript"
        elif re.search(r"^\s*(echo|dir|ls|cd)\b", codigo, re.MULTILINE):
            lang = "shell"
        else:
            lang = "python"
    if lang in {"python", "py"}:
        return executar_python(codigo, timeout)
    if lang in {"javascript", "js", "node", "typescript", "ts"}:
        return executar_javascript(codigo, timeout)
    if lang in {"shell", "bash", "cmd", "powershell", "ps1", "sh"}:
        return executar_shell(codigo, timeout=timeout)
    return executar_python(codigo, timeout)


def instalar_pacote(pacote: str) -> RunResult:
    if not re.match(r"^[\w.\-]+$", pacote or ""):
        return RunResult(False, "", "Nome de pacote invalido.", 0.0, -1, "pip")
    start = time.time()
    try:
        proc = subprocess.run(["pip", "install", pacote, "--quiet"], capture_output=True, text=True, timeout=120)
        stdout = proc.stdout or (f"{pacote} instalado." if proc.returncode == 0 else "")
        return RunResult(proc.returncode == 0, stdout, proc.stderr, time.time() - start, proc.returncode, "pip")
    except subprocess.TimeoutExpired:
        return RunResult(False, "", "Timeout na instalacao.", 120, -1, "pip")
    except FileNotFoundError:
        return RunResult(False, "", "pip nao encontrado.", 0.0, -1, "pip")

