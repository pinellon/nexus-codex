from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re

from app.obsidian_memory import get_vault_path, markdown_files, normalize


_TAG_RE = re.compile(r"(?<!\w)#([a-zA-Z0-9_/\-]+)")
_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
_MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)#]+)(?:#[^)]+)?\)")


@dataclass(frozen=True)
class MemoryGraphNode:
    id: str
    label: str
    node_type: str
    group: str
    size: int
    path: str


@dataclass(frozen=True)
class MemoryGraphEdge:
    source: str
    target: str
    relation: str


def _safe_id(prefix: str, value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9_\-./]+", "-", normalize(value))
    cleaned = cleaned.strip("-") or prefix
    return f"{prefix}:{cleaned}"


def _note_aliases(relative_path: Path) -> set[str]:
    without_suffix = relative_path.with_suffix("")
    parts = without_suffix.parts
    aliases = {normalize(relative_path.stem)}
    aliases.add(normalize(relative_path.as_posix()))
    aliases.add(normalize(without_suffix.as_posix()))
    for index in range(len(parts)):
        suffix = Path(*parts[index:]).as_posix()
        aliases.add(normalize(suffix))
    return {alias for alias in aliases if alias}


def _iter_links(content: str) -> set[str]:
    references: set[str] = set()
    for raw_link in _WIKILINK_RE.findall(content):
        normalized_link = normalize(raw_link)
        if normalized_link:
            references.add(normalized_link)
    for raw_link in _MARKDOWN_LINK_RE.findall(content):
        if raw_link.startswith(("http://", "https://", "mailto:")):
            continue
        normalized_link = normalize(raw_link.removesuffix(".md").strip("./"))
        if normalized_link:
            references.add(normalized_link)
    return references


def build_memory_graph(note_limit: int = 90, tag_limit: int = 80) -> dict[str, object]:
    vault = get_vault_path()
    if not vault:
        return {
            "enabled": False,
            "vault_name": "",
            "vault_path": "",
            "nodes": [],
            "edges": [],
            "stats": {"areas": 0, "notes": 0, "tags": 0, "links": 0},
        }

    files = markdown_files(vault)[:note_limit]
    vault_id = _safe_id("vault", vault.name or "vault")

    nodes: dict[str, MemoryGraphNode] = {
        vault_id: MemoryGraphNode(
            id=vault_id,
            label=vault.name or "Vault",
            node_type="vault",
            group="vault",
            size=26,
            path="",
        )
    }
    edges: dict[tuple[str, str, str], MemoryGraphEdge] = {}
    note_index: dict[str, str] = {}
    tag_usage: dict[str, int] = {}
    area_usage: dict[str, int] = {}
    links_count = 0

    for path in files:
        relative_path = path.relative_to(vault)
        area = relative_path.parts[0] if relative_path.parts else "raiz"
        area_id = _safe_id("area", area)
        area_usage[area_id] = area_usage.get(area_id, 0) + 1
        nodes.setdefault(
            area_id,
            MemoryGraphNode(
                id=area_id,
                label=area,
                node_type="area",
                group="area",
                size=18,
                path=area,
            ),
        )
        edges[(vault_id, area_id, "contains")] = MemoryGraphEdge(vault_id, area_id, "contains")

        note_id = _safe_id("note", relative_path.with_suffix("").as_posix())
        note_node = MemoryGraphNode(
            id=note_id,
            label=path.stem,
            node_type="note",
            group=area,
            size=12,
            path=relative_path.as_posix(),
        )
        nodes[note_id] = note_node
        edges[(area_id, note_id, "contains")] = MemoryGraphEdge(area_id, note_id, "contains")

        for alias in _note_aliases(relative_path):
            note_index.setdefault(alias, note_id)

    for path in files:
        relative_path = path.relative_to(vault)
        note_id = _safe_id("note", relative_path.with_suffix("").as_posix())
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for match in _TAG_RE.findall(content):
            tag = match.strip().lower()
            if not tag:
                continue
            tag_usage[tag] = tag_usage.get(tag, 0) + 1

        for normalized_link in _iter_links(content):
            target_id = note_index.get(normalized_link)
            if target_id and target_id != note_id:
                edges[(note_id, target_id, "links")] = MemoryGraphEdge(note_id, target_id, "links")
    links_count = len([edge for edge in edges.values() if edge.relation == "links"])

    sorted_tags = sorted(tag_usage.items(), key=lambda item: item[1], reverse=True)[:tag_limit]
    for tag, usage in sorted_tags:
        tag_id = _safe_id("tag", tag)
        nodes[tag_id] = MemoryGraphNode(
            id=tag_id,
            label=f"#{tag}",
            node_type="tag",
            group="tag",
            size=8 + min(usage, 8),
            path=tag,
        )

    for path in files:
        relative_path = path.relative_to(vault)
        note_id = _safe_id("note", relative_path.with_suffix("").as_posix())
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        note_tags = {tag.strip().lower() for tag in _TAG_RE.findall(content) if tag.strip()}
        for tag in note_tags:
            tag_id = _safe_id("tag", tag)
            if tag_id in nodes:
                edges[(note_id, tag_id, "tagged")] = MemoryGraphEdge(note_id, tag_id, "tagged")

    return {
        "enabled": True,
        "vault_name": vault.name,
        "vault_path": str(vault),
        "nodes": [asdict(node) for node in nodes.values()],
        "edges": [asdict(edge) for edge in edges.values()],
        "stats": {
            "areas": len([node for node in nodes.values() if node.node_type == "area"]),
            "notes": len([node for node in nodes.values() if node.node_type == "note"]),
            "tags": len([node for node in nodes.values() if node.node_type == "tag"]),
            "links": links_count,
        },
    }
