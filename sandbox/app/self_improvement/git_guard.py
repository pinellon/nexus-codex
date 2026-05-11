import subprocess
from datetime import datetime

class GitGuard:
    """Garante backup antes de qualquer mudança"""
    
    def commit_before_change(self, reason: str) -> bool:
        try:
            subprocess.run(["git", "add", "-A"], check=True)
            msg = f"[NEXUS-AUTO] {datetime.now().strftime('%H:%M')} - {reason}"
            subprocess.run(["git", "commit", "-m", msg], check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    def rollback(self) -> bool:
        """Volta ao último commit se algo quebrar"""
        try:
            subprocess.run(["git", "reset", "--hard", "HEAD~1"], check=True)
            return True
        except:
            return False
