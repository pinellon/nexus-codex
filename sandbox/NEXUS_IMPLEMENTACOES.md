# NEXUS - Implementacoes e Guia de Uso

Este arquivo resume tudo que foi adicionado ao NEXUS.

## Como Rodar

```powershell
cd C:\Users\nicol\Documents\Codex\2026-05-03\files-mentioned-by-the-user-theme\nexus-codex-push
pip install -r requirements.txt
python theme.py
```

## Interface Principal

O NEXUS agora tem uma interface desktop com abas:

- Chat
- Automacao
- Coder
- Configuracoes
- Logs

Atalhos:

- `Ctrl+1`: Chat
- `Ctrl+2`: Automacao
- `Ctrl+3`: Coder
- `Ctrl+4`: Configuracoes
- `Ctrl+5`: Logs
- `Ctrl+K`: focar input
- `Ctrl+L`: limpar chat

## Melhorias Visuais

Foram adicionados:

- Scanner animado no header e footer.
- Ticker de status com frases do sistema.
- Toast notifications no canto inferior direito.
- Microfeedback nos botoes.
- Sons leves de hover, clique, sucesso, aviso, erro, iniciar e parar.
- Configuracoes para ativar/desativar sons e animacoes.

Arquivos principais:

- `ui/widgets.py`
- `ui/desktop_app.py`
- `ui/theme.py`

## Chat

Melhorias adicionadas:

- Mensagens do usuario alinhadas a direita.
- Mensagens do NEXUS alinhadas a esquerda.
- Timestamp por mensagem.
- Botao de copiar em cada mensagem.
- Historico de comandos com setas `↑` e `↓`.
- Placeholder inteligente no input.
- Botao para limpar memoria.

## Monitor Ao Vivo

A aba Automacao possui monitor do sistema:

- Grafico Canvas de CPU.
- Grafico Canvas de RAM.
- Grafico Canvas de disco.
- Barras de progresso que ficam amarelas/vermelhas conforme uso.
- Footer atualizado a cada 2 segundos.

## Configuracoes

As configuracoes sao salvas em:

```text
data/settings.json
```

Configuracoes disponiveis:

- OpenAI API Key.
- Nome do dono.
- Responder por voz.
- Motor TTS: `pyttsx3`, `edge-tts`, `elevenlabs`.
- ElevenLabs API Key.
- ElevenLabs Voice ID.
- Plataforma padrao de midia.
- Sempre no topo.
- Modo compacto.
- Timestamps no chat.
- Sons da interface.
- Animacoes ambientais.
- Memoria Obsidian.

## NEXUS CODER

Foi adicionada a aba `Coder`, com:

- Editor de codigo.
- Numeros de linha.
- Seletor de linguagem.
- Output integrado.
- Rodar codigo Python, JavaScript/Node e shell.
- Copiar codigo.
- Salvar arquivo.
- Extrair bloco de codigo do output para o editor.
- Acoes rapidas de IA.

Comandos suportados:

```text
gera um codigo python para ler csv
explica o codigo
revisa o codigo
refatora o codigo
gera testes para o codigo
documenta o codigo
otimiza performance do codigo
auditoria de seguranca
converte python para javascript
roda o codigo
instala o pacote requests
verifica o ambiente
```

Arquivos principais:

- `coding/code_assistant.py`
- `coding/code_runner.py`
- `coding/file_manager.py`
- `coding/git_ops.py`
- `coding/snippet_vault.py`
- `coding/terminal.py`
- `coding/intent_coding.py`
- `coding/dispatcher.py`
- `ui_coding/coder_panel.py`

## Git

Comandos integrados:

```text
git status
git diff
git log
git add
faz commit com mensagem "fix: corrige bug"
commit automatico com ia
git push
git pull
cria branch feature/nova-funcao
resumo do repositorio
```

## Terminal Inteligente

Recursos:

- Executa comandos no projeto ativo.
- Aliases de produtividade.
- Historico de comandos.
- Confirmacao para comandos perigosos.
- Verificacao de ferramentas instaladas.

Exemplos:

```text
roda npm install
roda pytest
roda python manage.py migrate
historico de terminal
verifica o ambiente
```

## Gerenciador de Projeto

Comandos:

