import type { OrbState } from "@/hooks/useConversationMode";

const COPY: Record<OrbState, { label: string; description: string; tone: string }> = {
  idle: {
    label: "Modo parado.",
    description: "Ative a conversa natural para o Nexus voltar a ouvir voce.",
    tone: "text-slate-300",
  },
  listening: {
    label: "Ouvindo voce...",
    description: "Pode falar de forma natural. O Nexus esta captando sua fala agora.",
    tone: "text-cyan-300",
  },
  thinking: {
    label: "Pensando na melhor resposta...",
    description: "Organizando contexto, memoria e proximo passo antes de responder.",
    tone: "text-amber-300",
  },
  generating_audio: {
    label: "Preparando voz...",
    description: "Gerando a primeira frase em audio para responder sem travar a conversa.",
    tone: "text-amber-300",
  },
  speaking: {
    label: "Respondendo...",
    description: "A resposta tambem aparece em texto para voce continuar a conversa sem depender so da voz.",
    tone: "text-emerald-300",
  },
  ready: {
    label: "Pronto para continuar.",
    description: "Assim que terminar de falar, o Nexus volta a ouvir automaticamente.",
    tone: "text-emerald-300",
  },
  error: {
    label: "Algo deu errado.",
    description: "Revise a mensagem abaixo ou use o campo manual para continuar.",
    tone: "text-rose-300",
  },
  interrupted: {
    label: "Fala interrompida.",
    description: "A fila de voz foi limpa e o Nexus esta pronto para uma nova instrucao.",
    tone: "text-slate-300",
  },
  paused: {
    label: "Modo pausado.",
    description: "O contexto continua salvo. Quando quiser, retome do ponto em que parou.",
    tone: "text-slate-300",
  },
};

export function ConversationStatusBar({
  state,
  error,
}: {
  state: OrbState;
  error?: string;
}) {
  const copy = COPY[state];
  return (
    <div className="rounded-2xl border border-white/10 bg-white/[0.04] px-4 py-3 backdrop-blur-xl">
      <p className={`text-sm font-semibold ${copy.tone}`}>{copy.label}</p>
      <p className="mt-1 text-sm leading-6 text-slate-400">{error?.trim() || copy.description}</p>
    </div>
  );
}
