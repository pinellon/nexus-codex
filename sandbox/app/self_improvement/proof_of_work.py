import subprocess
import os
import json
import ast
from datetime import datetime

class ProofOfWork:
    """Coleta evidências reais do que o NexusMind fez"""

    def get_git_log(self, n=20) -> list:
        """Pega os últimos N commits do Git com detalhes reais"""
        try:
            result = subprocess.run(
                ["git", "log", f"-{n}",
                 "--pretty=format:%H|%s|%ai|%an",
                 "--shortstat"],
                capture_output=True, text=True
            )
            commits = []
            for line in result.stdout.strip().split("\n"):
                if "|" in line:
                    h, msg, date, author = line.split("|", 3)
                    commits.append({
                        "hash": h[:7],
                        "full_hash": h,
                        "msg": msg,
                        "date": date[:16],
                        "author": author,
                        "is_nexus": "[NEXUS-AUTO]" in msg
                    })
            return commits
        except Exception as e:
            return [{"error": str(e)}]

    def get_diff(self, commit_hash: str) -> str:
        """Pega o diff real de um commit"""
        try:
            result = subprocess.run(
                ["git", "show", "--stat", "--patch", commit_hash],
                capture_output=True, text=True
            )
            return result.stdout
        except Exception as e:
            return f"Erro ao buscar diff: {e}"

    def get_changed_files(self, commit_hash: str) -> list:
        """Lista arquivos que foram realmente modificados"""
        try:
            result = subprocess.run(
                ["git", "show", "--name-status", commit_hash],
                capture_output=True, text=True
            )
            files = []
            for line in result.stdout.split("\n"):
                if line and line[0] in ("M", "A", "D"):
                    status, *path = line.split("\t")
                    files.append({
                        "status": {"M": "edit", "A": "create", "D": "delete"}[status],
                        "path": "\t".join(path)
                    })
            return files
        except Exception as e:
            return []

    def verify_last_change(self) -> list:
        """Roda checklist de verificação após uma mudança"""
        checks = []

        # 1. Git funcionando?
        try:
            r = subprocess.run(["git", "status"], capture_output=True, text=True)
            checks.append({"status": "ok", "label": "git status ok", "detail": "repositório limpo"})
        except:
            checks.append({"status": "fail", "label": "git status", "detail": "git não encontrado"})

        # 2. Sintaxe Python válida nos arquivos .py modificados
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
            capture_output=True, text=True
        )
        py_files = [f for f in result.stdout.strip().split("\n") if f.endswith(".py")]
        syntax_ok = True
        for f in py_files:
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    ast.parse(fp.read())
            except SyntaxError as e:
                syntax_ok = False
                checks.append({"status": "fail", "label": f"sintaxe: {f}", "detail": str(e)})
        if syntax_ok and py_files:
            checks.append({"status": "ok", "label": "sintaxe Python válida", "detail": f"{len(py_files)} arquivo(s) verificados"})

        # 3. Testes
        test_result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-q", "--tb=no"],
            capture_output=True, text=True
        )
        if "passed" in test_result.stdout:
            checks.append({"status": "ok", "label": "testes unitários", "detail": test_result.stdout.strip().split("\n")[-1]})
        elif "no tests ran" in test_result.stdout:
            checks.append({"status": "warn", "label": "testes unitários", "detail": "nenhum teste encontrado"})
        else:
            checks.append({"status": "fail", "label": "testes unitários", "detail": "falhas detectadas"})

        # 4. .env intocado
        try:
            env_result = subprocess.run(
                ["git", "diff", "HEAD~1", "HEAD", "--", ".env"],
                capture_output=True, text=True
            )
            if not env_result.stdout.strip():
                checks.append({"status": "ok", "label": ".env intocado", "detail": "arquivo protegido"})
            else:
                checks.append({"status": "fail", "label": ".env foi modificado!", "detail": "ALERTA — revisar imediatamente"})
        except:
            checks.append({"status": "skip", "label": ".env", "detail": "não verificado"})

        # 5. Import funciona?
        import_result = subprocess.run(
            ["python", "-c", "import app"],
            capture_output=True, text=True
        )
        if import_result.returncode == 0:
            checks.append({"status": "ok", "label": "import app funcionando", "detail": "sem erros de importação"})
        else:
            checks.append({"status": "fail", "label": "import app quebrado", "detail": import_result.stderr[:80]})

        return checks

    def save_report(self, path="data/nexus_proof.json"):
        """Salva relatório completo em JSON pra UI ler"""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        report = {
            "generated_at": datetime.now().isoformat(),
            "commits": self.get_git_log(10),
            "verifications": self.verify_last_change(),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        return report
