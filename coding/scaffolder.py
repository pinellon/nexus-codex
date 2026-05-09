"""Scaffolding de projetos para o NEXUS CODER."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from string import Template

try:
    from app.logger import log_action
except ImportError:
    def log_action(text: str):  # type: ignore[override]
        print(text)

try:
    from coding.code_assistant import _call_ai
except ImportError:
    def _call_ai(prompt: str, **_kwargs) -> str:  # type: ignore[override]
        return ""


@dataclass
class ScaffoldResult:
    success: bool
    message: str
    path: str = ""

    def __str__(self) -> str:
        return self.message


SUPPORTED_TEMPLATES = {
    "fastapi": "FastAPI API com SQLAlchemy, testes e CORS",
    "react": "React + Vite + TypeScript",
    "vite": "React + Vite + TypeScript",
    "express": "Node.js + Express API",
    "node": "Node.js + Express API",
    "flask": "Flask API simples com blueprints e testes",
    "cli": "CLI Python com argparse e testes",
    "python-cli": "CLI Python com argparse e testes",
    "lib": "Biblioteca Python com pyproject, src layout e pytest",
    "lib-python": "Biblioteca Python com pyproject, src layout e pytest",
}


def listar_templates() -> str:
    lines = ["Templates disponiveis no NEXUS CODER:", ""]
    seen: set[str] = set()
    for key, description in SUPPORTED_TEMPLATES.items():
        if description in seen:
            continue
        seen.add(description)
        canonical = _normalize_template(key)
        lines.append(f"- {canonical}: {description}")
    lines.extend([
        "",
        "Exemplos:",
        "- cria projeto fastapi chamado minha-api",
        "- cria projeto react chamado dashboard em C:\\Projetos",
        "- cria projeto lib chamado toolkit",
    ])
    return "\n".join(lines)


def criar_projeto(nome: str, template: str, destino: str = "", init_git: bool = True) -> ScaffoldResult:
    project_name = _sanitize_project_name(nome)
    template_name = _normalize_template(template)
    if not project_name:
        return ScaffoldResult(False, "Informe o nome do projeto.")
    if template_name not in _template_builders():
        return _scaffold_com_ia(project_name, template, destino, init_git)

    base_dir = _resolve_base_dir(destino)
    project_dir = base_dir / project_name
    validation_error = _validate_project_dir(project_dir, base_dir)
    if validation_error:
        return ScaffoldResult(False, validation_error)

    files = _template_builders()[template_name](project_name)
    context = _render_context(project_name, template_name, project_dir)

    created: list[str] = []
    try:
        project_dir.mkdir(parents=True, exist_ok=False)
        for rel_path, content in files.items():
            rendered_rel_path = _render(rel_path, context).replace("\\", "/")
            relative_target = Path(rendered_rel_path)
            if relative_target.is_absolute() or ".." in relative_target.parts:
                return ScaffoldResult(False, f"Caminho invalido no template: {rel_path}")
            target = project_dir / rendered_rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(_render(content, context), encoding="utf-8")
            created.append(rendered_rel_path)

        if ".gitignore" not in files:
            project_type = "node" if template_name in {"react", "express", "nextjs"} else "python"
            (project_dir / ".gitignore").write_text(_gitignore(project_type), encoding="utf-8")
            created.append(".gitignore")

        if init_git:
            _git_init(project_dir)
    except Exception as error:
        return ScaffoldResult(False, f"Nao consegui criar o projeto: {error}")

    log_action(f"Scaffold criado: {project_name} ({template_name}) em {project_dir}")
    return ScaffoldResult(
        True,
        "\n".join([
            f"Projeto '{project_name}' criado.",
            f"Template: {template_name}",
            f"Local: {project_dir}",
            f"Arquivos: {len(created)}",
            "",
            _next_steps(template_name, context),
        ]).strip(),
        str(project_dir),
    )


def _template_builders():
    return {
        "fastapi": _fastapi_files,
        "react": _react_files,
        "express": _express_files,
        "flask": _flask_files,
        "cli": _cli_files,
        "lib": _library_files,
    }


def _normalize_template(template: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", (template or "").lower()).strip("-")
    aliases = {
        "vite": "react",
        "react-vite": "react",
        "react-ts": "react",
        "node": "express",
        "nodejs": "express",
        "node-express": "express",
        "python-cli": "cli",
        "argparse": "cli",
        "biblioteca": "lib",
        "library": "lib",
        "lib-python": "lib",
    }
    return aliases.get(value, value)


def _sanitize_project_name(name: str) -> str:
    cleaned = (name or "").strip().strip("'\"")
    cleaned = re.sub(r"\s+(?:em|na pasta|no diretorio|no diretório)\s+.+$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"[<>:\"|?*]", "-", cleaned)
    cleaned = re.sub(r"\s+", "-", cleaned)
    cleaned = re.sub(r"-{2,}", "-", cleaned).strip(".- ")
    return cleaned[:80]


def _slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "nexus-project"


def _module_name(name: str) -> str:
    module = re.sub(r"[^a-zA-Z0-9_]+", "_", name.lower()).strip("_")
    if not module or module[0].isdigit():
        module = f"app_{module}"
    return module


def _resolve_base_dir(destino: str) -> Path:
    if destino:
        return Path(destino).expanduser().resolve()
    desktop = Path.home() / "Desktop"
    return desktop if desktop.exists() else Path.home()


def _validate_project_dir(project_dir: Path, base_dir: Path) -> str:
    try:
        base_dir.mkdir(parents=True, exist_ok=True)
    except Exception as error:
        return f"Nao consegui acessar o destino: {error}"
    if project_dir.exists():
        return f"A pasta ja existe: {project_dir}"
    if project_dir.anchor == project_dir.as_posix():
        return "Destino invalido."
    return ""


def _render_context(name: str, template: str, project_dir: Path) -> dict[str, str]:
    module = _module_name(name)
    return {
        "name": name,
        "slug": _slug(name),
        "module": module,
        "class_name": "".join(part.capitalize() for part in module.split("_")) or "NexusProject",
        "template": template,
        "date": datetime.now().strftime("%d/%m/%Y"),
        "year": str(datetime.now().year),
        "project_dir": str(project_dir),
    }


def _render(content: str, context: dict[str, str]) -> str:
    return Template(content).safe_substitute(context)


def _gitignore(kind: str) -> str:
    base = "\n".join([
        "# NEXUS CODER",
        ".env",
        ".env.local",
        ".DS_Store",
        "Thumbs.db",
        "",
    ])
    if kind == "node":
        return base + "\n".join(["node_modules/", "dist/", "build/", "coverage/", ".next/", "npm-debug.log*", ""])
    return base + "\n".join(["__pycache__/", "*.py[cod]", ".venv/", "venv/", "dist/", "build/", "*.egg-info/", ".pytest_cache/", ".mypy_cache/", ""])


def _git_init(project_dir: Path):
    try:
        subprocess.run(["git", "init"], cwd=str(project_dir), capture_output=True, text=True, timeout=10)
    except Exception:
        pass


def _next_steps(template: str, context: dict[str, str]) -> str:
    steps = {
        "fastapi": "Proximos passos:\ncd <projeto>\npython -m venv .venv\npip install -r requirements.txt\nuvicorn main:app --reload",
        "react": "Proximos passos:\ncd <projeto>\nnpm install\nnpm run dev",
        "express": "Proximos passos:\ncd <projeto>\nnpm install\nnpm run dev",
        "flask": "Proximos passos:\ncd <projeto>\npython -m venv .venv\npip install -r requirements.txt\npython app.py",
        "cli": "Proximos passos:\ncd <projeto>\npython -m venv .venv\npip install -e .[dev]\npython -m $module --help",
        "lib": "Proximos passos:\ncd <projeto>\npython -m venv .venv\npip install -e .[dev]\npytest",
    }
    return _render(steps.get(template, ""), context)


def _readme(stack: str, run_cmd: str) -> str:
    return """# $name

