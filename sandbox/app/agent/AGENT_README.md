# NEXUS Agent — Agente Autônomo de Pesquisa

Módulo que permite ao NEXUS executar tarefas de pesquisa de forma totalmente
autônoma, sem intervenção do usuário.

## Como funciona

```
Usuário: "Nexus, pesquisa os melhores cursos de Rust 2025 e salva no Obsidian"
   │
   ▼
CommandRouter detecta intenção de agente
   │
   ▼
ResearchAgent inicia loop agentic (gpt-4o-mini + function calling)
   │
   ├─► web_search("melhores cursos Rust 2025")
   │      └─ DuckDuckGo → 5 resultados
   │
   ├─► scrape_page("https://...")       ← lê as páginas mais relevantes
   │      └─ texto limpo extraído
   │
   ├─► (mais buscas/scrapes se necessário)
   │
   └─► save_to_obsidian(title, conteúdo consolidado em Markdown)
          └─ Nota criada em vault/NEXUS/Pesquisas/2025-XX-XX Cursos Rust.md

UI exibe cada etapa em tempo real no chat do NEXUS
```

## Instalação

Adicione ao `requirements.txt`:

```
beautifulsoup4>=4.12.0
```

Instale:

```bash
pip install beautifulsoup4
```

## Estrutura de arquivos

```
app/agent/
├── __init__.py          # expõe ResearchAgent
├── tools.py             # web_search, scrape_page, save_to_obsidian
├── research_agent.py    # loop agentic principal
└── agent_commands.py    # integração com CommandRouter
```

## Configurações necessárias (settings.json / .env)

```json
{
  "openai_api_key": "sk-...",
  "obsidian_vault_path": "C:\\Users\\nicol\\OneDrive\\Apps\\cerebro-nexus\\nexus",
  "agent_model": "gpt-4o-mini"
}
```

## Plugando no CommandRouter

Ver `PATCH_command_router.py` para as 4 linhas que precisam ser adicionadas.

## Comandos de voz reconhecidos

```
Nexus, pesquisa Python async e salva no Obsidian
Nexus, pesquise os melhores livros de IA de 2025 e salve
Nexus, busca tutoriais de FastAPI e salva no Obsidian
Nexus, agente pesquisa sobre Rust lang
Nexus, modo agente: encontra artigos sobre embeddings
Nexus, parar agente       ← interrompe a tarefa em andamento
```

## Estrutura de uma nota salva

```markdown
---
title: "Melhores cursos de Rust 2025"
created: 2025-07-10 14:32
source: NEXUS Agent
tags:
  - nexus
  - pesquisa-autonoma
  - rust
---

## Melhores cursos de Rust 2025

### Resumo
...conteúdo consolidado das fontes pesquisadas...

### Fontes
- [The Rust Programming Language](https://doc.rust-lang.org/book/)
- ...
```

## Rodando os testes

```bash
pytest tests/test_agent.py -v
```

## Estendendo com novas ferramentas

Para adicionar uma nova ferramenta (ex: `summarize_youtube`):

1. Implemente a função em `tools.py`
2. Adicione o schema em `TOOL_SCHEMAS`
3. Registre no `TOOL_MAP`

O agente começará a usar automaticamente na próxima execução.
