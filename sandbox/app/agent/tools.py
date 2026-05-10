"""Ferramentas disponíveis para o agente autônomo do NEXUS.

Cada ferramenta é uma função Python pura + um schema OpenAI para que o
modelo saiba quando e como chamá-la.
"""
from __future__ import annotations

import datetime
import re
import textwrap
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Schemas OpenAI (function calling)
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": (
                "Pesquisa na web usando DuckDuckGo e retorna os títulos, "
                "snippets e URLs dos primeiros resultados. Use para descobrir "
                "o que existe sobre um assunto antes de ir mais fundo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Termos de busca em qualquer idioma.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Quantidade de resultados (padrão 5, máximo 10).",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_page",
            "description": (
                "Acessa uma URL e extrai o texto limpo da página (sem HTML, "
                "scripts ou anúncios). Use quando quiser ler o conteúdo "
                "completo de um resultado de busca."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL completa da página a ser lida.",
                    },
                    "max_chars": {
                        "type": "integer",
                        "description": "Limite de caracteres do texto extraído (padrão 4000).",
                        "default": 4000,
                    },
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_to_obsidian",
            "description": (
                "Salva uma nota Markdown formatada no vault do Obsidian. "
                "Chame esta ferramenta somente quando o conteúdo já estiver "
                "consolidado e pronto para ser arquivado."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Título da nota (vira o nome do arquivo .md).",
                    },
                    "content": {
                        "type": "string",
                        "description": "Conteúdo Markdown completo da nota.",
                    },
                    "folder": {
                        "type": "string",
                        "description": (
                            "Subpasta dentro do vault onde salvar "
                            "(padrão: 'NEXUS/Pesquisas')."
                        ),
                        "default": "NEXUS/Pesquisas",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Lista de tags Obsidian para a nota.",
                        "default": [],
                    },
                },
                "required": ["title", "content"],
            },
        },
    },
]


# ---------------------------------------------------------------------------
# Implementações das ferramentas
# ---------------------------------------------------------------------------


def web_search(query: str, max_results: int = 5) -> dict[str, Any]:
    """Busca no DuckDuckGo via HTML scraping (sem API key necessária)."""
    max_results = min(max_results, 10)
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
    except requests.RequestException as exc:
        return {"error": str(exc), "results": []}

    soup = BeautifulSoup(resp.text, "html.parser")
    results: list[dict] = []

    for item in soup.select(".result")[:max_results]:
        title_tag = item.select_one(".result__title")
        snippet_tag = item.select_one(".result__snippet")
        link_tag = item.select_one(".result__url")

        title = title_tag.get_text(strip=True) if title_tag else ""
        snippet = snippet_tag.get_text(strip=True) if snippet_tag else ""
        link_href = link_tag.get_text(strip=True) if link_tag else ""

        # DuckDuckGo às vezes coloca o href no atributo data-href
        a_tag = item.select_one("a.result__a")
        real_url = ""
        if a_tag:
            real_url = a_tag.get("href", "")
            # Desembala redirecionamento DDG se necessário
            if real_url.startswith("//duckduckgo.com/l/"):
                import urllib.parse
                qs = urllib.parse.parse_qs(urllib.parse.urlparse(real_url).query)
                real_url = qs.get("uddg", [link_href])[0]

        if title or snippet:
            results.append({"title": title, "snippet": snippet, "url": real_url})

    return {"query": query, "results": results}


def scrape_page(url: str, max_chars: int = 4000) -> dict[str, Any]:
    """Extrai texto limpo de uma URL."""
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        )
    }
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as exc:
        return {"error": str(exc), "url": url, "text": ""}

    soup = BeautifulSoup(resp.text, "html.parser")

    # Remove elementos indesejados
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "form", "noscript", "iframe"]):
        tag.decompose()

    # Pega o texto principal
    text = soup.get_text(separator="\n")
    # Limpa linhas em branco excessivas
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    text = "\n".join(lines)
    # Trunca
    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[... texto truncado ...]"

    return {"url": url, "text": text}


def save_to_obsidian(
    title: str,
    content: str,
    vault_path: str,
    folder: str = "NEXUS/Pesquisas",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Salva uma nota Markdown formatada no vault Obsidian."""
    tags = tags or []
    now = datetime.datetime.now()

    # Frontmatter YAML padrão Obsidian
    tag_str = "\n".join(f"  - {t}" for t in ["nexus", "pesquisa-autonoma"] + tags)
    frontmatter = textwrap.dedent(f"""\
        ---
        title: "{title}"
        created: {now.strftime('%Y-%m-%d %H:%M')}
        source: NEXUS Agent
        tags:
        {tag_str}
        ---

    """)

    full_content = frontmatter + content

    # Sanitiza o nome do arquivo
    safe_title = re.sub(r'[\\/*?:"<>|]', "", title).strip()
    safe_title = re.sub(r"\s+", " ", safe_title)[:100]
    filename = f"{now.strftime('%Y-%m-%d')} {safe_title}.md"

    # Resolve o caminho dentro do vault
    target_dir = Path(vault_path) / folder
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        target_file = target_dir / filename
        target_file.write_text(full_content, encoding="utf-8")
        return {
            "saved": True,
            "path": str(target_file),
            "title": title,
            "filename": filename,
        }
    except OSError as exc:
        return {"saved": False, "error": str(exc), "title": title}


# ---------------------------------------------------------------------------
# Dispatcher — chamado pelo ResearchAgent para executar as ferramentas
# ---------------------------------------------------------------------------

TOOL_MAP = {
    "web_search": web_search,
    "scrape_page": scrape_page,
    "save_to_obsidian": save_to_obsidian,
}


def dispatch(
    tool_name: str,
    arguments: dict[str, Any],
    vault_path: str = "",
) -> Any:
    """Executa a ferramenta pelo nome, injetando vault_path quando necessário."""
    if tool_name not in TOOL_MAP:
        return {"error": f"Ferramenta desconhecida: {tool_name}"}

    if tool_name == "save_to_obsidian":
        arguments = {**arguments, "vault_path": vault_path}

    return TOOL_MAP[tool_name](**arguments)
