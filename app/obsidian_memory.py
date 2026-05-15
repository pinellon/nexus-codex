"""Memoria de longo prazo usando um vault Obsidian local."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re
import unicodedata

from app.logger import log_action, log_error
from app.settings_manager import load, save


@dataclass
class MemoryHit:
    path: Path
    score: float
    title: str
    excerpt: str


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", text or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text.lower()).strip()


def tokens(text: str) -> set[str]:
    stop = {
        "a", "o", "os", "as", "um", "uma", "de", "do", "da", "dos", "das",
        "e", "ou", "em", "no", "na", "nos", "nas", "para", "pra", "por",
        "que", "qual", "quais", "como", "sobre", "me", "minha", "meu",
        "nexus", "voce", "você",
    }
    return {t for t in re.findall(r"[a-z0-9_]{3,}", normalize(text)) if t not in stop}


def discover_vaults(max_depth: int = 3) -> list[Path]:
    roots = [
        Path.home() / "Documents",
        Path.home() / "Desktop",
        Path.home() / "OneDrive",
        Path.home() / "OneDrive" / "Documents",
    ]
    found: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        try:
            for obsidian_dir in root.glob("**/.obsidian"):
                try:
                    rel_depth = len(obsidian_dir.relative_to(root).parts)
                except Exception:
                    rel_depth = 99
                if rel_depth <= max_depth + 1:
                    found.append(obsidian_dir.parent)
        except Exception:
            continue
    unique = []
    seen = set()
    for path in found:
        key = str(path).lower()
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return unique


def get_vault_path() -> Path | None:
    cfg = load()
    raw = (cfg.get("obsidian_vault_path") or "").strip()
    if raw:
        path = Path(raw).expanduser()
        if path.exists() and path.is_dir():
            return path
        return None
    discovered = discover_vaults(max_depth=2)
    if discovered:
        cfg["obsidian_vault_path"] = str(discovered[0])
        save(cfg)
        return discovered[0]
    return None


def is_enabled() -> bool:
    cfg = load()
    return bool(cfg.get("obsidian_enabled", True)) and get_vault_path() is not None


def configure_vault(path: str) -> str:
    vault = Path(path).expanduser()
    if not vault.exists() or not vault.is_dir():
        return f"Vault não encontrado: {path}"
    if not (vault / ".obsidian").exists():
        return f"A pasta existe, mas não parece um vault Obsidian: {vault}"
    cfg = load()
    cfg["obsidian_vault_path"] = str(vault)
    cfg["obsidian_enabled"] = True
    save(cfg)
    return f"Obsidian conectado: {vault}"


def markdown_files(vault: Path) -> list[Path]:
    ignored = {".obsidian", ".git", "node_modules", ".trash", "__pycache__"}
    files = []
    for path in vault.rglob("*.md"):
        if any(part in ignored for part in path.parts):
            continue
        files.append(path)
    return files


def search(query: str, limit: int | None = None) -> list[MemoryHit]:
    if not load().get("obsidian_enabled", True):
        return []
    vault = get_vault_path()
    if not vault:
        return []
    cfg = load()
    limit = limit or int(cfg.get("obsidian_max_results", 5))
    q_tokens = tokens(query)
    if not q_tokens:
        return []
    hits: list[MemoryHit] = []
    for path in markdown_files(vault):
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        haystack = normalize(path.stem + " " + content)
        c_tokens = tokens(path.stem + " " + content[:12000])
        overlap = q_tokens & c_tokens
        if not overlap:
            continue
        exact_bonus = 2.5 if normalize(query) in haystack else 0
        title_bonus = 1.5 if q_tokens & tokens(path.stem) else 0
        score = len(overlap) / max(1, len(q_tokens)) + exact_bonus + title_bonus
        excerpt = build_excerpt(content, q_tokens)
        hits.append(MemoryHit(path=path, score=score, title=path.stem, excerpt=excerpt))
    hits.sort(key=lambda h: h.score, reverse=True)
    return hits[:limit]


def build_excerpt(content: str, q_tokens: set[str], size: int = 700) -> str:
    clean = re.sub(r"\s+", " ", content.replace("\ufeff", "")).strip()
    normalized = normalize(clean)
    positions = [normalized.find(token) for token in q_tokens if normalized.find(token) >= 0]
    if not positions:
        return clean[:size]
    start = max(0, min(positions) - size // 3)
    return clean[start:start + size].strip()


def format_hits(hits: list[MemoryHit]) -> str:
    if not hits:
        return ""
    parts = []
    for index, hit in enumerate(hits, 1):
        parts.append(f"[{index}] {hit.title}\nArquivo: {hit.path}\nTrecho: {hit.excerpt}")
    return "\n\n".join(parts)


def context_for_prompt(query: str) -> tuple[str, list[MemoryHit]]:
    hits = search(query)
    if not hits:
        return "", []
    context = (
        "MEMORIA DO OBSIDIAN ENCONTRADA:\n"
        "Use as notas abaixo como fonte preferencial. Se algo conflitar, diga que a memoria local tem prioridade. "
        "Quando usar a memoria, cite discretamente o nome da nota no final.\n\n"
        + format_hits(hits)
    )
    log_action(f"Obsidian: {len(hits)} nota(s) usadas para '{query[:60]}'")
    return context, hits


def safe_note_title(text: str) -> str:
    title = re.sub(r"[^\w\s.-]", "", normalize(text)).strip()
    title = re.sub(r"\s+", "-", title)[:70].strip("-")
    return title or "memoria"


def register(query: str, answer: str, source: str = "nexus") -> Path | None:
    cfg = load()
    if not cfg.get("obsidian_enabled", True):
        return None
    if not cfg.get("obsidian_auto_register", True):
        return None
    vault = get_vault_path()
    if not vault:
        return None
    folder = vault / (cfg.get("obsidian_memory_folder") or "NEXUS/Memory Inbox")
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H%M%S")
    path = folder / f"{stamp} - {safe_note_title(query)}.md"
    body = f"""---