Gerado com NEXUS CODER em $date.

## Stack

$stack

## Rodar

```bash
$run_cmd
```

## Estrutura

O projeto ja vem com configuracao base, exemplo funcional, ambiente `.env.example`,
testes iniciais e `.gitignore`.
""".replace("$stack", stack).replace("$run_cmd", run_cmd)


def _fastapi_files(name: str) -> dict[str, str]:
    return {
        "requirements.txt": "fastapi>=0.110.0\nuvicorn[standard]>=0.29.0\npython-dotenv>=1.0.0\npydantic>=2.0.0\nsqlalchemy>=2.0.0\npytest>=8.0.0\nhttpx>=0.27.0\n",
        ".env.example": "APP_NAME=$name\nDEBUG=true\nDATABASE_URL=sqlite:///./db.sqlite3\nALLOWED_ORIGINS=http://localhost:3000\n",
        ".gitignore": _gitignore("python"),
        "README.md": _readme("Python, FastAPI, SQLAlchemy, Pytest", "pip install -r requirements.txt\nuvicorn main:app --reload"),
        "main.py": '''"""API $name gerada pelo NEXUS CODER."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI(title=os.getenv("APP_NAME", "$name"), version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "ok", "app": os.getenv("APP_NAME", "$name")}


@app.get("/health")
async def health():
    return {"status": "healthy"}
