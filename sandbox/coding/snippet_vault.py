"""Cofre local de snippets do NEXUS CODER."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json
import uuid

try:
    from app.config import DATA_DIR
    SNIPPETS_DIR = DATA_DIR / "snippets"
except ImportError:
    SNIPPETS_DIR = Path("data/snippets")

SNIPPETS_FILE = SNIPPETS_DIR / "vault.json"
SNIPPETS_DIR.mkdir(parents=True, exist_ok=True)


def _load() -> list[dict]:
    try:
        if SNIPPETS_FILE.exists():
            data = json.loads(SNIPPETS_FILE.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
    except Exception:
        pass
    return []


def _save(snippets: list[dict]):
    SNIPPETS_DIR.mkdir(parents=True, exist_ok=True)
    SNIPPETS_FILE.write_text(json.dumps(snippets, ensure_ascii=False, indent=2), encoding="utf-8")


def salvar_snippet(titulo: str, codigo: str, linguagem: str = "python", tags: list[str] | None = None, descricao: str = "") -> dict:
    snippets = _load()
    snippet = {
        "id": str(uuid.uuid4())[:8],
        "titulo": titulo,
        "linguagem": linguagem.lower(),
        "tags": [tag.lower() for tag in (tags or [])],
        "codigo": codigo,
        "descricao": descricao,
        "criado_em": datetime.now().isoformat(),
        "usado": 0,
    }
    snippets.append(snippet)
    _save(snippets)
    return snippet


def buscar_snippets(termo: str) -> list[dict]:
    query = (termo or "").lower()
    scored = []
    for snippet in _load():
        score = 0
        if query in snippet.get("titulo", "").lower():
            score += 3
        if any(query in tag for tag in snippet.get("tags", [])):
            score += 2
        if query == snippet.get("linguagem", ""):
            score += 2
        if query in snippet.get("descricao", "").lower():
            score += 1
        if query in snippet.get("codigo", "").lower():
            score += 1
        if score:
            scored.append((score, snippet))
    return [snippet for _, snippet in sorted(scored, key=lambda item: -item[0])]


def listar_snippets(linguagem: str = "", tag: str = "") -> list[dict]:
    snippets = _load()
    if linguagem:
        snippets = [s for s in snippets if s.get("linguagem") == linguagem.lower()]
    if tag:
        snippets = [s for s in snippets if tag.lower() in s.get("tags", [])]
    return sorted(snippets, key=lambda s: s.get("criado_em", ""), reverse=True)


def get_snippet(snippet_id: str) -> dict | None:
    return next((s for s in _load() if s.get("id") == snippet_id), None)


def usar_snippet(snippet_id: str) -> str | None:
    snippets = _load()
    for snippet in snippets:
        if snippet.get("id") == snippet_id:
            snippet["usado"] = snippet.get("usado", 0) + 1
            _save(snippets)
            return snippet.get("codigo", "")
    return None


def deletar_snippet(snippet_id: str) -> bool:
    snippets = _load()
    new = [s for s in snippets if s.get("id") != snippet_id]
    if len(new) == len(snippets):
        return False
    _save(new)
    return True


def editar_snippet(snippet_id: str, **campos) -> bool:
    snippets = _load()
    allowed = {"titulo", "codigo", "tags", "descricao", "linguagem"}
    for snippet in snippets:
        if snippet.get("id") == snippet_id:
            snippet.update({key: value for key, value in campos.items() if key in allowed})
            _save(snippets)
            return True
    return False


def formatar_snippet(snippet: dict, mostrar_codigo: bool = True) -> str:
    tags = " ".join(f"#{tag}" for tag in snippet.get("tags", []))
    lines = [
        f"[{snippet['id']}] {snippet['titulo']}",
        f"    {snippet.get('linguagem', '').upper()} {tags} usado {snippet.get('usado', 0)}x",
    ]
    if snippet.get("descricao"):
        lines.append(f"    {snippet['descricao']}")
    if mostrar_codigo:
        lines.append(f"\n```{snippet.get('linguagem', '')}")
        lines.append(snippet.get("codigo", ""))
        lines.append("```")
    return "\n".join(lines)


def formatar_lista(snippets: list[dict]) -> str:
    if not snippets:
        return "Nenhum snippet encontrado."
    lines = [f"{len(snippets)} snippet(s):\n"]
    for snippet in snippets[:20]:
        tags = " ".join(f"#{tag}" for tag in snippet.get("tags", [])[:3])
        lines.append(f"[{snippet['id']}] {snippet['titulo']} ({snippet.get('linguagem', '')}) {tags}")
    if len(snippets) > 20:
        lines.append(f"... e mais {len(snippets) - 20}")
    return "\n".join(lines)


def estatisticas() -> str:
    snippets = _load()
    if not snippets:
        return "Cofre vazio. Comece salvando snippets."
    by_lang: dict[str, int] = {}
    for snippet in snippets:
        lang = snippet.get("linguagem", "outros")
        by_lang[lang] = by_lang.get(lang, 0) + 1
    most = max(snippets, key=lambda s: s.get("usado", 0))
    lines = [f"Total: {len(snippets)} snippets"]
    lines += [f"{lang:12s} {qty} snippet(s)" for lang, qty in sorted(by_lang.items(), key=lambda item: -item[1])]
    lines.append(f"Mais usado: [{most['id']}] {most['titulo']} ({most.get('usado', 0)}x)")
    return "\n".join(lines)