source: {source}
created: {datetime.now().isoformat(timespec="seconds")}
query: {query!r}
tags:
  - nexus
  - memoria
---

# {query}

## Resposta registrada

{answer}
"""
    try:
        path.write_text(body, encoding="utf-8")
        log_action(f"Obsidian: memoria registrada em {path}")
        return path
    except Exception as error:
        log_error(f"Obsidian register error: {error}")
        return None


def save_note(
    title: str,
    body: str,
    *,
    folder: str = "NEXUS/Conversas",
    frontmatter: dict[str, object] | None = None,
) -> Path | None:
    cfg = load()
    if not cfg.get("obsidian_enabled", True):
        return None
    vault = get_vault_path()
    if not vault:
        return None

    target_folder = vault / folder
    target_folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H%M%S")
    path = target_folder / f"{stamp} - {safe_note_title(title)}.md"
    header = ""
    if frontmatter:
        lines = ["---"]
        for key, value in frontmatter.items():
            if isinstance(value, list):
                lines.append(f"{key}:")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"{key}: {value}")
        lines.append("---")
        header = "\n".join(lines) + "\n\n"

    try:
        path.write_text(header + body.strip() + "\n", encoding="utf-8")
        log_action(f"Obsidian: nota salva em {path}")
        return path
    except Exception as error:
        log_error(f"Obsidian save_note error: {error}")
        return None


def search_or_status(query: str = "") -> str:
    vault = get_vault_path()
    if not vault:
        discovered = discover_vaults()
        if discovered:
            return "Vaults encontrados:\n" + "\n".join(str(p) for p in discovered)
        return "Nenhum vault Obsidian configurado. Informe o caminho em Configurações."
    if not query:
        return f"Obsidian conectado: {vault}\nNotas Markdown: {len(markdown_files(vault))}"
    hits = search(query)
    if not hits:
        return f"Nada encontrado no Obsidian para: {query}"
    return format_hits(hits)
