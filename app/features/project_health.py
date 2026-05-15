"""Diagnostico simples de saude do projeto NEXUS.

Analisa arquivos basicos, dependencias e riscos comuns para mostrar um resumo
rapido dentro da UI ou pelo comando de voz "diagnostico do projeto".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class HealthReport:
    score: int
    status: str
    found: list[str] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def as_text(self) -> str:
        lines = [f"Saude do projeto: {self.score}/100 - {self.status}"]
        if self.found:
            lines.append("Encontrado:")
            lines.extend(f"- {item}" for item in self.found)
        if self.missing:
            lines.append("Faltando:")
            lines.extend(f"- {item}" for item in self.missing)
        if self.warnings:
            lines.append("Avisos:")
            lines.extend(f"- {item}" for item in self.warnings)
        return "\n".join(lines)


IMPORTANT_PATHS = [
    "README.md",
    "requirements.txt",
    "main.py",
    "app/web/server.py",
    "frontend/package.json",
    "frontend/src/App.tsx",
    "app/settings_manager.py",
    "app/core/command_router.py",
    "app/core/safety.py",
    "app/voice/voice_loop.py",
    "app/coder/editor_bridge.py",
]


def analyze_project(root: str | Path = ".") -> HealthReport:
    root = Path(root)
    found: list[str] = []
    missing: list[str] = []
    warnings: list[str] = []

    for relative in IMPORTANT_PATHS:
        path = root / relative
        if path.exists():
            found.append(relative)
        else:
            missing.append(relative)

    env_file = root / ".env"
    gitignore = root / ".gitignore"
    if env_file.exists():
        warnings.append("Arquivo .env existe. Confirme que ele nao foi commitado com chaves reais.")
    if gitignore.exists():
        content = gitignore.read_text(encoding="utf-8", errors="ignore")
        if ".env" not in content:
            warnings.append(".gitignore nao parece bloquear .env.")
    else:
        warnings.append(".gitignore nao encontrado.")

    requirements = root / "requirements.txt"
    if requirements.exists():
        req_text = requirements.read_text(encoding="utf-8", errors="ignore").lower()
        for package in ["speechrecognition", "psutil", "pyautogui", "fastapi"]:
            if package not in req_text:
                warnings.append(f"Dependencia possivelmente ausente: {package}")

    desktop_file = root / "ui" / "desktop_app.py"
    if desktop_file.exists():
        found.append("ui/desktop_app.py (legado)")

    base = len(IMPORTANT_PATHS)
    score = int((len(found) / base) * 80) if base else 80
    score -= min(len(warnings) * 4, 25)
    score = max(0, min(100, score + 20))

    if score >= 85:
        status = "forte"
    elif score >= 65:
        status = "bom, mas pode melhorar"
    elif score >= 40:
        status = "incompleto"
    else:
        status = "critico"

    return HealthReport(score=score, status=status, found=found, missing=missing, warnings=warnings)
