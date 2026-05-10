"""Acoes de IA com patch para o projeto ativo."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
import re

from coding.code_assistant import _call_ai
from coding.file_manager import get_projeto
from coding.patcher import apply_patch_files, preview_patch
from coding.project_context import build_context_snapshot, resolve_project_root


SYSTEM_EXTRA = """Voce e o NEXUS CODER em modo patch local.
Responda apenas JSON valido.
Nunca inclua chaves, tokens ou senhas.
Preserve o estilo do projeto e altere somente arquivos necessarios.

Formato obrigatorio:
{
  "summary": "resumo curto",
  "risk": "low | medium | high",
  "files": [
    {"path": "caminho/relativo.py", "content": "conteudo completo do arquivo"}
  ],
  "commands": ["comando opcional para testar"],
  "notes": ["observacoes"]
}
"""

ACTION_INSTRUCTIONS = {
    "generate": "Gere codigo novo e integre ao projeto quando o contexto indicar o local correto.",
    "review_bugs": "Encontre bugs reais e corrija apenas o necessario.",
    "refactor": "Refatore mantendo comportamento e estilo.",
    "tests": "Crie ou melhore testes automatizados.",
    "document": "Adicione documentacao util sem poluir o codigo.",
    "performance": "Otimize apenas gargalos claros.",
    "security": "Corrija riscos de seguranca reais: injection, path traversal, secrets e entradas sem validacao.",
}


@dataclass
class WorkspaceAIResult:
    summary: str
    risk: str = "medium"
    files: list[dict[str, str]] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    raw: str = ""


_last_result: WorkspaceAIResult | None = None
_last_diff: str = ""


def run_workspace_ai(
    request: str,
    action_id: str = "generate",
    active_file: str = "",
    selection: str = "",
    language: str = "python",
) -> tuple[WorkspaceAIResult, str]:
    global _last_result, _last_diff
    root = resolve_project_root()
    if not root:
        result = WorkspaceAIResult("Nenhum projeto ativo. Use: define o projeto em C:\\caminho\\do\\projeto", "low")
        _last_result = result
        _last_diff = "Sem patch."
        return result, _last_diff

    context = build_context_snapshot(root, active_file=active_file, selection=selection)
    instruction = ACTION_INSTRUCTIONS.get(action_id, ACTION_INSTRUCTIONS["generate"])
    prompt = f"""ACAO: {action_id}
LINGUAGEM: {language}
PEDIDO: {request}
INSTRUCAO: {instruction}

CONTEXTO DO PROJETO:
{context}
"""
    raw = _call_ai(prompt, system_extra=SYSTEM_EXTRA, max_tokens=3500)
    result = _parse_result(raw)
    _last_result = result
    _last_diff = preview_patch(root, result.files) if result.files else "Sem patch para aplicar."
    return result, _last_diff


def format_workspace_result(result: WorkspaceAIResult, diff: str) -> str:
    lines = [
        f"Resumo: {result.summary}",
        f"Risco: {result.risk}",
    ]
    if result.commands:
        lines.append("\nComandos sugeridos:")
        lines.extend(f"- {command}" for command in result.commands)
    if result.notes:
        lines.append("\nNotas:")
        lines.extend(f"- {note}" for note in result.notes)
    lines.append("\nPreview do diff:")
    lines.append(f"```diff\n{diff[:12000]}\n```")
    return "\n".join(lines)


def preview_last_patch() -> str:
    return _last_diff or "Nenhum patch gerado ainda."


def apply_last_patch() -> str:
    if not _last_result or not _last_result.files:
        return "Nenhum patch gerado para aplicar."
    root = get_projeto()
    if not root:
        return "Nenhum projeto ativo."
    changed = apply_patch_files(Path(root), _last_result.files)
    if not changed:
        return "Nenhum arquivo alterado."
    return "Patch aplicado em:\n" + "\n".join(f"- {path}" for path in changed)


def _parse_result(raw: str) -> WorkspaceAIResult:
    data = _parse_json(raw)
    return WorkspaceAIResult(
        summary=str(data.get("summary", "Sem resumo.")),
        risk=str(data.get("risk", "medium")),
        files=_normalize_files(data.get("files", [])),
        commands=[str(item) for item in data.get("commands", [])],
        notes=[str(item) for item in data.get("notes", [])],
        raw=raw,
    )


def _parse_json(text: str) -> dict:
    cleaned = (text or "").strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, re.DOTALL | re.IGNORECASE)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "summary": "A IA nao retornou JSON valido. Veja a resposta bruta nas notas.",
            "risk": "medium",
            "files": [],
            "commands": [],
            "notes": [text[:3000]],
        }


def _normalize_files(files) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    if not isinstance(files, list):
        return normalized
    for item in files:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path", "")).strip()
        content = item.get("content", "")
        if path:
            normalized.append({"path": path, "content": str(content)})
    return normalized
