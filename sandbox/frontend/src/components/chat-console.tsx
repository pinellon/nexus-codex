import { AnimatePresence, motion } from "framer-motion";
import { ArrowUpRight, ShieldAlert, Zap } from "lucide-react";

import { cn } from "@/lib/utils";
import { Panel } from "@/components/ui/panel";
import { Pill } from "@/components/ui/pill";

export type ChatMessage = {
  id: string;
  role: "assistant" | "user" | "system";
  content: string;
  meta?: string;
};

type ChatConsoleProps = {
  command: string;
  isSending: boolean;
  messages: ChatMessage[];
  pendingConfirmation: string | null;
  quickActions: string[];
  onChange: (value: string) => void;
  onSend: () => void;
  onQuickAction: (value: string) => void;
  onConfirmPending: () => void;
};

const roleStyles: Record<ChatMessage["role"], string> = {
  assistant: "border-accent-cyan/15 bg-accent-cyan/8 text-white",
  user: "border-accent-amber/15 bg-accent-amber/8 text-white",
  system: "border-white/10 bg-white/5 text-slate-200",
};

export function ChatConsole({
  command,
  isSending,
  messages,
  pendingConfirmation,
  quickActions,
  onChange,
  onSend,
  onQuickAction,
  onConfirmPending,
}: ChatConsoleProps) {
  return (
    <Panel tone="cyan" className="p-6">
      <div className="flex flex-col gap-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <Pill label="command surface" tone="cyan" />
            <h2 className="mt-3 text-2xl font-semibold tracking-tight">NEXUS / chat gateway</h2>
            <p className="mt-2 max-w-2xl text-sm text-muted">
              O frontend novo conversa com o pipeline real do projeto. Confirmacoes de risco ja voltam pela API.
            </p>
          </div>
          <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs text-muted">
            <Zap className="h-4 w-4 text-accent-cyan" />
            {isSending ? "Processando" : "Pronto"}
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {quickActions.map((action) => (
            <button
              key={action}
              type="button"
              onClick={() => onQuickAction(action)}
              className="rounded-full border border-white/10 bg-white/5 px-3 py-2 font-mono text-xs text-slate-200 transition hover:border-accent-cyan/30 hover:bg-accent-cyan/10 hover:text-accent-cyan"
            >
              {action}
            </button>
          ))}
        </div>

        <div className="grid gap-4 lg:grid-cols-[1fr_280px]">
          <div className="rounded-[24px] border border-white/8 bg-bg/60 p-3">
            <div className="max-h-[28rem] space-y-3 overflow-y-auto pr-1">
              <AnimatePresence initial={false}>
                {messages.map((message) => (
                  <motion.article
                    key={message.id}
                    initial={{ opacity: 0, y: 18 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -8 }}
                    transition={{ duration: 0.22 }}
                    className={cn("rounded-3xl border px-4 py-3", roleStyles[message.role])}
                  >
                    <div className="flex items-center justify-between gap-3 text-[11px] uppercase tracking-[0.26em] text-muted">
                      <span>{message.role}</span>
                      {message.meta ? <span className="truncate text-right">{message.meta}</span> : null}
                    </div>
                    <p className="mt-2 whitespace-pre-wrap text-sm leading-6">{message.content}</p>
                  </motion.article>
                ))}
              </AnimatePresence>
            </div>
          </div>

          <div className="space-y-3 rounded-[24px] border border-white/8 bg-elevated/50 p-4">
            <div className="rounded-2xl border border-white/8 bg-black/15 p-4">
              <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-accent-cyan">flow</p>
              <p className="mt-2 text-sm text-slate-200">Web shell, API Python e roteador de comandos unificados.</p>
            </div>
            <div className="rounded-2xl border border-white/8 bg-black/15 p-4">
              <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-accent-amber">status</p>
              <p className="mt-2 text-sm text-slate-200">
                A interface nova nao substitui o desktop ainda. Ela roda em paralelo para a migracao.
              </p>
            </div>
            {pendingConfirmation ? (
              <div className="rounded-2xl border border-accent-orange/25 bg-accent-orange/10 p-4">
                <div className="flex items-start gap-3">
                  <ShieldAlert className="mt-0.5 h-5 w-5 text-accent-orange" />
                  <div>
                    <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-accent-orange">
                      confirmacao pendente
                    </p>
                    <p className="mt-2 text-sm text-slate-100">{pendingConfirmation}</p>
                    <button
                      type="button"
                      onClick={onConfirmPending}
                      className="mt-4 inline-flex items-center gap-2 rounded-full border border-accent-orange/30 bg-black/20 px-3 py-2 text-xs font-medium text-accent-orange transition hover:bg-accent-orange/15"
                    >
                      Confirmar comando
                      <ArrowUpRight className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>

        <div className="rounded-[24px] border border-white/8 bg-bg/70 p-3">
          <div className="flex flex-col gap-3">
            <textarea
              value={command}
              onChange={(event) => onChange(event.target.value)}
              onKeyDown={(event) => {
                if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
                  event.preventDefault();
                  onSend();
                }
              }}
              rows={4}
              placeholder="Digite um comando, pergunta ou fluxo do projeto..."
              className="min-h-32 w-full resize-none rounded-[18px] border border-white/8 bg-transparent px-4 py-4 font-mono text-sm text-white outline-none placeholder:text-muted"
            />
            <div className="flex flex-wrap items-center justify-between gap-3">
              <p className="text-xs text-muted">Ctrl+Enter envia. A API retorna entendimento, resposta e confirmacoes.</p>
              <button
                type="button"
                onClick={onSend}
                disabled={isSending}
                className="rounded-full bg-accent-cyan px-5 py-3 text-sm font-semibold text-slate-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSending ? "Enviando..." : "Executar comando"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </Panel>
  );
}
