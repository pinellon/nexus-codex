"""Detector de intencoes de programacao."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class CodingIntent:
    name: str
    params: dict


def detectar_intent_coding(texto: str) -> CodingIntent | None:
    raw = texto.strip()
    t = texto.lower().strip()

    if re.search(r"\b(?:lista?|mostra?|quais|ver)\b.*\b(?:templates?|scaffoldings?|scaffolds?)\b|\btemplates?\s+(?:disponiveis|disponiveis)\b", t):
        return CodingIntent("listar_templates", {})

    scaffold = _detect_scaffold(raw)
    if scaffold:
        return scaffold

    if re.search(r"\b(?:contexto|snapshot|mapa)\s+(?:do\s+)?projeto\b|\bindexa\s+(?:o\s+)?projeto\b", t):
        return CodingIntent("contexto_projeto", {})

    if re.search(r"\b(?:preview|mostra|ver)\s+(?:do\s+)?patch\b|\bdiff\s+(?:do\s+)?patch\b", t):
        return CodingIntent("preview_ai_patch", {})

    if re.search(r"\b(?:aplica?|aplicar|confirma?)\s+(?:o\s+)?patch\b|\bapply\s+patch\b", t):
        return CodingIntent("aplicar_ai_patch", {})

    if re.search(r"\b(?:roda?|executa?)\s+ruff\b|\bruff\s+check\b", t):
        return CodingIntent("run_ruff", {})

    if re.search(r"\b(?:roda?|executa?)\s+pytest\b|\bpytest\b", t):
        return CodingIntent("run_pytest", {})

    workspace_patch = _detect_workspace_patch(raw)
    if workspace_patch:
        return workspace_patch

    m = re.search(r"\b(?:gera?|cria?|escreve?|faz(?:er)?|codifica?)\s+(?:um\s+|uma\s+)?(?:codigo|código|script|funcao|função|classe|componente|api|endpoint|modulo|módulo)\s*(?:(?:em\s+)?(\w+))?\s+(?:para|que|pra)\s+(.+)", t)
    if m:
        return CodingIntent("gerar_codigo", {"linguagem": m.group(1) or "python", "descricao": m.group(2).strip()})

    m = re.search(r"\b(?:gera?|cria?)\s+(?:o\s+)?(?:arquivo\s+)?([\w.\-]+\.\w+)\s+(?:que|para|pra)\s+(.+)", t)
    if m:
        ext = m.group(1).rsplit(".", 1)[-1]
        lang = {"py": "python", "js": "javascript", "ts": "typescript", "jsx": "jsx", "tsx": "tsx"}.get(ext, ext)
        return CodingIntent("gerar_e_salvar", {"nome": m.group(1), "descricao": m.group(2), "linguagem": lang})

    if re.search(r"\b(?:explica?|explique|o que faz|como funciona)\b.*\b(?:codigo|código|funcao|função|classe|arquivo|esse|este)\b", t):
        nivel = "avancado" if "avanc" in t else "iniciante" if "iniciante" in t else "intermediario"
        return CodingIntent("explicar_codigo", {"nivel": nivel})

    if re.search(r"\b(?:revis[ae]|review|analisa?|verifica?|checa?)\b.*\b(?:codigo|código|arquivo|bug|bugs)\b", t):
        file = _file_from_text(t)
        return CodingIntent("revisar_codigo", {"arquivo": file})

    if re.search(r"\b(?:refatora?|refactor|melhora?)\b.*\b(?:codigo|código|funcao|função|classe|arquivo|esse|este)\b", t):
        m = re.search(r"(?:foco|objetivo|para)\s*:?\s*(.+)", t)
        return CodingIntent("refatorar_codigo", {"objetivo": m.group(1) if m else ""})

    if re.search(r"\b(?:gera?|cria?|escreve?)\s+(?:os?\s+)?(?:testes?|tests?|specs?|unitarios?|unitários?)\b", t):
        framework = "jest" if any(x in t for x in ["jest", "js", "ts", "react"]) else "pytest"
        return CodingIntent("gerar_testes", {"alvo": _file_from_text(t), "framework": framework})

    if re.search(r"\b(?:documenta?|docstring|jsdoc|comenta?)\b.*\b(?:codigo|código|funcao|função|classe|arquivo|esse)\b", t):
        return CodingIntent("documentar_codigo", {"estilo": "numpy" if "numpy" in t else "google"})

    if re.search(r"\b(?:corrige?|conserta?|arruma?|fix)\b.*\b(?:erro|bug|exception|traceback|problema)\b|\b(?:ta dando|tá dando|tem um)\s+(?:erro|bug)\b", t):
        return CodingIntent("corrigir_erro", {})

    m = re.search(r"\b(?:converte?|traduz?|porta?)\s+(?:de\s+)?(\w+)\s+(?:para|pra)\s+(\w+)\b", t)
    if m:
        return CodingIntent("converter_linguagem", {"de": m.group(1), "para": m.group(2)})

    if re.search(r"\b(?:auditoria|seguranca|segurança|vulnerabilidade|sql injection|xss|pentest)\b", t):
        return CodingIntent("revisar_seguranca", {})

    if re.search(r"\b(?:otimiza?|performance|performatico|performático|lento|big.?o|complexidade)\b", t):
        return CodingIntent("otimizar_performance", {})

    if re.search(r"\b(?:completa?|termina?|finaliza?)\b.*\b(?:codigo|código|funcao|função|classe|arquivo)\b", t):
        return CodingIntent("completar_codigo", {})

    if re.search(r"\b(?:roda?|rode|executa?|execute|run)\b.*\b(?:codigo|código|snippet)\b", t):
        return CodingIntent("executar_codigo", {})

    if re.search(r"\b(?:salva?|salve|salvar)\s+(?:esse\s+|este\s+|o\s+)?arquivo\b", t):
        match = re.search(r"(?:como|chamado|nome)\s+([\w.\-]+)", t)
        return CodingIntent("coder_save_file", {"arquivo": match.group(1) if match else ""})

    match = re.search(r"\b(?:cria?|crie|criar|novo)\s+(?:um\s+)?arquivo\s+(?:chamado\s+|nome\s+)?([\w.\-]+)", t)
    if match:
        return CodingIntent("coder_new_file", {"arquivo": match.group(1)})

    if re.search(r"\b(?:limpa?|limpe|limpar)\s+(?:o\s+)?(?:terminal|output|saida|saída)\b", t):
        return CodingIntent("coder_clear_output", {})

    if re.search(r"\bgit\s+status\b|\bstatus\s+(?:do\s+)?(?:git|repo|repositorio|repositório)\b", t):
        return CodingIntent("git_status", {})
    if re.search(r"\bgit\s+(?:diff|diferenca|diferença|mudancas|mudanças)\b|\b(?:diferencas|diferenças|mudancas|mudanças)\b.*\bgit\b", t):
        return CodingIntent("git_diff", {})
    if re.search(r"\bgit\s+(?:log|historico|histórico|commits?)\b|\b(?:historico|histórico|ultimos|últimos)\s+commits?\b", t):
        n_match = re.search(r"\b(\d+)\s+commits?\b", t)
        return CodingIntent("git_log", {"n": int(n_match.group(1)) if n_match else 10})
    if re.search(r"\bgit\s+(?:add|stage)\b|\badiciona?\s+.*(?:git|stage)\b", t):
        return CodingIntent("git_add", {"arquivo": "."})
    m = re.search(r"\bgit\s+commit\b|\bfaz?\s+(?:um\s+)?commit\b", t)
    if m:
        msg = re.search(r"(?:mensagem|com|msg)\s+['\"]?([^'\"]+)['\"]?", t)
        return CodingIntent("git_commit", {"mensagem": msg.group(1).strip() if msg else ""})
    if re.search(r"\bgit\s+push\b|\bpusha?\b", t):
        return CodingIntent("git_push", {})
    if re.search(r"\bgit\s+pull\b|\bpull\b.*\b(?:repo|git|repositorio|repositório)\b", t):
        return CodingIntent("git_pull", {})
    m = re.search(r"\b(?:cria?\s+)?(?:branch|galho)\s+['\"]?([\w\-/]+)['\"]?", t)
    if m:
        return CodingIntent("git_branch", {"nome": m.group(1)})
    if re.search(r"\bcommit\s+(?:automatico|automático|rapido|rápido|ia|inteligente)\b|\bgerar?\s+mensagem\s+de\s+commit\b", t):
        return CodingIntent("git_commit_ai", {})
    if re.search(r"\bresumo\s+(?:do\s+)?(?:repositorio|repositório|repo)\b|\bgit\s+resumo\b", t):
        return CodingIntent("git_resumo", {})

    m = re.search(r"\b(?:roda?|executa?|run)\s+(?:o\s+)?(?:comando\s+|script\s+|arquivo\s+)?(.+)", t)
    if m and not re.search(r"\b(codigo|código|esse|este)\b", m.group(1)):
        return CodingIntent("terminal_exec", {"comando": m.group(1).strip()})
    m = re.search(r"\binstala?\s+(?:o\s+pacote\s+|a\s+biblioteca\s+|o\s+modulo\s+|o\s+módulo\s+)?(?:python\s+)?([\w.\-]+)", t)
    if m:
        return CodingIntent("instalar_pacote", {"pacote": m.group(1)})
    if re.search(r"\bverifica?\s+(?:o\s+)?ambiente\b|\bambiente\s+de\s+desenvolvimento\b", t):
        return CodingIntent("verificar_ambiente", {})
    if re.search(r"\b(?:historico|histórico|history)\s+(?:de\s+)?(?:terminal|comandos?)\b", t):
        return CodingIntent("terminal_history", {})

    m = re.search(r"\b(?:define?|seta?|abre?|carrega?)\s+(?:o\s+)?projeto\s+(?:em\s+|como\s+)?(.+)", t)
    if m:
        return CodingIntent("definir_projeto", {"caminho": m.group(1).strip()})
    if re.search(r"\b(?:mostra?|lista?|exibe?|ver)\s+(?:a\s+)?(?:estrutura|arvore|árvore|tree)\s+(?:do\s+)?(?:projeto|pasta|diretorio|diretório)\b", t):
        return CodingIntent("estrutura_projeto", {})
    if re.search(r"\b(?:conta|contar|quantas?)\s+(?:linhas?|loc)\b|\bloc\b|\blines?\s+of\s+code\b", t):
        return CodingIntent("contar_linhas", {})
    m = re.search(r"\b(?:busca?|procura?|encontra?|search)\s+(?:por\s+)?['\"]?([^'\"]+?)['\"]?\s+(?:no\s+)?(?:projeto|codigo|código|arquivos?)\b", t)
    if m:
        return CodingIntent("buscar_projeto", {"termo": m.group(1).strip()})
    m = re.search(r"\b(?:le|lê|ler|mostra?|exibe?)\s+(?:o\s+)?(?:arquivo\s+)?([\w.\-/\\]+\.\w+)\b", t)
    if m:
        return CodingIntent("ler_arquivo", {"arquivo": m.group(1)})
    m = re.search(r"\b(?:abre?|abrir)\s+(?:o\s+)?(?:arquivo\s+)?([\w.\-/\\]+\.\w+)\s+(?:no\s+)?editor\b", t)
    if m:
        return CodingIntent("abrir_editor", {"arquivo": m.group(1)})

    m = re.search(r"\b(?:salva?|guarda?)\s+(?:esse\s+)?snippet\s+(?:como\s+|com\s+nome\s+)?['\"]?([^'\"]+)['\"]?\b", t)
    if m:
        return CodingIntent("salvar_snippet", {"titulo": m.group(1).strip()})
    m = re.search(r"\b(?:busca?|procura?)\s+snippets?\s+(?:de\s+|sobre\s+)?(.+)", t)
    if m:
        return CodingIntent("buscar_snippets", {"termo": m.group(1).strip()})
    if re.search(r"\b(?:lista?|mostra?)\s+(?:meus\s+|os\s+)?snippets?\b", t):
        lang = re.search(r"\b(python|javascript|typescript|js|ts|react)\b", t)
        return CodingIntent("listar_snippets", {"linguagem": lang.group(1) if lang else ""})
    if re.search(r"\bestatisticas?|estatísticas?\s+(?:dos\s+)?snippets?\b|\bsnippets?\s+(?:stats?|estatisticas?)\b", t):
        return CodingIntent("snippets_stats", {})

    if re.search(r"\b(?:pair\s+program|programar\s+junto|me\s+ajuda\s+a\s+(?:codar|programar|desenvolver))\b", t):
        return CodingIntent("pair_program", {"mensagem": texto})

    return None


def _file_from_text(text: str) -> str:
    match = re.search(r"([\w.\-/\\]+\.\w+)", text)
    return match.group(1) if match else ""


def _detect_scaffold(text: str) -> CodingIntent | None:
    templates = (
        r"fastapi|react|vite|express|node|nodejs|flask|cli|python-cli|lib|biblioteca|"
        r"lib-python|django|next|nextjs|electron|discord(?:-|\s)?bot"
    )
    patterns = [
        rf"\b(?:cria?r?|gera?r?|novo|nova)\s+(?:um\s+|uma\s+)?(?:projeto|project|app|api|servico|serviço)\s+({templates})(?:\s+(?:chamado|chamada|nomeado|nomeada|com\s+nome|nome)\s+|\s+)(.+)$",
        rf"\bscaffold\s+({templates})\s+(.+)$",
        rf"\b(?:cria?r?|gera?r?)\s+({templates})\s+(?:chamado|chamada|nomeado|nomeada|com\s+nome)?\s*(.+)$",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if not match:
            continue
        template = match.group(1).strip()
        name, destino = _split_name_destino(match.group(2).strip())
        if name:
            return CodingIntent("criar_projeto", {"template": template, "nome": name, "destino": destino})
    return None


def _split_name_destino(value: str) -> tuple[str, str]:
    value = value.strip().strip("'\"")
    match = re.search(r"\s+(?:em|na\s+pasta|no\s+diretorio|no\s+diretório)\s+(.+)$", value, re.IGNORECASE)
    if not match:
        return value, ""
    name = value[: match.start()].strip().strip("'\"")
    destino = match.group(1).strip().strip("'\"")
    return name, destino


def _detect_workspace_patch(text: str) -> CodingIntent | None:
    action_map = [
        (r"\b(?:gera?|cria?|faz|implementa?|codifica?)\s+(?:um\s+)?patch\s+(?:para|pra|que)?\s*(.+)$", "generate"),
        (r"\b(?:implementa?|adiciona?|cria?)\s+(?:no\s+)?projeto\s+(.+)$", "generate"),
        (r"\b(?:corrige?|conserta?|fix)\s+(?:no\s+)?projeto\s+(.+)$", "review_bugs"),
        (r"\b(?:refatora?)\s+(?:o\s+)?projeto\s+(.+)$", "refactor"),
        (r"\b(?:gera?|cria?)\s+testes?\s+(?:no\s+)?projeto\s+(.+)$", "tests"),
        (r"\b(?:documenta?)\s+(?:o\s+)?projeto\s+(.+)$", "document"),
        (r"\b(?:audita?|seguranca|segurança)\s+(?:do\s+)?projeto\s+(.+)$", "security"),
    ]
    for pattern, action_id in action_map:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            request = match.group(1).strip() or text.strip()
            return CodingIntent("workspace_ai_patch", {"acao": action_id, "pedido": request})
    return None
