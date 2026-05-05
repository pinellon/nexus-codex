"""Detector de intencoes de programacao."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass
class CodingIntent:
    name: str
    params: dict


def detectar_intent_coding(texto: str) -> CodingIntent | None:
    t = texto.lower().strip()

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

    if re.search(r"\b(?:roda?|executa?|run)\b.*\b(?:codigo|código|snippet)\b", t):
        return CodingIntent("executar_codigo", {})

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
