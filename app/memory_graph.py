from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import re

from app.config import BASE_DIR
from app.finance.store import FinanceStore
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

    try:
        finance_store = FinanceStore(base_dir=BASE_DIR)
        transactions = sorted(finance_store.list_transactions(), key=lambda item: (item.date, item.created_at), reverse=True)[:18]
        bills = sorted(finance_store.list_bills(), key=lambda item: item.due_date, reverse=True)[:12]
        goals = sorted(finance_store.list_goals(), key=lambda item: item.deadline, reverse=True)[:10]
        if transactions or bills or goals:
            finance_root_id = _safe_id("finance", "financeiro")
            nodes[finance_root_id] = MemoryGraphNode(
                id=finance_root_id,
                label="Financeiro",
                node_type="finance",
                group="finance",
                size=22,
                path="NEXUS/Financeiro",
            )
            edges[(vault_id, finance_root_id, "contains")] = MemoryGraphEdge(vault_id, finance_root_id, "contains")

            account_ids: dict[str, str] = {}
            category_ids: dict[str, str] = {}

            def _ensure_account(name: str) -> str:
                account_name = name.strip() or "Conta principal"
                account_id = account_ids.get(account_name)
                if account_id:
                    return account_id
                account_id = _safe_id("account", account_name)
                account_ids[account_name] = account_id
                nodes[account_id] = MemoryGraphNode(
                    id=account_id,
                    label=account_name,
                    node_type="account",
                    group="finance",
                    size=15,
                    path=account_name,
                )
                edges[(finance_root_id, account_id, "contains")] = MemoryGraphEdge(finance_root_id, account_id, "contains")
                return account_id

            def _ensure_category(name: str) -> str:
                category_name = name.strip() or "Geral"
                category_id = category_ids.get(category_name)
                if category_id:
                    return category_id
                category_id = _safe_id("category", category_name)
                category_ids[category_name] = category_id
                nodes[category_id] = MemoryGraphNode(
                    id=category_id,
                    label=category_name,
                    node_type="category",
                    group="finance",
                    size=14,
                    path=category_name,
                )
                edges[(finance_root_id, category_id, "contains")] = MemoryGraphEdge(finance_root_id, category_id, "contains")
                return category_id

            for item in transactions:
                account_id = _ensure_account(item.account)
                category_id = _ensure_category(item.category)
                transaction_id = _safe_id("transaction", item.id)
                nodes[transaction_id] = MemoryGraphNode(
                    id=transaction_id,
                    label=item.title,
                    node_type="transaction",
                    group=item.category,
                    size=11,
                    path=item.date,
                )
                edges[(finance_root_id, transaction_id, "contains")] = MemoryGraphEdge(finance_root_id, transaction_id, "contains")
                edges[(account_id, transaction_id, "contains")] = MemoryGraphEdge(account_id, transaction_id, "contains")
                edges[(category_id, transaction_id, "contains")] = MemoryGraphEdge(category_id, transaction_id, "contains")

            for item in bills:
                account_id = _ensure_account(item.account)
                category_id = _ensure_category(item.category)
                bill_id = _safe_id("bill", item.id)
                nodes[bill_id] = MemoryGraphNode(
                    id=bill_id,
                    label=item.title,
                    node_type="bill",
                    group=item.category,
                    size=12,
                    path=item.due_date,
                )
                edges[(finance_root_id, bill_id, "contains")] = MemoryGraphEdge(finance_root_id, bill_id, "contains")
                edges[(account_id, bill_id, "contains")] = MemoryGraphEdge(account_id, bill_id, "contains")
                edges[(category_id, bill_id, "contains")] = MemoryGraphEdge(category_id, bill_id, "contains")

            for item in goals:
                goal_id = _safe_id("goal", item.id)
                nodes[goal_id] = MemoryGraphNode(
                    id=goal_id,
                    label=item.title,
                    node_type="goal",
                    group="finance",
                    size=13,
                    path=item.deadline,
                )
                edges[(finance_root_id, goal_id, "contains")] = MemoryGraphEdge(finance_root_id, goal_id, "contains")
    except Exception:
        pass

    finance_types = {"finance", "account", "category", "transaction", "bill", "goal"}

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
            "finance": len([node for node in nodes.values() if node.node_type in finance_types]),
        },
    }