''',
        "app/__init__.py": "",
        "app/database.py": '''from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
import os


class Base(DeclarativeBase):
    pass


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./db.sqlite3")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
''',
        "app/routers/__init__.py": "",
        "tests/test_main.py": '''from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
''',
    }


def _react_files(name: str) -> dict[str, str]:
    return {
        "package.json": '''{
  "name": "$slug",
  "private": true,
  "version": "0.1.0",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "lucide-react": "^0.468.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.2.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "typescript": "^5.4.0",
    "vite": "^5.2.0",
    "vitest": "^1.6.0"
  }
}
''',
        ".gitignore": _gitignore("node"),
        "README.md": _readme("React 18, Vite, TypeScript", "npm install\nnpm run dev"),
        "index.html": '''<!doctype html>
<html lang="pt-BR">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>$name</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
''',
        "tsconfig.json": '''{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": ["src"]
}
''',
        "vite.config.ts": '''import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: { port: 3000 },
});
''',
        "src/main.tsx": '''import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
''',
        "src/App.tsx": '''import { Code2 } from "lucide-react";

export default function App() {
  return (
    <main className="shell">
      <section className="panel">
        <Code2 size={34} />
        <h1>$name</h1>
        <p>Projeto React gerado com NEXUS CODER.</p>
      </section>
    </main>
  );
}
''',
        "src/styles.css": '''* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: Inter, system-ui, sans-serif;
  background: #071014;
  color: #e8fbff;
}

.shell {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px;
}

.panel {
  width: min(560px, 100%);
  border: 1px solid #164b5a;
  border-radius: 8px;
  background: #0c1c22;
  padding: 32px;
}

h1 {
  margin: 16px 0 8px;
  color: #38e8ff;
}
''',
    }


def _express_files(name: str) -> dict[str, str]:
    return {
        "package.json": '''{
  "name": "$slug",
  "version": "0.1.0",
  "main": "src/index.js",
  "scripts": {
    "start": "node src/index.js",
    "dev": "nodemon src/index.js",
    "test": "jest --runInBand"
  },
  "dependencies": {
    "cors": "^2.8.5",
    "dotenv": "^16.4.0",
    "express": "^4.19.0",
    "helmet": "^7.1.0",
    "morgan": "^1.10.0"
  },
  "devDependencies": {
    "jest": "^29.7.0",
    "nodemon": "^3.1.0",
    "supertest": "^7.0.0"
  }
}
''',
        ".env.example": "PORT=3000\nNODE_ENV=development\n",
        ".gitignore": _gitignore("node"),
        "README.md": _readme("Node.js, Express, Jest, Supertest", "npm install\nnpm run dev"),
        "src/app.js": '''const cors = require("cors");
const express = require("express");
const helmet = require("helmet");
const morgan = require("morgan");

const app = express();

app.use(helmet());
app.use(cors());
app.use(morgan("dev"));
app.use(express.json());

app.get("/", (_req, res) => res.json({ status: "ok", app: "$name" }));
app.get("/health", (_req, res) => res.json({ status: "healthy" }));

app.use((err, _req, res, _next) => {
  console.error(err);
  res.status(500).json({ error: "Internal Server Error" });
});

module.exports = app;
''',
        "src/index.js": '''require("dotenv").config();
const app = require("./app");

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`$name rodando em http://localhost:${port}`);
});
''',
        "tests/app.test.js": '''const request = require("supertest");
const app = require("../src/app");

