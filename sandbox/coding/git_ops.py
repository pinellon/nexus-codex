"""Integração Git para o NEXUS CODER."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
import subprocess

from coding.file_manager import get_projeto

try:
    from app.logger import log_action
except ImportError:
    def log_action(text: str):  # type: ignore[override]
        print(text)


@dataclass
class GitResult:
    success: bool
    output: str
    cmd: str = ""

    def __str__(self) -> str:
        return self.output


def _confirm(confirm_callback, message: str) -> bool:
    if not confirm_callback:
        return True
    return bool(confirm_callback(message))


def _git(args: list[str], cwd: Path | None = None) -> GitResult:
    repo = cwd or get_projeto()
    if not repo:
        return GitResult(False, "Nenhum projeto/repositório ativo.")
    cmd = ["git"] + args
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=str(repo), timeout=30)
        output = proc.stdout.strip() or proc.stderr.strip()
        ok = proc.returncode == 0
        log_action(f"git {' '.join(args)} -> {'ok' if ok else 'erro'}")
        return GitResult(ok, output or ("OK" if ok else "Sem saída"), " ".join(cmd))
    except FileNotFoundError:
        return GitResult(False, "Git não encontrado.")
    except subprocess.TimeoutExpired:
        return GitResult(False, "Timeout no comando git.")
    except Exception as error:
        return GitResult(False, str(error))


def status() -> GitResult:
    result = _git(["status", "-sb"])
    if result.success and not result.output:
        return GitResult(True, "Repositório limpo.")
    return result


def diff(arquivo: str = "") -> GitResult:
    return _git(["diff", arquivo] if arquivo else ["diff", "--stat"])


def diff_completo(arquivo: str = "") -> GitResult:
    return _git(["diff", arquivo] if arquivo else ["diff"])


def log(n: int = 10, formato: str = "curto") -> GitResult:
    fmt = "%h | %s | %an | %ar" if formato == "curto" else "%h %ad %s <%an>"
    return _git(["log", f"-{n}", f"--pretty=format:{fmt}", "--date=short"])


def branch_atual() -> GitResult:
    result = _git(["branch", "--show-current"])
    if result.success:
        result.output = result.output.strip()
    return result


def listar_branches() -> GitResult:
    return _git(["branch", "-a"])


def add(arquivos: str = ".") -> GitResult:
    return _git(["add", arquivos])


def commit(mensagem: str) -> GitResult:
    if not mensagem:
        return GitResult(False, "Mensagem de commit não pode ser vazia.")
    result = _git(["commit", "-m", mensagem])
    if result.success:
        result.output = f"Commit: {mensagem}\n{result.output}"
    return result


def push(branch: str = "", remote: str = "origin", confirm_callback=None) -> GitResult:
    current = branch_atual()
    br = (branch or (current.output if current.success else "main")).strip() or "main"
    if not _confirm(confirm_callback, f"Enviar alterações para {remote}/{br} agora?"):
        return GitResult(False, "Ação cancelada pelo usuário.")
    return _git(["push", remote, br])


def pull(remote: str = "origin", branch: str = "", confirm_callback=None) -> GitResult:
    current = branch_atual()
    br = (branch or (current.output if current.success else "")).strip()
    label = f"{remote}/{br}" if br else remote
    if not _confirm(confirm_callback, f"Baixar alterações de {label} agora?"):
        return GitResult(False, "Ação cancelada pelo usuário.")
    args = ["pull", remote] + ([br] if br else [])
    return _git(args)


def criar_branch(nome: str, checkout: bool = True, confirm_callback=None) -> GitResult:
    safe = re.sub(r"[^a-zA-Z0-9\-_/]", "-", nome or "")
    if not safe:
        return GitResult(False, "Nome de branch inválido.")
    if not _confirm(confirm_callback, f"Criar a branch '{safe}' agora?"):
        return GitResult(False, "Ação cancelada pelo usuário.")
    return _git(["checkout", "-b", safe] if checkout else ["branch", safe])


def trocar_branch(nome: str) -> GitResult:
    return _git(["checkout", nome])


def stash(mensagem: str = "") -> GitResult:
    return _git(["stash", "push"] + (["-m", mensagem] if mensagem else []))


def stash_pop() -> GitResult:
    return _git(["stash", "pop"])


def init_repo() -> GitResult:
    return _git(["init"])


def gerar_mensagem_commit() -> str:
    from coding.code_assistant import _call_ai

    result = diff_completo()
    if not result.success or not result.output.strip():
        return "Sem mudanças para gerar mensagem."
    return _call_ai(
        f"""Gere uma mensagem Conventional Commit para este diff:

```diff
{result.output[:4000]}
```

Retorne apenas a mensagem.""",
        max_tokens=100,
    )


def resumir_mudancas() -> str:
    from coding.code_assistant import _call_ai

    result = diff_completo()
    if not result.success or not result.output.strip():
        return status().output
    return _call_ai(f"Resuma este diff em português, máximo 5 linhas:\n```diff\n{result.output[:4000]}\n```", max_tokens=300)


def commit_rapido(mensagem: str = "") -> GitResult:
    add_result = add()
    if not add_result.success:
        return add_result
    msg = mensagem or gerar_mensagem_commit()
    if not msg or "Sem mudanças" in msg:
        return GitResult(False, "Nada para commitar.")
    return commit(msg)


def resumo_repositorio() -> str:
    parts = []
    br = branch_atual()
    if br.success:
        parts.append(f"Branch: {br.output}")
    parts.append(f"Status:\n{status().output}")
    history = log(5)
    if history.success and history.output:
        parts.append(f"Últimos commits:\n{history.output}")
    return "\n\n".join(parts)
