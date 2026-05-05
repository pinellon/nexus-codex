"""
NEXUS — Assistente Pessoal Desktop
Ponto de entrada principal do sistema.

Uso:
    python main.py
"""

import sys
import os
import re
from pathlib import Path

# Garantir que o diretório raiz do projeto esteja no PYTHONPATH
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Criar pastas necessárias antes de importar os módulos
(ROOT / "data").mkdir(exist_ok=True)
(ROOT / "data" / "logs").mkdir(exist_ok=True)

from app.logger import log_action, log_error, log_command
from app.error_handler import handle_error
from app.intent_router import detectar_intent
from app.security import precisa_confirmacao, mensagem_confirmacao
from app.memory import save_message, clear_memory
from app.config import NEXUS_OWNER
from coding.intent_coding import detectar_intent_coding
from coding.dispatcher import executar_intent as executar_coding_intent


def processar_comando(texto: str, confirm_callback=None) -> str:
    """
    Ponto central de processamento de comandos.
    1. Detecta intenção.
    2. Verifica segurança.
    3. Executa ação ou conversa com IA.
    """
    texto = texto.strip()
    if not texto:
        return "."

    log_command(texto)

    obsidian_response = _processar_obsidian(texto)
    if obsidian_response:
        return obsidian_response

    # Detectar intenção de programação antes do roteador geral
    coding_intent = detectar_intent_coding(texto)
    if coding_intent:
        return executar_coding_intent(coding_intent, confirm_callback)

    # Detectar intenção
    intent = detectar_intent(texto)

    if intent is None:
        # Sem intenção detectada → conversa com a IA
        return _responder_ia(texto)

    # Verificar se precisa de confirmação
    if precisa_confirmacao(intent.name):
        pergunta = mensagem_confirmacao(intent.name)
        confirmado = confirm_callback(pergunta) if confirm_callback else False
        if not confirmado:
            return "Ação cancelada."

    # Executar a intenção
    return _executar_intent(intent)


def _processar_obsidian(texto: str) -> str:
    """Comandos diretos para memoria Obsidian."""
    t = texto.strip()
    low = t.lower()
    if "obsidian" not in low and "vault" not in low:
        return ""
    try:
        from app.obsidian_memory import configure_vault, register, search_or_status
        if any(k in low for k in ("status", "conectado", "configurado")):
            return search_or_status()
        m = re.search(r"(?:conecta|configura|define|usar|usa)\s+(?:o\s+)?(?:obsidian|vault)(?:\s+em|\s+para|\s+como)?\s+(.+)", t, re.IGNORECASE)
        if m:
            return configure_vault(m.group(1).strip().strip('"'))
        m = re.search(r"(?:busca|procura|pesquisa)\s+(?:no\s+)?(?:obsidian|vault)\s+(.+)", t, re.IGNORECASE)
        if m:
            return search_or_status(m.group(1).strip())
        m = re.search(r"(?:salva|registra|guarda)\s+(?:no\s+)?(?:obsidian|vault)\s+(.+)", t, re.IGNORECASE)
        if m:
            note = register("Registro manual", m.group(1).strip(), source="nexus-manual")
            return f"Registrado no Obsidian: {note}" if note else "Nao consegui registrar no Obsidian. Verifique o vault nas Configuracoes."
        return search_or_status()
    except Exception as e:
        return handle_error(e)


