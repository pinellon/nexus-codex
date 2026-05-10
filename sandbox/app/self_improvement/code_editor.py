import os
import shutil

class CodeEditor:
    """Aplica mudanças nos arquivos com segurança"""
    
    def write_file(self, path: str, content: str) -> bool:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Erro ao escrever {path}: {e}")
            return False
    
    def delete_file(self, path: str) -> bool:
        try:
            os.remove(path)
            return True
        except:
            return False
    
    def delete_folder(self, path: str) -> bool:
        try:
            shutil.rmtree(path)
            return True
        except:
            return False
    
    def create_folder(self, path: str) -> bool:
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except:
            return False
