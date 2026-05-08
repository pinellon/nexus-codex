"""Runner de snippets com execução menos permissiva.

Observação importante: isso melhora bastante a segurança, mas não substitui uma sandbox real.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import ast
import os
import re
import subprocess
import sys
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


_BLOCKED_JS_PATTERNS = [
    r"child_process",
    r"fs\.rm",
    r"fs\.unlink",
    r"process\.kill",
    r"require\(['\"]net['\"]\)",
    r"require\(['\"]http['\"]\)",
    r"require\(['\"]https['\"]\)",
]

_BLOCKED_SHELL_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bformat\b",
    r"\bshutdown\b",
    r"\bmkfs\b",
]


class _PythonSafetyVisitor(ast.NodeVisitor):
    forbidden_imports = {"socket", "subprocess", "requests", "urllib", "http", "ftplib", "telnetlib"}
    forbidden_calls = {
        ("os", "system"),
        ("os", "remove"),
        ("os", "unlink"),
        ("os", "rmdir"),
        ("os", "removedirs"),
        ("shutil", "rmtree"),
        ("subprocess", "run"),
        ("subprocess", "Popen"),
    }

    def __init__(self):
        self.errors: list[str] = []

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            root = alias.name.split(".", 1)[0]
            if root in self.forbidden_imports:
                self.errors.append(f"import bloqueado: {root}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        root = (node.module or "").split(".", 1)[0]
        if root in self.forbidden_imports:
            self.errors.append(f"import bloqueado: {root}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        func = node.func
        if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
            pair = (func.value.id, func.attr)
            if pair in self.forbidden_calls:
                self.errors.append(f"chamada bloqueada: {func.value.id}.{func.attr}")
        self.generic_visit(node)


def _safe_env() -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", ""),
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "PIP_DISABLE_PIP_VERSION_CHECK": "1",
    }
    for key in ["SYSTEMROOT", "WINDIR", "TEMP", "TMP", "HOME", "USERPROFILE"]:
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def _check_python_safety(code: str) -> tuple[bool, str]:
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        return False, f"erro de sintaxe: {error}"
    visitor = _PythonSafetyVisitor()
    visitor.visit(tree)
    if visitor.errors:
        return False, "; ".join(visitor.errors)
    return True, ""


def _check_js_safety(code: str) -> tuple[bool, str]:
    for pattern in _BLOCKED_JS_PATTERNS:
        if re.search(pattern, code or "", re.IGNORECASE):
            return False, f"padrão bloqueado: {pattern}"
    return True, ""


def _check_shell_safety(code: str) -> tuple[bool, str]:
    for pattern in _BLOCKED_SHELL_PATTERNS:
        if re.search(pattern, code or "", re.IGNORECASE):
            return False, f"padrão bloqueado: {pattern}"
    return True, ""


def executar_python(codigo: str, timeout: int = 15) -> RunResult:
    safe, reason = _check_python_safety(codigo)
    if not safe:
        return RunResult(False, "", f"Bloqueado: {reason}", 0.0, -1, "Python")
    with tempfile.TemporaryDirectory() as tmpdir:
        script = Path(tmpdir) / "snippet.py"
        script.write_text(codigo, encoding="utf-8")
        start = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, str(script)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=tmpdir,
                env=_safe_env(),
            )
            return RunResult(proc.returncode == 0, proc.stdout or "", proc.stderr or "", time.time() - start, proc.returncode, "Python")
        except subprocess.TimeoutExpired:
            return RunResult(False, "", f"Timeout após {timeout}s", timeout, -1, "Python")
        except FileNotFoundError:
            return RunResult(False, "", "Python não encontrado no PATH.", 0.0, -1, "Python")


def executar_javascript(codigo: str, timeout: int = 15) -> RunResult:
    safe, reason = _check_js_safety(codigo)
    if not safe:
        return RunResult(False, "", f"Bloqueado: {reason}", 0.0, -1, "JavaScript")
    with tempfile.TemporaryDirectory() as tmpdir:
        script = Path(tmpdir) / "snippet.js"
        script.write_text(codigo, encoding="utf-8")
        start = time.time()
        try:
            proc = subprocess.run(["node", str(script)], capture_output=True, text=True, timeout=timeout, cwd=tmpdir, env=_safe_env())
            return RunResult(proc.returncode == 0, proc.stdout or "", proc.stderr or "", time.time() - start, proc.returncode, "JavaScript")
        except subprocess.TimeoutExpired:
            return RunResult(False, "", f"Timeout após {timeout}s", timeout, -1, "JavaScript")
        except FileNotFoundError:
            return RunResult(False, "", "Node.js não encontrado no PATH.", 0.0, -1, "JavaScript")


def executar_shell(comando: str, cwd: str = "", timeout: int = 30, confirm_callback=None) -> RunResult:
    safe, reason = _check_shell_safety(comando)
    if not safe:
        return RunResult(False, "", f"Bloqueado: {reason}", 0.0, -1, "Shell")

    from coding.terminal import executar as executar_terminal

    result = executar_terminal(comando, cwd=cwd, timeout=timeout, confirmar_callback=confirm_callback)
    return RunResult(result.success, result.output, "", result.elapsed, 0 if result.success else 1, "Shell")


def executar_auto(codigo: str, linguagem: str = "auto", timeout: int = 15, confirm_callback=None) -> RunResult:
    lang = (linguagem or "auto").lower().strip()
    if lang == "auto":
        if re.search(r"\bconsole\.log\b|\bconst\b|\blet\b|\bfunction\b|=>", codigo):
            lang = "javascript"
        elif re.search(r"^\s*(echo|dir|ls|cd|git|pip|npm)\b", codigo, re.MULTILINE):
            lang = "shell"
        else:
            lang = "python"
    if lang in {"python", "py"}:
        return executar_python(codigo, timeout)
    if lang in {"javascript", "js", "node", "typescript", "ts"}:
        return executar_javascript(codigo, timeout)
    if lang in {"shell", "bash", "cmd", "powershell", "ps1", "sh"}:
        return executar_shell(codigo, timeout=timeout, confirm_callback=confirm_callback)
    return executar_python(codigo, timeout)


def instalar_pacote(pacote: str, confirm_callback=None) -> RunResult:
    if not re.match(r"^[\w.\-]+$", pacote or ""):
        return RunResult(False, "", "Nome de pacote inválido.", 0.0, -1, "pip")
    if confirm_callback and not confirm_callback(f"Instalar o pacote '{pacote}' agora?"):
        return RunResult(False, "", "Instalação cancelada pelo usuário.", 0.0, -1, "pip")
    start = time.time()
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pip", "install", pacote, "--quiet", "--disable-pip-version-check"],
            capture_output=True,
            text=True,
            timeout=120,
            env=_safe_env(),
        )
        stdout = proc.stdout or (f"{pacote} instalado." if proc.returncode == 0 else "")
        return RunResult(proc.returncode == 0, stdout, proc.stderr or "", time.time() - start, proc.returncode, "pip")
    except subprocess.TimeoutExpired:
        return RunResult(False, "", "Timeout na instalação.", 120, -1, "pip")
    except FileNotFoundError:
        return RunResult(False, "", "pip não encontrado.", 0.0, -1, "pip")