def _executar_intent(intent) -> str:
    """Despacha a intenção para o módulo correto."""
    try:
        name = intent.name
        p = intent.params

        # ── Aplicativos ────────────────────────────────────────────
        if name == "abrir_chrome":
            from automation.apps import abrir_chrome
            return abrir_chrome()

        elif name == "abrir_edge":
            from automation.apps import abrir_edge
            return abrir_edge()

        elif name == "abrir_spotify":
            from automation.media import abrir_spotify
            return abrir_spotify()

        elif name == "abrir_vscode":
            from automation.apps import abrir_vscode
            return abrir_vscode()

        elif name == "abrir_bloco_de_notas":
            from automation.apps import abrir_bloco_de_notas
            return abrir_bloco_de_notas()

        elif name == "abrir_calculadora":
            from automation.apps import abrir_calculadora
            return abrir_calculadora()

        elif name == "abrir_programa":
            from automation.apps import abrir_programa_por_nome
            return abrir_programa_por_nome(p.get("nome", ""))

        # ── Navegador ──────────────────────────────────────────────
        elif name == "abrir_youtube":
            from automation.browser import abrir_youtube
            return abrir_youtube()

        elif name == "abrir_site":
            from automation.browser import abrir_site
            return abrir_site(p.get("url", ""))

        elif name == "pesquisar_google":
            from automation.browser import pesquisar_google
            return pesquisar_google(p.get("termo", ""))

        elif name == "pesquisar_youtube":
            from automation.browser import pesquisar_youtube
            return pesquisar_youtube(p.get("termo", ""))

        # ── Mídia ──────────────────────────────────────────────────
        elif name == "tocar_spotify":
            from automation.media import tocar_musica_spotify
            return tocar_musica_spotify(p.get("musica", ""))

        elif name == "tocar_youtube":
            from automation.media import tocar_musica_youtube
            return tocar_musica_youtube(p.get("musica", ""))

        elif name == "tocar_musica":
            from automation.media import escolher_plataforma_e_tocar
            return escolher_plataforma_e_tocar(p.get("musica", ""))

        # ── Arquivos ───────────────────────────────────────────────
        elif name == "abrir_downloads":
            from automation.files import abrir_downloads
            return abrir_downloads()

        elif name == "abrir_desktop":
            from automation.files import abrir_area_trabalho
            return abrir_area_trabalho()

        elif name == "criar_arquivo":
            from automation.files import criar_arquivo
            return criar_arquivo(p.get("nome", "arquivo.txt"))

        elif name == "procurar_arquivo":
            from automation.files import procurar_arquivo
            return procurar_arquivo(p.get("nome", ""))

        # ── Sistema / PC ───────────────────────────────────────────
        elif name == "status_pc":
            from automation.pc_control import mostrar_cpu_ram_disco
            return mostrar_cpu_ram_disco()

        elif name == "desligar_pc":
            from automation.pc_control import desligar_pc
            return desligar_pc()

        elif name == "reiniciar_pc":
            from automation.pc_control import reiniciar_pc
            return reiniciar_pc()

        elif name == "suspender_pc":
            from automation.pc_control import suspender_pc
            return suspender_pc()

        elif name == "bloquear_tela":
            from automation.pc_control import bloquear_tela
            return bloquear_tela()

        # ── Volume ─────────────────────────────────────────────────
        elif name == "aumentar_volume":
            from automation.system import aumentar_volume
            return aumentar_volume()

        elif name == "diminuir_volume":
            from automation.system import diminuir_volume
            return diminuir_volume()

        elif name == "mutar_volume":
            from automation.system import mutar_volume
            return mutar_volume()

        # ── Utilitários ────────────────────────────────────────────
        elif name == "tirar_print":
            from automation.system import tirar_print
            return tirar_print()

        elif name == "mostrar_data_hora":
            from automation.system import mostrar_data_hora
            return mostrar_data_hora()

        elif name == "limpar_memoria":
            clear_memory()
            return "Memória limpa."

        else:
            return _responder_ia(f"[Intenção desconhecida: {name}]")

    except Exception as e:
        return handle_error(e)


def _responder_ia(texto: str) -> str:
    """Envia o texto para a IA e retorna a resposta."""
    try:
        from app.assistant import responder
        return responder(texto)
    except Exception as e:
        return handle_error(e)


def main():
    """Inicializa o sistema NEXUS."""
    log_action("Sistema NEXUS iniciando...")

    # Verificar configuração da OpenAI (aviso, não erro fatal)
    from app.config import OPENAI_API_KEY
    if not OPENAI_API_KEY or OPENAI_API_KEY == "sua_chave_aqui":
        print("[AVISO] OPENAI_API_KEY não configurada. Respostas de IA indisponíveis.")
        print("        Configure o arquivo .env com sua chave da OpenAI.")

    # Iniciar interface
    from ui.desktop_app import NexusApp
    app = NexusApp(on_command_callback=processar_comando)
    log_action("Interface iniciada.")
    app.run()


if __name__ == "__main__":
    main()
