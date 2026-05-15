import { useState } from "react";
import { motion } from "framer-motion";
import { BookOpen, Brain, Mic, Pause, Play, RotateCcw, Save, Square, Sparkles } from "lucide-react";

import { NexusParticleOrb } from "@/components/nexus-particle-orb";
import { ConversationStatusBar } from "@/components/conversation-status-bar";
import { VoiceSettingsPanel } from "@/components/voice-settings-panel";
import type { ConversationModeController } from "@/hooks/useConversationMode";

function buildSuggestedTitle(controller: ConversationModeController) {
  if (controller.session?.current_topic?.trim()) {
    return `Resumo de ${controller.session.current_topic.trim()}`;
  }
  return "Resumo de conversa do Nexus";
}

export function ConversationModePanel({
  conversation,
  ownerName,
}: {
  conversation: ConversationModeController;
  ownerName: string;
}) {
  const [manualInput, setManualInput] = useState("");
  const [isSavingNote, setIsSavingNote] = useState(false);

  async function handleManualSend() {
    const cleaned = manualInput.trim();
    if (!cleaned) {
      return;
    }
    await conversation.sendText(cleaned);
    setManualInput("");
  }

  async function handleSaveNote() {
    setIsSavingNote(true);
    try {
      await conversation.saveCurrentNote(buildSuggestedTitle(conversation));
    } finally {
      setIsSavingNote(false);
    }
  }

  return (
    <section className="space-y-6 px-4 py-8 lg:px-12">
      <div className="grid gap-6 xl:grid-cols-[0.95fr_1.15fr]">
        <div className="rounded-[28px] border border-white/10 bg-white/[0.04] p-6 shadow-2xl shadow-black/20 backdrop-blur-xl">
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="shell-eyebrow text-cyan-300">Modo Conversa Natural</p>
              <h2 className="mt-2 text-2xl font-semibold text-white">Modo Jarvis</h2>
              <p className="mt-3 text-sm leading-7 text-slate-400">
                Converse de forma natural com o Nexus para estudar, organizar tarefas, tirar duvidas e salvar conhecimento no Obsidian.
              </p>
            </div>
            <div className="rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-xs uppercase tracking-[0.22em] text-slate-400">
              {ownerName}
            </div>
          </div>

          <div className="mt-8 flex justify-center">
            <motion.div
              initial={{ opacity: 0.88, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.2 }}
              className="rounded-full border border-white/10 bg-[radial-gradient(circle_at_center,rgba(34,211,238,0.09),transparent_70%)] p-4"
            >
              <NexusParticleOrb
                state={conversation.state}
                speakingLevel={conversation.speakingLevel}
                intensity={conversation.studyMode ? 1.05 : 0.92}
                size={280}
              />
            </motion.div>
          </div>

          <div className="mt-6">
            <ConversationStatusBar state={conversation.state} error={conversation.error} />
          </div>

          <div className="mt-5">
            <VoiceSettingsPanel voice={conversation.professionalVoice} />
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-2">
            <button
              type="button"
              className={`shell-primary-button ${conversation.active ? "opacity-90" : ""}`}
              onClick={() => {
                void (conversation.active ? conversation.stopConversation() : conversation.startConversation());
              }}
            >
              {conversation.active ? <Square className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
              {conversation.active ? "Encerrar conversa" : "Ativar conversa"}
            </button>
            <button
              type="button"
              className="shell-chip justify-center"
              onClick={() => {
                void (conversation.state === "paused" ? conversation.resumeConversation() : conversation.pauseConversation());
              }}
            >
              {conversation.state === "paused" ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
              {conversation.state === "paused" ? "Retomar" : "Pausar"}
            </button>
            <button
              type="button"
              className={`shell-chip justify-center ${conversation.studyMode ? "border-cyan-400/30 bg-cyan-400/10 text-cyan-200" : ""}`}
              onClick={conversation.toggleStudyMode}
            >
              <Brain className="h-4 w-4" />
              {conversation.studyMode ? "Modo estudo ON" : "Modo estudo OFF"}
            </button>
            <button type="button" className="shell-chip justify-center" onClick={() => void conversation.resetConversation()}>
              <RotateCcw className="h-4 w-4" />
              Resetar contexto
            </button>
            <button
              type="button"
              className="shell-chip justify-center sm:col-span-2"
              onClick={() => void handleSaveNote()}
              disabled={!conversation.lastResponse.trim() || isSavingNote}
            >
              <Save className="h-4 w-4" />
              {isSavingNote ? "Salvando..." : "Salvar resumo no Obsidian"}
            </button>
          </div>
        </div>

        <div className="space-y-6">
          <div className="rounded-[28px] border border-white/10 bg-white/[0.04] p-6 shadow-2xl shadow-black/20 backdrop-blur-xl">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="shell-eyebrow">Sessao viva</p>
                <h3 className="mt-2 text-xl font-semibold text-white">Contexto atual</h3>
              </div>
              <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-slate-400">
                {conversation.sessionId || "nova sessao"}
              </span>
            </div>

            <div className="mt-5 grid gap-4 md:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="shell-eyebrow">ultima fala</p>
                <p className="mt-3 text-sm leading-7 text-slate-200">{conversation.transcript || "Ainda esperando voce falar ou digitar."}</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="shell-eyebrow">ultimo topico</p>
                <p className="mt-3 text-sm leading-7 text-slate-200">{conversation.topic || conversation.session?.current_topic || "Sem topico definido ainda."}</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4 md:col-span-2">
                <p className="shell-eyebrow">ultima resposta</p>
                <p className="mt-3 text-sm leading-7 text-slate-200">{conversation.lastResponse || "As respostas do Nexus vao aparecer aqui em texto enquanto ele fala."}</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="shell-eyebrow">intencao detectada</p>
                <p className="mt-3 text-sm leading-7 text-slate-200">{conversation.intent || "general_chat"}</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="shell-eyebrow">notas relacionadas</p>
                <p className="mt-3 text-sm leading-7 text-slate-200">
                  {conversation.session?.related_notes?.length ? conversation.session.related_notes.join(", ") : "Nenhuma nota relevante usada ainda."}
                </p>
              </div>
            </div>
          </div>

          <div className="rounded-[28px] border border-white/10 bg-white/[0.04] p-6 shadow-2xl shadow-black/20 backdrop-blur-xl">
            <div className="flex items-center justify-between gap-4">
              <div>
                <p className="shell-eyebrow">Entrada manual</p>
                <h3 className="mt-2 text-xl font-semibold text-white">Falar ou digitar</h3>
              </div>
              <Sparkles className="h-5 w-5 text-cyan-300" />
            </div>

            <div className="mt-5 space-y-4">
              <textarea
                value={manualInput}
                onChange={(event) => setManualInput(event.target.value)}
                onKeyDown={(event) => {
                  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                    event.preventDefault();
                    void handleManualSend();
                  }
                }}
                rows={4}
                placeholder="Ex: me ajuda a estudar computacao em nuvem"
                className="w-full rounded-3xl border border-white/10 bg-[#0c1422]/80 px-4 py-4 text-sm leading-7 text-white outline-none placeholder:text-slate-500"
              />
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  className="shell-primary-button"
                  disabled={!manualInput.trim() || conversation.isThinking || conversation.isSpeaking}
                  onClick={() => void handleManualSend()}
                >
                  <BookOpen className="h-4 w-4" />
                  Enviar mensagem
                </button>
                <button
                  type="button"
                  className="shell-chip"
                  onClick={() => setManualInput("me ajuda a estudar redes")}
                >
                  exemplo de estudo
                </button>
                <button
                  type="button"
                  className="shell-chip"
                  onClick={() => setManualInput("faz perguntas sobre TCP e UDP")}
                >
                  exemplo de quiz
                </button>
              </div>

              {conversation.savedNotePath ? (
                <div className="rounded-2xl border border-emerald-400/20 bg-emerald-400/10 px-4 py-3 text-sm text-emerald-200">
                  Nota salva em: {conversation.savedNotePath}
                </div>
              ) : null}
              {!conversation.voiceSupported ? (
                <div className="rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-200">
                  Seu navegador nao oferece reconhecimento de voz aqui. O modo continua funcionando por texto e TTS quando disponivel.
                </div>
              ) : null}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
