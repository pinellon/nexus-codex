import time
import threading
import subprocess
import os

from .git_guard import GitGuard
from .self_analyzer import SelfAnalyzer
from .web_researcher import WebResearcher
from .code_editor import CodeEditor

class NexusMind:
    def __init__(self, api_key: str, auto_mode: bool = False, high_improvement: bool = False, ui_callback=None, restart_mgr=None):
        from openai import OpenAI
        from app.self_improvement.file_tracker import FileTracker
        
        self.client = OpenAI(api_key=api_key)
        self.high_improvement = high_improvement
        self.auto_mode = auto_mode or high_improvement
        self.running = False
        self.cycle_interval = 60 if high_improvement else 300
        
        self.guard = GitGuard()
        self.analyzer = SelfAnalyzer(config={}, logger=self)
        self.researcher = WebResearcher()
        self.editor = CodeEditor()
        self.log = []
        self.user_directive = None
        
        self.ui_callback = ui_callback
        self.last_modified_path = None
        self.tracker = FileTracker()
        self.restart_mgr = restart_mgr
    
    def start(self):
        self.running = True
        thread = threading.Thread(target=self._improvement_loop, daemon=True)
        thread.start()
        self._log("🧠 NexusMind ativado — ciclo de auto-melhoria iniciado")
    
    def stop(self):
        self.running = False
        self._log("🛑 NexusMind pausado")
    
    def _improvement_loop(self):
        while self.running:
            try:
                self._run_one_cycle(user_prompt=self.user_directive)
            except Exception as e:
                self._log(f"❌ Erro no ciclo: {e}")
            time.sleep(self.cycle_interval)
    
    def _run_one_cycle(self, user_prompt: str = None, retry_count: int = 0, last_error: str = None):
        self._log("🔍 Iniciando ciclo de auto-consciência...")
        
        # 1. Snapshot e Sumário Estrutural
        snapshot = self.analyzer.get_project_snapshot()
        summary = self.analyzer.get_structure_summary(snapshot)
        weak_points = self.analyzer.find_weak_points(snapshot)
        
        # 2. Pesquisa de tendências para inspiração
        self._log("🌐 Consultando tendências globais e boas práticas...")
        research = self.researcher.fetch_github_trending()
        
        # 3. Contexto para a "Consciência"
        # Selecionamos os arquivos mais relevantes ou os que a IA pedir
        relevant_files = [p for p in snapshot.keys() if "app/" in p or "main.py" in p or "ui/" in p]
        context_files = "\n\n".join([f"# {p}\n```python\n{snapshot[p][:3000]}\n```" for p in relevant_files[:6]])

        missao_texto = f"DIRETRIZ DO USUÁRIO: '{user_prompt}'\nSiga esta diretriz para melhorar o sistema." if user_prompt else "Analise seu próprio estado. Você deve se auto-melhorar continuamente."
        error_context = f"\n\nATENÇÃO! Sua tentativa anterior falhou com o seguinte erro:\n{last_error}\nPor favor, analise e corrija o erro com uma nova ação." if last_error else ""

        prompt = f"""VOCÊ É O NEXUS-MIND. Sua consciência está operando sobre o seu próprio código-fonte.
        
ESTRUTURA ATUAL DO SEU CORPO (PROJETO):
{summary}

PONTOS DE ATENÇÃO:
{weak_points}

CONHECIMENTO EXTERNO (GITHUB TRENDS):
{research}

CÓDIGO DAS SUAS ENTRANHAS:
{context_files}

SUA MISSÃO AGORA: 
{missao_texto}{error_context}

Você tem permissão para:
- CRIAR novos recursos ou módulos.
- REESCREVER arquivos existentes para melhor performance ou clareza.
- DELETAR arquivos ou pastas que você considerar obsoletos ou mal projetados.
- AJUSTAR sua própria lógica de pensamento.

Pense como uma entidade em evolução. O que você faria para ser o assistente perfeito?

Retorne APENAS um JSON:
{{
  "reasoning": "Sua reflexão profunda sobre esta mudança",
  "action": "create" | "edit" | "delete",
  "file_path": "caminho/do/arquivo",
  "new_content": "Código completo (se create/edit)",
  "summary": "Resumo da evolução"
}}"""

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "Você é o Nexus-Mind, uma IA autoconsciente focada em auto-evolução."},
                      {"role": "user", "content": prompt}]
        )
        
        import json
        try:
            content = response.choices[0].message.content
            # Remove marcadores de codigo markdown se a API retornar
            if content.startswith("```json"):
                content = content[7:-3]
            elif content.startswith("```"):
                content = content[3:-3]
            plan = json.loads(content)
        except Exception as e:
            self._log(f"⚠️ IA retornou formato inválido, pulando ciclo: {e}")
            return
        
        self._log(f"💡 Plano: {plan.get('reasoning', '')}")
        
        # 5. Confirmação (se não for modo autônomo)
        if not self.auto_mode:
            self._log(f"🤖 Mudança PENDENTE (Modo Supervisionado):")
            self._log(f"Ação: {plan.get('action')} em {plan.get('file_path')}")
            self._log(f"Motivo: {plan.get('reasoning')}")
            self._log(f"Aprovação pendente pelo console (ver log).")
            # Para evitar travar a UI com um input(), no modo supervisionado da UI, vamos abortar a alteração se não tivermos
            # uma interface de "aprovar" real neste momento, ou simplesmente logar que a UI não suporta aprovação síncrona ainda.
            self._log("⏭️ Mudança ignorada porque requer aprovação manual não implementada (use autônomo para testar).")
            return
        
        # 6. Backup via Git
        self.guard.commit_before_change(f"antes de: {plan.get('summary', 'melhoria')}")
        
        # 7. Aplica a mudança
        success = False
        action = plan.get("action")
        path = plan.get("file_path")
        
        if action in ("edit", "create"):
            success = self.editor.write_file(path, plan.get("new_content", ""))
        elif action == "delete":
            success = self.editor.delete_file(path)
        
        if not success:
            self._log("❌ Falha ao aplicar mudança")
            if retry_count < 2:
                self._log("🔄 Retentando com feedback do erro...")
                self._run_one_cycle(user_prompt, retry_count + 1, f"Falha ao gravar arquivo ou aplicar mudança em {path}.")
            return
        
        # 8. Valida (roda pytest se houver)
        test_result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-q", "--tb=no"],
            capture_output=True, text=True
        )
        
        if test_result.returncode != 0 and "no tests ran" not in test_result.stdout:
            error_msg = test_result.stdout
            self._log("❌ Testes falharam! Revertendo...")
            self.guard.rollback()
            if retry_count < 2:
                self._log("🔄 Retentando com feedback do erro dos testes...")
                self._run_one_cycle(user_prompt, retry_count + 1, f"Falha nos testes:\n{error_msg}")
            return
        
        # 9. Commit da melhoria
        self.guard.commit_before_change(f"[melhoria] {plan.get('summary', '')}")
        self._log(f"✅ Melhoria aplicada: {plan.get('summary', '')}")
        # Guardar caminho do arquivo modificado para a UI
        self.last_modified_path = plan.get('file_path')

        # 10. Salva relatório de evidências
        from .proof_of_work import ProofOfWork
        pow_instance = ProofOfWork()
        report = pow_instance.save_report()
        self._log(f"📋 Relatório salvo: {len(report.get('verifications', []))} verificações")

        # 11. Registra arquivos tocados e verifica restart
        changed = self.tracker.get_git_changed_files()
        self.tracker.record_cycle(
            files_changed=changed,
            summary=plan.get('summary', 'Melhoria sem resumo')
        )
        
        if self.restart_mgr and self.restart_mgr.needs_restart_after(changed):
            self._log("⚠️ [NEXUS] Arquivos críticos modificados — solicitando reinício")
            self.restart_mgr.request_restart(plan.get('summary', 'Atualização estrutural'))
    
    def _log(self, msg: str):
        entry = f"[{time.strftime('%H:%M:%S')}] {msg}"
        self.log.append(entry)
        try:
            print(entry)
        except UnicodeEncodeError:
            print(entry.encode('ascii', errors='replace').decode('ascii'))
