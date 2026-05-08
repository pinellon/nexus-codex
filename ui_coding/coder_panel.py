"""Aba visual do NEXUS CODER."""

from __future__ import annotations

import datetime
import re
import threading
import tkinter as tk
from tkinter import filedialog

import customtkinter as ctk

from ui.theme import BTN, C, F
from ui.widgets import AmbientScanner, SoundBus, bind_button_fx, show_toast


class CoderPanel(tk.Frame):
    """Painel com editor, output, acoes rapidas e comando de programacao."""

    def __init__(self, parent, on_command=None, **kwargs):
        super().__init__(parent, bg=C["bg"], **kwargs)
        self._on_command = on_command
        self._linguagem_var = tk.StringVar(value="python")
        self._projeto_var = tk.StringVar(value="(nenhum projeto)")
        self._filename_var = tk.StringVar(value="main.py")
        self._build()

    def _build(self):
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=0)
        self.rowconfigure(0, weight=2)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=0)
        self._build_editor()
        self._build_output()
        self._build_sidebar()
        self._build_command_bar()

    def _build_editor(self):
        frame = tk.Frame(self, bg=C["panel"])
        frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=(10, 4))
        hdr = tk.Frame(frame, bg=C["card"])
        hdr.pack(fill="x")
        scan = AmbientScanner(hdr, height=34, bg=C["card"])
        scan.place(x=0, y=0, relwidth=1, relheight=1)
        scan.start()
        tk.Label(hdr, text="EDITOR", bg=C["card"], fg=C["cyan"], font=F["small"]).pack(side="left", padx=10, pady=6)
        tk.Label(hdr, textvariable=self._filename_var, bg=C["card"], fg=C["text_muted"], font=F["tiny"]).pack(side="left", padx=(0, 8))
        langs = ["python", "javascript", "typescript", "html", "css", "sql", "bash", "java", "c", "cpp", "go", "rust", "php"]
        ctk.CTkOptionMenu(
            hdr,
            values=langs,
            variable=self._linguagem_var,
            width=135,
            height=26,
            fg_color=C["border"],
            button_color=C["border_hi"],
            button_hover_color=C["cyan_bg"],
            text_color=C["cyan"],
            command=self._on_lang_change,
        ).pack(side="left", padx=6)
        for text, command, color in [
            ("Rodar", self._rodar_codigo, C["green"]),
            ("Copiar", self._copiar_codigo, C["text_dim"]),
            ("Limpar", self._limpar_editor, C["error"]),
            ("Salvar", self._salvar_arquivo, C["cyan"]),
        ]:
            lbl = tk.Label(hdr, text=text, bg=C["card"], fg=color, font=F["tiny"], cursor="hand2", padx=8)
            lbl.pack(side="right", pady=6)
            lbl.bind("<Button-1>", lambda _e, c=command: c())
            lbl.bind("<Enter>", lambda _e: SoundBus.play("hover"))
        tk.Frame(frame, bg=C["border"], height=1).pack(fill="x")
        row = tk.Frame(frame, bg=C["panel"])
        row.pack(fill="both", expand=True)
        self._line_nums = tk.Text(row, width=4, bg=C["card"], fg=C["text_muted"], font=("Courier New", 12), relief="flat", bd=0, state="disabled")
        self._line_nums.pack(side="left", fill="y", padx=(4, 0))
        self._editor = tk.Text(row, bg=C["card"], fg=C["text"], insertbackground=C["cyan"], font=("Courier New", 12), relief="flat", bd=0, undo=True, tabs=("1c",), wrap="none", selectbackground=C["border_hi"])
        self._editor.pack(side="left", fill="both", expand=True, padx=4)
        sy = tk.Scrollbar(row, command=self._sync_scroll)
        sy.pack(side="right", fill="y")
        sx = tk.Scrollbar(frame, orient="horizontal", command=self._editor.xview, bg=C["border"], troughcolor=C["bg"])
        sx.pack(fill="x")
        self._editor.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        self._editor.bind("<KeyRelease>", self._update_line_nums)
        self._editor.bind("<Tab>", self._insert_tab)
        self._editor.bind("<Control-Return>", lambda _e: self._rodar_codigo())
        self._update_line_nums()

    def _build_output(self):
        frame = tk.Frame(self, bg=C["panel"])
        frame.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(0, 4))
        hdr = tk.Frame(frame, bg=C["card"])
        hdr.pack(fill="x")
        scan = AmbientScanner(hdr, height=32, bg=C["card"])
        scan.place(x=0, y=0, relwidth=1, relheight=1)
        scan.start()
        tk.Label(hdr, text="OUTPUT / NEXUS", bg=C["card"], fg=C["cyan"], font=F["small"]).pack(side="left", padx=10, pady=5)
        for text, command, color in [
            ("Copiar", self._copiar_output, C["text_dim"]),
            ("Limpar", self._limpar_output, C["error"]),
            ("-> Editor", self._output_para_editor, C["green"]),
        ]:
            lbl = tk.Label(hdr, text=text, bg=C["card"], fg=color, font=F["tiny"], cursor="hand2", padx=8)
            lbl.pack(side="right", pady=5)
            lbl.bind("<Button-1>", lambda _e, c=command: c())
            lbl.bind("<Enter>", lambda _e: SoundBus.play("hover"))
        tk.Frame(frame, bg=C["border"], height=1).pack(fill="x")
        self._output = tk.Text(frame, bg=C["bg"], fg=C["text"], insertbackground=C["cyan"], font=("Courier New", 11), relief="flat", bd=4, state="normal", wrap="word", selectbackground=C["border_hi"])
        self._output.pack(fill="both", expand=True, padx=4, pady=4)
        self._output.tag_config("code", foreground=C["cyan"], font=("Courier New", 11))
        self._output.tag_config("comment", foreground=C["text_dim"])
        self._output.tag_config("success", foreground=C["green"])
        self._output.tag_config("error", foreground=C["error"])
        self._output.tag_config("header", foreground=C["purple"], font=F["small"])
        self._write_output("NEXUS CODER online. Cole codigo no editor ou use a barra de comando.\n", "comment")

    def _build_sidebar(self):
        sb = ctk.CTkScrollableFrame(self, fg_color=C["panel"], width=210, scrollbar_button_color=C["border"])
        sb.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(0, 10), pady=(10, 4))

        def section(title: str):
            tk.Label(sb, text=title, bg=C["panel"], fg=C["cyan"], font=F["tiny"]).pack(anchor="w", padx=8, pady=(10, 3))
            tk.Frame(sb, bg=C["border"], height=1).pack(fill="x", padx=4)

        def btn(text: str, command, style: str = "ghost"):
            button = ctk.CTkButton(sb, text=text, command=command, height=28, anchor="w", width=190, **BTN.get(style, BTN["ghost"]))
            bind_button_fx(button)
            button.pack(fill="x", padx=4, pady=2)

        section("IA - CODIGO")
        btn("Explicar codigo", lambda: self._cmd_com_codigo("explica o codigo"))
        btn("Revisar bugs", lambda: self._cmd_com_codigo("revisa o codigo"))
        btn("Refatorar", lambda: self._cmd_com_codigo("refatora o codigo"))
        btn("Gerar testes", lambda: self._cmd_com_codigo("gera testes para o codigo"))
        btn("Documentar", lambda: self._cmd_com_codigo("documenta o codigo"))
        btn("Otimizar performance", lambda: self._cmd_com_codigo("otimiza performance do codigo"))
        btn("Auditoria seguranca", lambda: self._cmd_com_codigo("auditoria de seguranca"))
        btn("Converter linguagem", self._prompt_converter)

        section("EXECUCAO")
        btn("Rodar codigo", self._rodar_codigo, "success")
        btn("Instalar pacote", self._prompt_instalar)
        btn("Verificar ambiente", lambda: self._cmd("verifica o ambiente"))
        btn("Historico terminal", lambda: self._cmd("historico de terminal"))
        btn("Rodar ruff", lambda: self._cmd("roda ruff"))
        btn("Rodar pytest", lambda: self._cmd("roda pytest"))

        section("COPILOTO LOCAL")
        btn("Contexto projeto", lambda: self._cmd("contexto do projeto"))
        btn("Gerar patch IA", self._prompt_ai_patch, "success")
        btn("Preview patch", lambda: self._cmd("preview patch"))
        btn("Aplicar patch", lambda: self._cmd("aplicar patch"), "danger")

        section("GIT")
        btn("Status", lambda: self._cmd("git status"))
        btn("Diff", lambda: self._cmd("git diff"))
        btn("Log", lambda: self._cmd("git log"))
        btn("Add tudo", lambda: self._cmd("git add"))
        btn("Commit IA", lambda: self._cmd("commit automatico com ia"))
        btn("Push", lambda: self._cmd("git push"))
        btn("Pull", lambda: self._cmd("git pull"))
        btn("Resumo repo", lambda: self._cmd("resumo do repositorio"))

        section("PROJETO")
        btn("Definir projeto", self._prompt_projeto)
        btn("Estrutura", lambda: self._cmd("mostra a estrutura do projeto"))
        btn("Linhas de codigo", lambda: self._cmd("conta linhas"))
        btn("Buscar no codigo", self._prompt_buscar)

        section("SCAFFOLD")
        btn("Listar templates", lambda: self._cmd("lista templates"))
        btn("Criar projeto", self._prompt_scaffold, "success")
        btn("FastAPI rapido", lambda: self._prompt_scaffold("fastapi"))
        btn("React rapido", lambda: self._prompt_scaffold("react"))
        btn("Express rapido", lambda: self._prompt_scaffold("express"))

        section("SNIPPETS")
        btn("Salvar snippet", self._prompt_salvar_snippet)
        btn("Buscar snippets", self._prompt_buscar_snippet)
        btn("Listar snippets", lambda: self._cmd("lista os snippets"))
        btn("Stats snippets", lambda: self._cmd("estatisticas dos snippets"))

    def _build_command_bar(self):
        bar = tk.Frame(self, bg=C["card"])
        bar.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
        tk.Frame(bar, bg=C["cyan"], height=1).pack(fill="x")
        inner = tk.Frame(bar, bg=C["card"])
        inner.pack(fill="x", padx=10, pady=8)
        tk.Label(inner, text=">", bg=C["card"], fg=C["cyan"], font=F["body"]).pack(side="left", padx=(0, 6))
        self._cmd_input = tk.Entry(inner, bg=C["card"], fg=C["text"], insertbackground=C["cyan"], font=F["body"], relief="flat")
        self._cmd_input.pack(side="left", fill="x", expand=True, ipady=6)
        self._cmd_input.insert(0, "  Ex: gera um codigo python para ler CSV...")
        self._cmd_input.configure(fg=C["text_muted"])
        self._cmd_input.bind("<Return>", self._submit_cmd)
        self._cmd_input.bind("<FocusIn>", self._focus_command)
        self._cmd_input.bind("<FocusOut>", self._blur_command)
        run_button = ctk.CTkButton(inner, text="Executar", command=self._submit_cmd_btn, height=34, width=90, **BTN["primary"])
        bind_button_fx(run_button)
        run_button.pack(side="left", padx=6)
        tk.Label(inner, textvariable=self._linguagem_var, bg=C["cyan_bg"], fg=C["cyan"], font=F["tiny"], padx=6, pady=2).pack(side="left", padx=6)

    def _cmd(self, texto: str):
        if not self._on_command:
            return
        self._set_context_from_editor()
        self._write_output(f"\n> {texto}\n", "header")

        def worker():
            try:
                result = self._on_command(texto)
                self.after(0, lambda: self._show_ai_response(result))
            except Exception as error:
                self.after(0, lambda: self._show_ai_response(f"Erro: {error}", error=True))

        threading.Thread(target=worker, daemon=True).start()

    def _cmd_com_codigo(self, base_cmd: str):
        if not self.get_codigo().strip():
            self._write_output("Editor vazio. Cole codigo antes de usar esta acao.\n", "error")
            return
        self._cmd(base_cmd)

    def _submit_cmd(self, _event=None):
        text = self._cmd_input.get().strip()
        if not text or text.startswith("Ex:"):
            return
        self._cmd_input.delete(0, "end")
        self._cmd(text)

    def _submit_cmd_btn(self):
        self._submit_cmd()

    def _rodar_codigo(self):
        code = self.get_codigo().strip()
        if not code:
            self._write_output("Editor vazio.\n", "error")
            return
        lang = self._linguagem_var.get()
        self._write_output(f"\nExecutando ({lang})...\n", "header")
        SoundBus.play("start")

        def worker():
            from coding.code_runner import executar_auto
            result = executar_auto(code, lang)
            self.after(0, lambda: SoundBus.play("success" if result.success else "error"))
            self.after(0, lambda: self._write_output(result.format() + "\n", "success" if result.success else "error"))

        threading.Thread(target=worker, daemon=True).start()

    def _set_context_from_editor(self):
        try:
            from coding.dispatcher import set_contexto
            set_contexto(codigo=self.get_codigo().strip(), linguagem=self._linguagem_var.get())
        except Exception:
            pass

    def _show_ai_response(self, text: str, error: bool = False):
        self._write_output(f"\n-- NEXUS [{datetime.datetime.now():%H:%M:%S}] --\n", "header")
        for part in re.split(r"(```(?:\w+)?\n.*?```)", text or "", flags=re.DOTALL):
            self._write_output(part, "code" if part.startswith("```") else ("error" if error else "comment"))
        self._write_output("\n")

    def _write_output(self, text: str, tag: str = ""):
        self._output.configure(state="normal")
        self._output.insert("end", text, tag or None)
        self._output.see("end")

    def _copiar_codigo(self):
        self.clipboard_clear()
        self.clipboard_append(self.get_codigo())
        show_toast(self.winfo_toplevel(), "Codigo copiado!", "success", 1500)

    def _limpar_editor(self):
        self._editor.delete("1.0", "end")
        self._update_line_nums()

    def _salvar_arquivo(self):
        code = self.get_codigo().strip()
        if not code:
            return
        ext = {"python": ".py", "javascript": ".js", "typescript": ".ts", "html": ".html", "css": ".css"}.get(self._linguagem_var.get(), ".txt")
        path = filedialog.asksaveasfilename(defaultextension=ext, filetypes=[("Codigo", f"*{ext}"), ("Todos", "*.*")])
        if path:
            from pathlib import Path
            Path(path).write_text(code, encoding="utf-8")
            self._filename_var.set(Path(path).name)
            show_toast(self.winfo_toplevel(), f"Salvo: {Path(path).name}", "success")

    def _copiar_output(self):
        self.clipboard_clear()
        self.clipboard_append(self._output.get("1.0", "end-1c"))
        show_toast(self.winfo_toplevel(), "Copiado!", "success", 1500)

    def _limpar_output(self):
        self._output.delete("1.0", "end")

    def _output_para_editor(self):
        blocks = re.findall(r"```(?:\w+)?\n(.*?)```", self._output.get("1.0", "end-1c"), re.DOTALL)
        if not blocks:
            show_toast(self.winfo_toplevel(), "Nenhum bloco de codigo encontrado.", "warning")
            return
        self.set_codigo(blocks[0].strip(), self._linguagem_var.get())
        show_toast(self.winfo_toplevel(), "Codigo enviado ao editor.", "success")

    def _prompt_instalar(self):
        dialog = ctk.CTkInputDialog(text="Nome do pacote pip:", title="Instalar pacote")
        package = dialog.get_input()
        if package:
            self._cmd(f"instala o pacote {package}")

    def _prompt_buscar(self):
        dialog = ctk.CTkInputDialog(text="Buscar no projeto:", title="Busca no codigo")
        term = dialog.get_input()
        if term:
            self._cmd(f"busca {term} no projeto")

    def _prompt_projeto(self):
        path = filedialog.askdirectory(title="Selecionar projeto")
        if path:
            self._cmd(f"define o projeto em {path}")
            self._projeto_var.set(path)

    def _prompt_scaffold(self, template: str = ""):
        if template:
            dialog = ctk.CTkInputDialog(text=f"Nome do projeto {template}:", title="Criar projeto")
            name = dialog.get_input()
            if name:
                self._cmd(f"cria projeto {template} chamado {name}")
            return
        dialog = ctk.CTkInputDialog(text="Template e nome. Ex: fastapi minha-api", title="Criar projeto")
        text = dialog.get_input()
        if not text:
            return
        parts = text.strip().split(maxsplit=1)
        if len(parts) == 1:
            self._cmd(f"cria projeto {parts[0]} chamado app-nexus")
        else:
            self._cmd(f"cria projeto {parts[0]} chamado {parts[1]}")

    def _prompt_salvar_snippet(self):
        if not self.get_codigo().strip():
            show_toast(self.winfo_toplevel(), "Editor vazio.", "warning")
            return
        dialog = ctk.CTkInputDialog(text="Nome do snippet:", title="Salvar snippet")
        title = dialog.get_input()
        if title:
            self._cmd(f"salva snippet como {title}")

    def _prompt_buscar_snippet(self):
        dialog = ctk.CTkInputDialog(text="Buscar snippets:", title="Snippets")
        term = dialog.get_input()
        if term:
            self._cmd(f"busca snippets de {term}")

    def _prompt_converter(self):
        dialog = ctk.CTkInputDialog(text="Ex: python para javascript", title="Converter linguagem")
        text = dialog.get_input()
        if text:
            self._cmd_com_codigo(f"converte {text}")

    def _prompt_ai_patch(self):
        dialog = ctk.CTkInputDialog(text="O que implementar/corrigir no projeto ativo?", title="Patch com IA")
        text = dialog.get_input()
        if text:
            self._cmd(f"gera patch para {text}")

    def _focus_command(self, _event):
        if self._cmd_input.get().startswith("  Ex:"):
            self._cmd_input.delete(0, "end")
            self._cmd_input.configure(fg=C["text"])

    def _blur_command(self, _event):
        if not self._cmd_input.get():
            self._cmd_input.insert(0, "  Ex: gera um codigo python para ler CSV...")
            self._cmd_input.configure(fg=C["text_muted"])

    def _sync_scroll(self, *args):
        self._editor.yview(*args)
        self._line_nums.yview(*args)

    def _update_line_nums(self, _event=None):
        n_lines = self._editor.get("1.0", "end-1c").count("\n") + 1
        nums = "\n".join(str(i) for i in range(1, n_lines + 1))
        self._line_nums.configure(state="normal")
        self._line_nums.delete("1.0", "end")
        self._line_nums.insert("1.0", nums)
        self._line_nums.configure(state="disabled")

    def _insert_tab(self, _event):
        self._editor.insert(tk.INSERT, "    ")
        return "break"

    def _on_lang_change(self, lang: str):
        try:
            from coding.dispatcher import set_contexto
            set_contexto(linguagem=lang)
        except Exception:
            pass

    def set_codigo(self, codigo: str, linguagem: str = "python"):
        self._editor.delete("1.0", "end")
        self._editor.insert("1.0", codigo)
        self._linguagem_var.set(linguagem)
        self._update_line_nums()

    def get_codigo(self) -> str:
        return self._editor.get("1.0", "end-1c")

    def set_output(self, text: str):
        self._limpar_output()
        self._write_output(text or "", "comment")

    def get_filename(self) -> str:
        return self._filename_var.get()

    def set_filename(self, filename: str):
        self._filename_var.set(filename or "main.py")

    def build_editor_bridge(self):
        from app.coder.editor_bridge import EditorBridge

        return EditorBridge(
            get_code=self.get_codigo,
            set_code=lambda text: self.set_codigo(text, self._linguagem_var.get()),
            get_filename=self.get_filename,
            set_filename=self.set_filename,
            set_output=self.set_output,
            clear_output=self._limpar_output,
        )
