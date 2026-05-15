from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from uuid import uuid4

from app.assistant import conversar
from app.chat.session_context import SessionContext
from app.chat.study_assistant import detect_study_intent
from app.obsidian_memory import save_note, search
from app.settings_manager import load as load_settings

CONVERSATION_PROMPT = """Voce e o Nexus Companion do Nicolas.

Quando o Modo Conversa Natural estiver ativo:
- responda em portugues do Brasil;
- fale de forma natural, curta e clara;
- nao use linguagem robotica;
- nao faca respostas longas sem necessidade;
- mantenha contexto da conversa atual;
- se o assunto for estudo, atue como tutor inteligente;
- explique do simples ao tecnico quando necessario;
- proponha passos praticos;
- faca perguntas curtas quando precisar entender melhor;
- ajude em tarefas, resumos, revisoes e organizacao;
- quando a resposta puder ser curta, seja curta;
- quando o usuario pedir aprofundamento, aprofunde;
- se houver memoria relevante no Obsidian, use;
- se faltarem dados, pergunte antes de assumir;
- nunca diga que executou algo se nao executou.
"""


@dataclass(frozen=True)
class ConversationResult:
    ok: bool
    session_id: str
    state: str
    intent: str
    topic: str
    response: str
    should_speak: bool
    saved_note_path: str | None
    session: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "session_id": self.session_id,
            "state": self.state,
            "intent": self.intent,
            "topic": self.topic,
            "response": self.response,
            "should_speak": self.should_speak,
            "saved_note_path": self.saved_note_path,
            "session": self.session,
        }


