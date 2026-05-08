# NEXUS Desktop

Interface desktop em CustomTkinter com:

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

## Rodar

```powershell
cd C:\Users\nicol\Documents\Codex\2026-05-03\files-mentioned-by-the-user-theme\nexus-codex-push
pip install -r requirements.txt
python theme.py
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
- `app/plugins/`: base para comandos externos sem mexer no nucleo.
- `main.py`: launcher da UI e modo `--voice-demo`.
- `ui_coding/coder_panel.py`: painel visual da aba Coder.