```text
define o projeto em C:\caminho\do\projeto
mostra a estrutura do projeto
conta linhas de codigo
busca login no projeto
le o arquivo main.py
abre main.py no editor
```

## Cofre de Snippets

Os snippets sao salvos em:

```text
data/snippets/vault.json
```

Comandos:

```text
salva snippet como decorator de retry
busca snippets de autenticacao
lista os snippets
estatisticas dos snippets
```

## Scaffolding de Projetos

O NEXUS CODER agora cria estruturas completas de projeto.

Templates embutidos:

- `fastapi`
- `react`
- `express`
- `flask`
- `cli`
- `lib`

Comandos:

```text
lista templates
cria projeto fastapi chamado minha-api
cria projeto react chamado dashboard em C:\Projetos
cria projeto express chamado backend
cria projeto lib chamado toolkit
```

Arquivo principal:

```text
coding/scaffolder.py
```

## Copiloto Local com Patch

O NEXUS CODER tambem ganhou fluxo de patch revisavel:

- monta contexto do projeto ativo;
- pede para a IA devolver JSON estruturado;
- mostra preview em formato diff;
- aplica o patch somente dentro do projeto ativo;
- cria backup dos arquivos existentes antes de sobrescrever.

Comandos:

```text
contexto do projeto
gera patch para adicionar endpoint health
preview patch
aplicar patch
roda ruff
roda pytest
```

Arquivos principais:

```text
coding/project_context.py
coding/patcher.py
coding/workspace_ai.py
```

## Assistente Operacional

O NEXUS agora tem uma camada operacional unica para texto, voz e botoes:

- `VoiceLoop` escuta em thread separada;
- `CommandRouter` mostra o que foi entendido;
- `SafetyManager` centraliza confirmacoes;
- `EditorBridge` conecta voz/botoes ao editor visual;
- a tela registra "Ouvi", "Entendi" e executa pela mesma pipeline.

Comandos de voz/texto:

```text
Nexus, abrir Chrome
Nexus, status do PC
Nexus, rode esse codigo
Nexus, salve esse arquivo como main.py
Nexus, crie um arquivo chamado app.py
Nexus, limpe o terminal
```

Arquivos principais:

```text
app/core/command_router.py
app/core/safety.py
app/voice/voice_loop.py
app/coder/editor_bridge.py
app/actions/coder_actions.py
```

## Checklist v3

- [x] Estrutura operacional integrada ao projeto atual.
- [x] `main.py`, `install.bat`, `run.bat` e `.env.example`.
- [x] `load_settings()` compativel em `app/config.py`.
- [x] Testes de roteamento em `tests/test_router.py`.
- [x] Exemplo Tkinter em `examples/ui_integration_tkinter.py`.
- [x] Botao Voz ON/OFF.
- [x] EditorBridge integrado na aba Coder.
- [x] Logs em `data/logs/nexus.log`.
- [x] Base de plugins em `app/plugins`.

## Memoria Obsidian

O NEXUS foi conectado ao Obsidian como memoria de longo prazo.

Vault configurado:

```text
C:\Users\nicol\OneDrive\Apps\cerebro-nexus\nexus
```

Fluxo:

1. O usuario pergunta algo.
2. O NEXUS procura primeiro nas notas Markdown do Obsidian.
3. Se encontrar informacao, usa a memoria local como prioridade.
4. Se nao encontrar, chama a IA.
5. Depois registra a resposta nova em Markdown.

Pasta de registros:

```text
NEXUS/Memory Inbox
```

Comandos:

```text
obsidian status
busca no obsidian minha informacao
salva no obsidian lembrar que ...
conecta obsidian em C:\caminho\do\vault
```

Arquivo principal:

```text
app/obsidian_memory.py
```

## Arquivos Importantes

```text
theme.py
ui/desktop_app.py
ui/widgets.py
ui/theme.py
ui_coding/coder_panel.py
app/assistant.py
app/settings_manager.py
app/obsidian_memory.py
app/memory.py
coding/dispatcher.py
coding/intent_coding.py
requirements.txt
README.md
```

## Estado Atual

- Interface com abas funcionando.
- Coder integrado ao roteador do NEXUS.
- Sons e animacoes configuraveis.
- Memoria Obsidian conectada.
- Vault detectado com notas Markdown.
- Respostas novas podem ser registradas automaticamente no Obsidian.