describe("health", () => {
  it("responde status ok", async () => {
    const response = await request(app).get("/");
    expect(response.statusCode).toBe(200);
    expect(response.body.status).toBe("ok");
  });
});
''',
    }


def _flask_files(name: str) -> dict[str, str]:
    return {
        "requirements.txt": "flask>=3.0.0\npython-dotenv>=1.0.0\npytest>=8.0.0\n",
        ".env.example": "FLASK_ENV=development\nSECRET_KEY=change-me\n",
        ".gitignore": _gitignore("python"),
        "README.md": _readme("Python, Flask, Pytest", "pip install -r requirements.txt\npython app.py"),
        "app.py": '''from $module import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
''',
        "$module/__init__.py": '''from flask import Flask


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def root():
        return {"status": "ok", "app": "$name"}

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    return app
''',
        "tests/test_app.py": '''from $module import create_app


def test_root():
    client = create_app().test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert response.json["status"] == "ok"
''',
    }


def _cli_files(name: str) -> dict[str, str]:
    return {
        "pyproject.toml": '''[project]
name = "$slug"
version = "0.1.0"
description = "CLI gerada com NEXUS CODER"
requires-python = ">=3.10"

[project.optional-dependencies]
dev = ["pytest>=8.0.0"]

[project.scripts]
$slug = "$module.__main__:main"

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
''',
        ".gitignore": _gitignore("python"),
        "README.md": _readme("Python, argparse, pytest", "pip install -e .[dev]\n$slug --help"),
        "$module/__init__.py": '''__version__ = "0.1.0"
''',
        "$module/__main__.py": '''import argparse


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="$slug", description="$name")
    parser.add_argument("name", nargs="?", default="Nicolas", help="Nome para saudacao")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    print(f"Ola, {args.name}. $name esta pronto.")


if __name__ == "__main__":
    main()
''',
        "tests/test_cli.py": '''from $module.__main__ import build_parser


def test_parser_default_name():
    args = build_parser().parse_args([])
    assert args.name == "Nicolas"
''',
    }


def _library_files(name: str) -> dict[str, str]:
    return {
        "pyproject.toml": '''[project]
name = "$slug"
version = "0.1.0"
description = "Biblioteca Python gerada com NEXUS CODER"
readme = "README.md"
requires-python = ">=3.10"

[project.optional-dependencies]
dev = ["pytest>=8.0.0", "ruff>=0.6.0"]

[tool.ruff]
line-length = 100

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
''',
        ".gitignore": _gitignore("python"),
        "README.md": _readme("Python package, src layout, pytest, ruff", "pip install -e .[dev]\npytest"),
        "src/$module/__init__.py": '''from .core import greet

__all__ = ["greet"]
__version__ = "0.1.0"
''',
        "src/$module/core.py": '''def greet(name: str) -> str:
    """Retorna uma saudacao simples."""
    cleaned = name.strip() or "mundo"
    return f"Ola, {cleaned}!"
''',
        "tests/test_core.py": '''from $module import greet


def test_greet():
    assert greet("Nicolas") == "Ola, Nicolas!"
''',
    }


def _scaffold_com_ia(nome: str, template: str, destino: str, init_git: bool) -> ScaffoldResult:
    base_dir = _resolve_base_dir(destino)
    project_dir = base_dir / nome
    validation_error = _validate_project_dir(project_dir, base_dir)
    if validation_error:
        return ScaffoldResult(False, validation_error)

    prompt = f"""Gere uma estrutura pequena e funcional de projeto {template} chamado {nome}.

Use este formato exato para cada arquivo:
===FILE: caminho/arquivo.ext===
conteudo completo
===END===

Inclua README.md, .gitignore, arquivo de ambiente de exemplo e no maximo 10 arquivos."""
    answer = _call_ai(prompt, max_tokens=3000)
    files = re.findall(r"===FILE:\s*(.+?)===\s*\n(.*?)\n===END===", answer, re.DOTALL)
    if not files:
        return ScaffoldResult(False, f"Template '{template}' nao esta embutido e a IA nao gerou arquivos validos.")

    try:
        project_dir.mkdir(parents=True, exist_ok=False)
        for rel_path, content in files:
            relative_target = Path(rel_path.strip().replace("\\", "/"))
            if relative_target.is_absolute() or ".." in relative_target.parts:
                continue
            target = project_dir / relative_target
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content.strip() + "\n", encoding="utf-8")
        if init_git:
            _git_init(project_dir)
    except Exception as error:
        return ScaffoldResult(False, f"Nao consegui criar o projeto: {error}")

    return ScaffoldResult(True, f"Projeto '{nome}' criado com IA em {project_dir}.", str(project_dir))
