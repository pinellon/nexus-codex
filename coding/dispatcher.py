"""Dispatcher de intencoes do NEXUS CODER."""

from __future__ import annotations

import re
from typing import Callable, Optional

try:
    import pyperclip
except Exception:
    pyperclip = None

from coding.code_assistant import (
    completar_codigo,
    converter_linguagem,
    corrigir_erro,
    documentar_codigo,
    explicar_codigo,
    gerar_codigo,
    gerar_testes,
    otimizar_performance,
    pair_program,
    refatorar_codigo,
    responder_duvida_tecnica,
    revisar_codigo,
    revisar_seguranca,
)
from coding.code_runner import executar_auto, instalar_pacote
from coding.file_manager import (
    abrir_no_editor,
    buscar_em_projeto,
    contar_linhas_projeto,
    criar_arquivo_codigo,
    definir_projeto,
    ler_arquivo,
    listar_projeto,
)
from coding.git_ops import add, commit, commit_rapido, criar_branch, diff, log, pull, push, resumo_repositorio, status
from coding.intent_coding import CodingIntent
from coding.snippet_vault import buscar_snippets, estatisticas, formatar_lista, listar_snippets, salvar_snippet
from coding.terminal import executar, get_history, verificar_ambiente

try:
    from app.error_handler import handle_error
    from app.logger import log_action
except ImportError:
    def handle_error(error: Exception) -> str: return str(error)
    def log_action(text: str): print(text)

_contexto_codigo = ""
_arquivo_atual = ""
_linguagem_atual = "python"
_stack_projeto = ""


def set_contexto(codigo: str = "", arquivo: str = "", linguagem: str = "", stack: str = ""):
    global _contexto_codigo, _arquivo_atual, _linguagem_atual, _stack_projeto
    if codigo:
        _contexto_codigo = codigo
    if arquivo:
        _arquivo_atual = arquivo
    if linguagem:
        _linguagem_atual = linguagem
    if stack:
        _stack_projeto = stack


def _get_codigo(params: dict) -> str:
    if params.get("codigo"):
        return params["codigo"]
    if _contexto_codigo:
        return _contexto_codigo
    if pyperclip:
        try:
            clip = pyperclip.paste()
            if clip and len(clip) > 10:
                return clip
        except Exception:
            pass
    return ""


def _get_arquivo(params: dict) -> str:
    return params.get("arquivo", "") or _arquivo_atual