class ConversationModeRuntime:
    def __init__(self):
        self._sessions: dict[str, SessionContext] = {}
        self._lock = Lock()
        self._state = "idle"
        self._active_session_id: str | None = None

    def process_message(
        self,
        text: str,
        *,
        session_id: str | None = None,
        study_mode: bool = True,
        save_to_obsidian: bool = False,
    ) -> ConversationResult:
        cleaned = (text or "").strip()
        session = self._get_or_create_session(session_id)
        if not cleaned:
            self._state = "error"
            return ConversationResult(
                ok=False,
                session_id=session.session_id,
                state="error",
                intent="general_chat",
                topic=session.current_topic,
                response="Diga ou escreva algo para eu continuar a conversa.",
                should_speak=False,
                saved_note_path=None,
                session=session.to_dict(),
            )

        self._state = "thinking"
        session.study_mode_enabled = bool(study_mode)
        session.add_user_message(cleaned)

        intent_payload = detect_study_intent(cleaned)
        intent_name = str(intent_payload.get("intent") or "general_chat")
        topic = str(intent_payload.get("topic") or "").strip() or session.current_topic
        if topic:
            session.set_topic(topic)
        session.set_goal(self._goal_for_intent(intent_name, topic))
        related_hits = search(topic or cleaned, limit=3) if (topic or study_mode) else []
        session.related_notes = [hit.title for hit in related_hits[:3]]

        explicit_save = bool(save_to_obsidian or intent_name == "save_note")
        if explicit_save:
            saved_path = self.save_note(
                session_id=session.session_id,
                title=self._build_note_title(session),
                content=self._build_note_content(session),
            )
            response = (
                f"Salvei no Obsidian como {self._build_note_title(session)}."
                if saved_path
                else "Nao consegui salvar no Obsidian agora. Verifique se o vault esta configurado."
            )
            session.add_assistant_message(response)
            self._state = "ready" if saved_path else "error"
            return ConversationResult(
                ok=bool(saved_path),
                session_id=session.session_id,
                state="ready" if saved_path else "error",
                intent=intent_name,
                topic=session.current_topic,
                response=response,
                should_speak=True,
                saved_note_path=saved_path,
                session=session.to_dict(),
            )

        response = self._generate_response(cleaned, session, intent_name, topic)
        if intent_name in {"summarize", "explain", "quiz", "simplify", "deepen"}:
            session.last_summary = response
        session.add_assistant_message(response)
        self._state = "ready"
        return ConversationResult(
            ok=True,
            session_id=session.session_id,
            state="ready",
            intent=intent_name,
            topic=session.current_topic,
            response=response,
            should_speak=True,
            saved_note_path=None,
            session=session.to_dict(),
        )

    def reset(self, session_id: str) -> bool:
        session = self._get_or_create_session(session_id)
        session.reset()
        self._state = "idle"
        return True

    def save_note(self, *, session_id: str, title: str, content: str) -> str | None:
        session = self._get_or_create_session(session_id)
        note = save_note(
            title=title,
            body=self._build_note_body(session, title, content),
            folder=self._note_folder_for_session(session),
            frontmatter={
                "source": "nexus-conversation",
                "type": "study-note",
                "created": session.updated_at,
                "topic": session.current_topic,
                "tags": ["nexus", "estudo", "conversa"],
            },
        )
        return str(note) if note else None

    def get_state(self) -> dict[str, object]:
        session = self._sessions.get(self._active_session_id or "")
        return {
            "ok": True,
            "state": self._state,
            "session": session.to_dict() if session else None,
        }

    def _get_or_create_session(self, session_id: str | None) -> SessionContext:
        with self._lock:
            resolved_id = (session_id or "").strip() or uuid4().hex
            session = self._sessions.get(resolved_id)
            if session is None:
                session = SessionContext(session_id=resolved_id)
                self._sessions[resolved_id] = session
            self._active_session_id = resolved_id
            return session

    def _generate_response(self, user_text: str, session: SessionContext, intent_name: str, topic: str) -> str:
        settings = load_settings()
        owner_name = str(settings.get("owner_name", "Nicolas") or "Nicolas")
        study_guidance = self._intent_guidance(intent_name, topic, session.study_mode_enabled)
        context_block = session.get_context_text()
        system_prompt = (
            CONVERSATION_PROMPT
            + f"\n\nDono atual: {owner_name}."
            + (f"\n\nContexto da sessao:\n{context_block}" if context_block else "")
            + (f"\n\nOrientacao desta resposta:\n{study_guidance}" if study_guidance else "")
        )
        answer, _hits = conversar(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            memory_query=topic or user_text,
            temperature=0.35 if session.study_mode_enabled else 0.45,
        )
        return (answer or ".").strip()

    def _intent_guidance(self, intent_name: str, topic: str, study_mode: bool) -> str:
        topic_line = f"Topico principal: {topic}." if topic else ""
        intent_guidance = {
            "explain": "Explique em linguagem natural, curta e util. Se fizer sentido, ofereca um proximo passo simples.",
            "summarize": "Produza um resumo enxuto, em blocos curtos, destacando ideias centrais e um fechamento pratico.",
            "quiz": "Monte uma pergunta por vez, curta, e espere a resposta do usuario em vez de despejar varias perguntas de uma vez.",
            "task_help": "Ajude como tutor de tarefa: organize passos, itens e o que falta descobrir.",
            "code_help": "Explique codigo com clareza, apontando objetivo, funcionamento e o que observar primeiro.",
            "simplify": "Reexplique de forma mais simples, usando comparacoes curtas se ajudarem.",
            "deepen": "Aprofunde um pouco mais, trazendo detalhe tecnico sem perder clareza.",
            "continue_topic": "Continue do ponto anterior, mantendo o contexto ja existente sem reiniciar do zero.",
            "general_chat": "Responda de forma natural, objetiva e colaborativa.",
        }.get(intent_name, "Responda com clareza e contexto.")
        if study_mode and intent_name == "general_chat":
            intent_guidance += " Como o modo estudo esta ativo, puxe a resposta para uma pegada de tutor quando fizer sentido."
        return "\n".join(part for part in [topic_line, intent_guidance] if part)

    def _goal_for_intent(self, intent_name: str, topic: str) -> str:
        if intent_name == "quiz":
            return f"revisar por perguntas: {topic}".strip(": ")
        if intent_name == "summarize":
            return f"resumir: {topic}".strip(": ")
        if intent_name == "code_help":
            return f"entender codigo: {topic}".strip(": ")
        if intent_name == "task_help":
            return f"organizar tarefa: {topic}".strip(": ")
        if intent_name == "explain":
            return f"aprender: {topic}".strip(": ")
        return topic or intent_name

    def _build_note_title(self, session: SessionContext) -> str:
        if session.current_topic:
            return f"Resumo de {session.current_topic}"
        return "Resumo de conversa do Nexus"

    def _build_note_content(self, session: SessionContext) -> str:
        if session.last_summary.strip():
            return session.last_summary.strip()
        if session.last_assistant_messages:
            return session.last_assistant_messages[-1]
        return "Sem conteudo suficiente para salvar ainda."

    def _build_note_body(self, session: SessionContext, title: str, content: str) -> str:
        previous_context = session.get_context_text()
        next_steps = self._infer_next_steps(session, content)
        return (
            f"# {title}\n\n"
            "## Contexto\n\n"
            f"{previous_context or 'Conversa natural do Nexus.'}\n\n"
            "## Resumo\n\n"
            f"{content.strip()}\n\n"
            "## Proximos passos\n\n"
            f"{next_steps}\n"
        )

    def _infer_next_steps(self, session: SessionContext, content: str) -> str:
        suggestions: list[str] = []
        if session.current_topic:
            suggestions.append(f"- Revisar novamente o topico {session.current_topic}.")
        if session.current_goal:
            suggestions.append(f"- Continuar no objetivo atual: {session.current_goal}.")
        if "?" not in content:
            suggestions.append("- Pedir exemplos ou perguntas de revisao para fixar melhor.")
        return "\n".join(suggestions) or "- Continuar a conversa quando precisar aprofundar."

    def _note_folder_for_session(self, session: SessionContext) -> str:
        goal_text = session.current_goal.lower()
        if "perguntas" in goal_text or "quiz" in goal_text:
            return "NEXUS/Flashcards"
        if "resumir" in goal_text or session.last_summary:
            return "NEXUS/Resumos"
        if session.study_mode_enabled:
            return "NEXUS/Estudos"
        return "NEXUS/Conversas"
