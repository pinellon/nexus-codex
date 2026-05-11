import os
import shutil
import subprocess

class SandboxManager:
    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        self.sandbox_dir = os.path.join(self.root_dir, "sandbox")
        
    def create_sandbox(self):
        """Cria um clone do projeto para o diretório sandbox."""
        if os.path.exists(self.sandbox_dir):
            shutil.rmtree(self.sandbox_dir)
            
        os.makedirs(self.sandbox_dir, exist_ok=True)
        
        # Copia todos os arquivos, exceto pastas de ambiente virtual, .git e sandbox
        for item in os.listdir(self.root_dir):
            if item in ['.git', 'venv', 'env', '__pycache__', 'sandbox', '.pytest_cache', 'data', 'logs']:
                continue
            
            s = os.path.join(self.root_dir, item)
            d = os.path.join(self.sandbox_dir, item)
            
            if os.path.isdir(s):
                shutil.copytree(s, d)
            else:
                shutil.copy2(s, d)
                
        return self.sandbox_dir
        
    def validate_sandbox(self) -> bool:
        """Executa os testes no sandbox para validar as mudanças."""
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-q", "--tb=no"],
            cwd=self.sandbox_dir,
            capture_output=True, text=True
        )
        return result.returncode == 0
        
    def apply_to_live(self):
        """Move as alterações do sandbox para o sistema real."""
        # Para um ambiente real, seria mais seguro usar git para copiar apenas arquivos modificados,
        # ou shutil para mover do sandbox de volta para a raiz.
        for item in os.listdir(self.sandbox_dir):
            if item in ['__pycache__', 'data', 'logs']:
                continue
                
            s = os.path.join(self.sandbox_dir, item)
            d = os.path.join(self.root_dir, item)
            
            try:
                if os.path.isdir(s):
                    if os.path.exists(d):
                        shutil.rmtree(d, ignore_errors=True)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
            except Exception as e:
                print(f"Erro ao mover do sandbox para live: {e}")
                
    def discard_sandbox(self):
        """Descarta o sandbox atual."""
        if os.path.exists(self.sandbox_dir):
            shutil.rmtree(self.sandbox_dir)
