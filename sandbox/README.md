# NEXUS Desktop / NEXUS Codex

Interface desktop em CustomTkinter com foco em produtividade, automacao, voz e programacao assistida.

## Recursos atuais

- Chat com timestamps, copiar mensagem e historico por setas.
- 4 abas: Chat, Automacao, Configuracoes e Logs.
- Aba Coder com editor, runner, IA de codigo, Git, terminal e snippets.
- Scaffolding de projetos: FastAPI, React/Vite, Express, Flask, CLI e biblioteca Python.
- Copiloto local com contexto do projeto, preview de diff e aplicacao de patch.
- Modo operacional com VoiceLoop, CommandRouter, SafetyManager e EditorBridge.
- Monitor ao vivo com graficos Canvas de CPU, RAM e disco.
- Toast notifications no canto inferior direito.
- Efeitos visuais com scanner animado, ticker de status e microfeedback nos botoes.
- Sons leves de hover, clique, sucesso, aviso e erro, configuraveis pela UI.
- Configuracoes persistentes em `data/settings.json`.
- Memoria Obsidian: consulta o vault antes da IA e registra respostas novas em Markdown.
- Atalhos `Ctrl+1..4`, `Ctrl+K` para focar input e `Ctrl+L` para limpar chat.

## Novidades adicionadas

- Wake word configuravel com `voice_require_wake_word`.
- Timeout de escuta configuravel por `voice_listen_timeout`.
- Limite de frase configuravel por `voice_phrase_time_limit`.
- Cache de backend de voz para melhorar estabilidade.
- Modo descanso por voz: `Nexus, parar`.
- Reativacao por voz: `Nexus, acordar`.
- Templates de automacao em `app/features/command_templates.py`.
- Sugestoes de comando em `app/features/command_suggestions.py`.
- Gravador de sessao em `app/features/session_recorder.py`.
- Diagnostico de saude do projeto em `app/features/project_health.py`.
- Pipeline conectada para `modo foco`, `diagnostico do projeto`, `ultimos eventos` e `ajuda`.
- Agente autonomo de pesquisa em `app/agent/`, com busca web, leitura de paginas e salvamento no Obsidian.
- Modulo de visao em `app/vision/`, com captura de tela, camera, OCR inteligente e analise por GPT-4o Vision.
- Modulo residencial em `app/home/`, com Home Assistant e Spotify via comandos naturais.

## Rodar

```powershell
pip install -r requirements.txt
python main.py
```

Modo demo de voz:

```powershell
python main.py --voice-demo
```

## Comandos de voz uteis

```text
Nexus, abrir Chrome
Nexus, abrir Spotify
Nexus, abrir VS Code
Nexus, status do PC
Nexus, pesquisar Python no Google
Nexus, tirar print
Nexus, modo foco
Nexus, modo aula
Nexus, modo apresentacao
Nexus, diagnostico rapido
Nexus, diagnostico do projeto
Nexus, ultimos eventos
Nexus, rode esse codigo
Nexus, explique esse codigo
Nexus, corrija esse codigo
Nexus, documente esse codigo
Nexus, pesquisa Python async e salva no Obsidian
Nexus, parar agente
Nexus, descreve a tela
Nexus, leia o texto da tela
Nexus, analisa o codigo na tela
Nexus, olha a camera
Nexus, apaga as luzes
Nexus, status da casa
Nexus, autentica no Spotify
Nexus, toca AC/DC no Spotify
Nexus, o que esta tocando?
Nexus, parar
Nexus, acordar
```

## Arquivos principais

- `ui/desktop_app.py`: janela principal.
- `ui/widgets.py`: `LiveGraph`, `PulseIndicator`, `MiniBar` e `Toast`.
- `app/settings_manager.py`: configuracoes persistentes.
- `app/command_history.py`: historico de comandos.
- `app/obsidian_memory.py`: conexao com vault Obsidian e memoria Markdown.
- `coding/`: modulo NEXUS CODER.
- `coding/scaffolder.py`: gerador de projetos por template.
- `coding/project_context.py`: snapshot seguro do projeto ativo.
- `coding/patcher.py`: preview e aplicacao de patches.
- `coding/workspace_ai.py`: acoes de IA que geram patch revisavel.
- `app/core/command_router.py`: classifica comandos e mostra o que foi entendido.
- `app/core/safety.py`: confirma comandos de risco antes da execucao.
- `app/voice/voice_loop.py`: escuta continua em thread separada.
- `app/coder/editor_bridge.py`: ponte entre voz, botoes e editor.
- `app/features/`: recursos extras como modos inteligentes, diagnostico e memoria de sessao.
- `app/agent/`: agente autonomo de pesquisa com ferramentas de web search, scrape e Obsidian.
- `app/vision/`: captura e analise visual de tela/camera.
- `app/home/`: automacao residencial via Home Assistant e controle Spotify.
- `app/plugins/`: base para comandos externos sem mexer no nucleo.
- `main.py`: launcher da UI e modo `--voice-demo`.
- `ui_coding/coder_panel.py`: painel visual da aba Coder.

## Ideias futuras

- Exibir `project_health` em um card visual na aba Logs.
- Criar loja de plugins local para instalar comandos novos sem editar o nucleo.
- Transformar templates em editor visual dentro da aba Automacao.