def executar_intent(intent: CodingIntent, confirm_callback: Optional[Callable] = None) -> str:
    name = intent.name
    params = intent.params
    log_action(f"CODER: {name} {params}")
    try:
        if name == "gerar_codigo":
            return gerar_codigo(params.get("descricao", ""), params.get("linguagem", _linguagem_atual), _arquivo_atual)

        if name == "gerar_e_salvar":
            answer = gerar_codigo(params.get("descricao", ""), params.get("linguagem", "python"))
            match = re.search(r"```(?:\w+)?\n(.*?)```", answer, re.DOTALL)
            code = match.group(1).strip() if match else answer
            result = criar_arquivo_codigo(params.get("nome", "output.py"), code)
            return f"{answer}\n\n{result.message}"

        if name == "explicar_codigo":
            code = _get_codigo(params)
            return explicar_codigo(code, params.get("nivel", "intermediario")) if code else "Cole ou selecione o codigo que deseja explicar."

        if name == "revisar_codigo":
            file = _get_arquivo(params)
            code = ler_arquivo(file).data if file else _get_codigo(params)
            return revisar_codigo(code) if code else "Cole o codigo ou informe um arquivo para revisar."

        if name == "refatorar_codigo":
            code = _get_codigo(params)
            return refatorar_codigo(code, params.get("objetivo", "")) if code else "Cole o codigo que deseja refatorar."

        if name == "gerar_testes":
            target = params.get("alvo", "")
            code = ler_arquivo(target).data if target else _get_codigo(params)
            return gerar_testes(code, params.get("framework", "pytest")) if code else "Informe o arquivo ou cole o codigo para gerar testes."

        if name == "documentar_codigo":
            code = _get_codigo(params)
            return documentar_codigo(code, params.get("estilo", "google")) if code else "Cole o codigo que deseja documentar."

        if name == "corrigir_erro":
            code = _get_codigo(params)
            err = params.get("erro", "")
            return corrigir_erro(code, err) if (code or err) else "Cole o codigo com erro e a mensagem de erro."

        if name == "converter_linguagem":
            code = _get_codigo(params)
            return converter_linguagem(code, params.get("de", ""), params.get("para", "python")) if code else "Cole o codigo para converter."

        if name == "otimizar_performance":
            code = _get_codigo(params)
            return otimizar_performance(code, _linguagem_atual) if code else "Cole o codigo para otimizar."

        if name == "revisar_seguranca":
            code = _get_codigo(params)
            return revisar_seguranca(code) if code else "Cole o codigo para auditoria de seguranca."

        if name == "completar_codigo":
            code = _get_codigo(params)
            return completar_codigo(code) if code else "Cole o codigo incompleto para completar."

        if name == "pair_program":
            return pair_program(params.get("mensagem", ""), params.get("contexto", ""), _arquivo_atual, _stack_projeto)

        if name == "executar_codigo":
            code = _get_codigo(params)
            return executar_auto(code, _linguagem_atual).format() if code else "Cole o codigo para executar."

        if name == "terminal_exec":
            return executar(params.get("comando", ""), confirmar_callback=confirm_callback).format()
        if name == "instalar_pacote":
            pkg = params.get("pacote", "")
            return instalar_pacote(pkg).format() if pkg else "Qual pacote deseja instalar?"
        if name == "verificar_ambiente":
            return verificar_ambiente()
        if name == "terminal_history":
            return get_history()

        if name == "git_status":
            return str(status())
        if name == "git_diff":
            return str(diff())
        if name == "git_log":
            return str(log(params.get("n", 10)))
        if name == "git_add":
            return str(add(params.get("arquivo", ".")))
        if name == "git_commit":
            msg = params.get("mensagem", "")
            return str(commit(msg)) if msg else "Qual a mensagem do commit?"
        if name == "git_commit_ai":
            return str(commit_rapido())
        if name == "git_push":
            return str(push())
        if name == "git_pull":
            return str(pull())
        if name == "git_branch":
            branch = params.get("nome", "")
            return str(criar_branch(branch)) if branch else "Qual o nome da branch?"
        if name == "git_resumo":
            return resumo_repositorio()

        if name == "definir_projeto":
            return str(definir_projeto(params.get("caminho", "")))
        if name == "estrutura_projeto":
            return listar_projeto().message
        if name == "contar_linhas":
            return contar_linhas_projeto().message
        if name == "buscar_projeto":
            return buscar_em_projeto(params.get("termo", "")).message
        if name == "ler_arquivo":
            result = ler_arquivo(params.get("arquivo", ""))
            return f"{result.message}\n\n```\n{result.data[:4000]}\n```" if result.success else result.message
        if name == "abrir_editor":
            return str(abrir_no_editor(params.get("arquivo", "")))

        if name == "salvar_snippet":
            code = _get_codigo(params)
            if not code:
                return "Cole o codigo que deseja salvar como snippet."
            snippet = salvar_snippet(params.get("titulo", "Snippet sem titulo"), code, _linguagem_atual)
            return f"Snippet salvo: [{snippet['id']}] {snippet['titulo']}"
        if name == "buscar_snippets":
            return formatar_lista(buscar_snippets(params.get("termo", "")))
        if name == "listar_snippets":
            return formatar_lista(listar_snippets(params.get("linguagem", "")))
        if name == "snippets_stats":
            return estatisticas()

        return responder_duvida_tecnica(name + str(params), _stack_projeto)
    except Exception as error:
        return handle_error(error)
