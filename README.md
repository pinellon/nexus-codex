# NEXUS Desktop

Interface desktop em CustomTkinter com:

- Chat com timestamps, copiar mensagem e historico por setas.
- 4 abas: Chat, Automacao, Configuracoes e Logs.
- Aba Coder com editor, runner, IA de codigo, Git, terminal e snippets.
- Monitor ao vivo com graficos Canvas de CPU, RAM e disco.
- Toast notifications no canto inferior direito.
- Efeitos visuais com scanner animado, ticker de status e microfeedback nos botoes.
- Sons leves de hover, clique, sucesso, aviso e erro, configuraveis pela UI.
- Configuracoes persistentes em `data/settings.json`.
- Memoria Obsidian: consulta o vault antes da IA e registra respostas novas em Markdown.
- Atalhos `Ctrl+1..4`, `Ctrl+K` para focar input e `Ctrl+L` para limpar chat.

## Rodar

```powershell
cd C:\Users\nicol\AppData\Local\Temp
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
- `ui_coding/coder_panel.py`: painel visual da aba Coder.
