"""NEXUS CODER: chamadas de IA especializadas em programacao."""

from __future__ import annotations

import os
from typing import Optional

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    from app.config import OPENAI_API_KEY, OPENAI_MODEL
    from app.logger import log_action, log_error
    from app.memory import get_recent_history, save_message
except ImportError:
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = "gpt-4o-mini"

    def log_action(text: str): print(f"[ACTION] {text}")
    def log_error(text: str): print(f"[ERROR] {text}")
    def save_message(role: str, content: str): pass
    def get_recent_history(n: int = 8): return []


CODER_SYSTEM_PROMPT = """Voce e o NEXUS CODER, modulo de programacao do NEXUS.
Responda sempre em portugues do Brasil.
Seja direto, tecnico e eficiente.
Use blocos de codigo com a linguagem correta.
Quando revisar, liste bugs por prioridade e mostre a correcao.
Quando gerar codigo, entregue codigo completo, idiomatico e sem TODOs vazios.
Em Python, use type hints e docstrings quando fizer sentido.
Respeite o contexto do projeto fornecido."""

_client: Optional[object] = None
_client_key: str | None = None


def _current_key() -> str:
    try:
        import app.config as cfg
        return getattr(cfg, "OPENAI_API_KEY", "") or os.getenv("OPENAI_API_KEY", "")
    except Exception:
        return OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")


def _get_client():
    global _client, _client_key
    if OpenAI is None:
        raise RuntimeError("Pacote openai nao instalado. Rode: pip install -r requirements.txt")
    key = _current_key()
    if not key:
        raise RuntimeError("API Key nao configurada. Salve a chave em Configuracoes.")
    if _client is None or _client_key != key:
        _client = OpenAI(api_key=key)
        _client_key = key
    return _client


def _call_ai(prompt: str, system_extra: str = "", max_tokens: int = 1500) -> str:
    """Chamada base para a OpenAI usando o prompt especializado do CODER."""
    try:
        system = CODER_SYSTEM_PROMPT + (f"\n\n{system_extra}" if system_extra else "")
        messages = [{"role": "system", "content": system}]
        messages.extend(get_recent_history(6))
        messages.append({"role": "user", "content": prompt})
        resp = _get_client().chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.3,
        )
        result = (resp.choices[0].message.content or "").strip()
        save_message("user", prompt)
        save_message("assistant", result)
        log_action(f"CODER AI: {prompt[:80]}")
        return result
    except Exception as error:
        log_error(f"CODER AI error: {error}")
        return f"Erro ao chamar IA de codigo: {error}"


def gerar_codigo(descricao: str, linguagem: str = "python", contexto_arquivo: str = "") -> str:
    ctx = f"\n\nContexto do arquivo atual:\n```\n{contexto_arquivo[:2500]}\n```" if contexto_arquivo else ""
    return _call_ai(
        f"""Gere codigo completo em {linguagem} para:

{descricao}{ctx}

Requisitos:
- Codigo funcional e completo.
- Tratamento de erros adequado.
- Comentarios em portugues apenas onde ajudarem.
- Se for Python: type hints e docstrings.""",
        max_tokens=2200,
    )


def explicar_codigo(codigo: str, nivel: str = "intermediario") -> str:
    return _call_ai(
        f"""Explique este codigo em nivel {nivel}.

```
{codigo}
```

Estruture em: o que faz, como funciona, pontos de atencao.""",
        max_tokens=1400,
    )


def revisar_codigo(codigo: str, linguagem: str = "auto") -> str:
    return _call_ai(
        f"""Revise este codigo {linguagem}.

```
{codigo}
```

Liste problemas por prioridade: CRITICO, MEDIO, AVISO.
Para cada problema, indique linha/motivo/correcao.
Ao final entregue uma versao corrigida completa quando aplicavel.""",
        max_tokens=2400,
    )


def refatorar_codigo(codigo: str, objetivo: str = "") -> str:
    foco = f"Foco: {objetivo}." if objetivo else ""
    return _call_ai(
        f"""Refatore o codigo abaixo. {foco}

```
{codigo}
```

Responda com melhorias, codigo completo e explicacao curta.""",
        max_tokens=2200,
    )


def gerar_testes(codigo: str, framework: str = "pytest") -> str:
    return _call_ai(
        f"""Gere testes unitarios completos usando {framework} para:

```
{codigo}
```

Inclua happy path, edge cases, erros e mocks quando necessario.""",
        max_tokens=2200,
    )


def documentar_codigo(codigo: str, estilo: str = "google") -> str:
    return _call_ai(
        f"""Documente este codigo no estilo {estilo}:

```
{codigo}
```

Inclua docstrings, parametros, exemplos e excecoes possiveis.""",
        max_tokens=1800,
    )


def corrigir_erro(codigo: str, mensagem_erro: str) -> str:
    return _call_ai(
        f"""Analise e corrija o erro.

CODIGO:
```
{codigo}
```

ERRO:
```
{mensagem_erro}
```

Responda causa raiz, codigo corrigido e como evitar.""",
        max_tokens=1800,
    )


def converter_linguagem(codigo: str, de: str, para: str) -> str:
    return _call_ai(
        f"""Converta de {de} para {para}, mantendo a logica e usando idioms nativos.

```{de}
{codigo}
```""",
        max_tokens=2200,
    )


def otimizar_performance(codigo: str, linguagem: str = "python") -> str:
    return _call_ai(
        f"""Otimize a performance deste codigo {linguagem}.

```{linguagem}
{codigo}
```

Inclua Big O, gargalos, codigo otimizado e comparacao antes/depois.""",
        max_tokens=2200,
    )


def revisar_seguranca(codigo: str) -> str:
    return _call_ai(
        f"""Faca auditoria de seguranca neste codigo:

```
{codigo}
```

Procure injection, XSS/CSRF, path traversal, secrets, inputs sem validacao e outras falhas.""",
        max_tokens=2200,
    )


def responder_duvida_tecnica(pergunta: str, contexto_projeto: str = "") -> str:
    ctx = f"\n\nStack/contexto: {contexto_projeto}" if contexto_projeto else ""
    return _call_ai(
        f"""{pergunta}{ctx}

Responda com explicacao direta, exemplo funcional e quando usar/evitar.""",
        max_tokens=1600,
    )


def completar_codigo(codigo_parcial: str, instrucao: str = "") -> str:
    return _call_ai(
        f"""Complete este codigo. {instrucao}

```
{codigo_parcial}
```

Entregue o codigo completo, preservando estilo e convencoes.""",
        max_tokens=2200,
    )


def pair_program(mensagem: str, contexto_projeto: str = "", arquivo_atual: str = "", stack: str = "") -> str:
    extra = ""
    if contexto_projeto:
        extra += f"\nProjeto atual: {contexto_projeto}"
    if stack:
        extra += f"\nStack: {stack}"
    if arquivo_atual:
        extra += f"\nArquivo aberto:\n```\n{arquivo_atual[:2500]}\n```"
    return _call_ai(mensagem, system_extra=extra, max_tokens=2200)
