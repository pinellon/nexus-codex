import { useDeferredValue, useEffect, useState, useTransition } from "react";
import { Gauge, Sparkles, Waves } from "lucide-react";

import { ChatConsole, type ChatMessage } from "@/components/chat-console";
import { EventRail } from "@/components/event-rail";
import { ModuleGrid } from "@/components/module-grid";
import { SettingsForm } from "@/components/settings-form";
import { Panel } from "@/components/ui/panel";
import { Pill } from "@/components/ui/pill";
import {
  apiBase,
  fetchDashboard,
  fetchSettings,
  saveSettings,
  sendChat,
  type DashboardPayload,
  type SessionEvent,
} from "@/lib/api";

const quickActions = [
  "diagnostico do projeto",
  "ultimos eventos",
  "modo foco",
  "abrir VS Code",
  "descreve a tela",
  "status da casa",
];

const bootMessage: ChatMessage = {
  id: "boot",
  role: "assistant",
  content:
    "Shell web inicializada. O pipeline principal continua no backend Python e o desktop segue disponivel durante a migracao.",
  meta: "web/bootstrap",
};

function asMessageId() {
  return Math.random().toString(36).slice(2, 10);
}

function eventToSessionEvent(event: MessageEvent<string>): SessionEvent | null {
  try {
    const payload = JSON.parse(event.data) as {
      kind: string;
      message: string;
      data?: Record<string, unknown>;
    };

    return {
      timestamp: typeof payload.data?.timestamp === "string" ? payload.data.timestamp : new Date().toISOString(),
      kind: payload.kind,
      message: payload.message,
      data: payload.data ?? {},
    };
  } catch {
    return null;
  }
}

export default function App() {
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);
  const [settings, setSettings] = useState<Record<string, unknown>>({});
  const [messages, setMessages] = useState<ChatMessage[]>([bootMessage]);
  const [command, setCommand] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [pendingConfirmation, setPendingConfirmation] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isRefreshing, startTransition] = useTransition();
  const deferredLogs = useDeferredValue(dashboard?.logs ?? []);

  async function refreshDashboard() {
    const payload = await fetchDashboard();
    startTransition(() => {
      setDashboard(payload);
    });
  }

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      try {
        const [dashboardPayload, settingsPayload] = await Promise.all([fetchDashboard(), fetchSettings()]);
        if (!active) {
          return;
        }
        startTransition(() => {
          setDashboard(dashboardPayload);
        });
        setSettings(settingsPayload);
        setErrorMessage(null);
      } catch (error) {
        if (!active) {
          return;
        }
        setErrorMessage(error instanceof Error ? error.message : "Falha ao carregar a shell web.");
      }
    }

    void bootstrap();
    const intervalId = window.setInterval(() => {
      void refreshDashboard().catch((error: unknown) => {
        setErrorMessage(error instanceof Error ? error.message : "Falha ao atualizar o dashboard.");
      });
    }, 15000);

    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    const source = new EventSource(`${apiBase}/api/events/stream`);
    source.onmessage = (event) => {
      const nextEvent = eventToSessionEvent(event);
      if (!nextEvent) {
        return;
      }
      setDashboard((current) => {
        if (!current) {
          return current;
        }
        return {
          ...current,
          events: [nextEvent, ...current.events].slice(0, 40),
        };
      });
    };
    source.onerror = () => {
      source.close();
    };

    return () => {
      source.close();
    };
  }, []);

  async function executeCommand(text: string, confirm = false, echoUser = true) {
    const trimmed = text.trim();
    if (!trimmed) {
      return;
    }

    if (echoUser) {
      setMessages((current) => [
        ...current,
        {
          id: asMessageId(),
          role: "user",
          content: trimmed,
          meta: confirm ? "confirmed" : "draft",
        },
      ]);
    }

    setIsSending(true);
    try {
      const result = await sendChat(trimmed, confirm);
      setMessages((current) => [
        ...current,
        {
          id: asMessageId(),
          role: "assistant",
          content: result.response,
          meta: result.understood,
        },
      ]);
      setPendingConfirmation(result.confirmation_required ? trimmed : null);
      setErrorMessage(null);
      await refreshDashboard();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Falha ao enviar comando.";
      setMessages((current) => [
        ...current,
        {
          id: asMessageId(),
          role: "system",
          content: message,
          meta: "web/error",
        },
      ]);
      setErrorMessage(message);
    } finally {
      setIsSending(false);
    }
  }

  async function handleSend() {
    const nextCommand = command.trim();
    if (!nextCommand) {
      return;
    }
    setCommand("");
    await executeCommand(nextCommand);
  }

  async function handleConfirmPending() {
    if (!pendingConfirmation) {
      return;
    }
    const nextCommand = pendingConfirmation;
    setPendingConfirmation(null);
    await executeCommand(nextCommand, true, false);
  }

  async function handleSaveSettings(nextSettings: Record<string, unknown>) {
    setIsSaving(true);
    try {
      const saved = await saveSettings(nextSettings);
      setSettings(saved);
      setMessages((current) => [
        ...current,
        {
          id: asMessageId(),
          role: "system",
          content: "Configuracoes atualizadas com sucesso.",
          meta: "settings/save",
        },
      ]);
      setErrorMessage(null);
      await refreshDashboard();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Falha ao salvar configuracoes.";
      setErrorMessage(message);
      setMessages((current) => [
        ...current,
        {
          id: asMessageId(),
          role: "system",
          content: message,
          meta: "settings/error",
        },
      ]);
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-bg text-text">
      <div className="pointer-events-none absolute left-[8%] top-16 h-52 w-52 rounded-full bg-accent-cyan/10 blur-3xl" />
      <div className="pointer-events-none absolute right-[4%] top-28 h-64 w-64 rounded-full bg-accent-amber/10 blur-3xl" />

      <div className="mx-auto flex max-w-7xl flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
        <header className="grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
          <Panel tone="cyan" className="p-8">
            <div className="flex flex-wrap gap-2">
              <Pill label="magic ui base" tone="cyan" />
              <Pill label="react shell" tone="amber" />
              <Pill label="python api" tone="sky" />
            </div>

            <div className="mt-5 grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
              <div>
                <h1 className="max-w-3xl text-4xl font-semibold tracking-tight sm:text-5xl">
                  NEXUS command center para a migracao completa da interface.
                </h1>
                <p className="mt-4 max-w-2xl text-base leading-7 text-muted">
                  A interface desktop continua rodando, mas a nova shell web ja cobre chat, telemetria, logs, modulos e
                  configuracoes sobre o mesmo backend Python.
                </p>
              </div>

              <div className="grid gap-3">
                <div className="rounded-[24px] border border-white/8 bg-black/10 p-4">
                  <div className="flex items-center gap-3">
                    <Sparkles className="h-5 w-5 text-accent-cyan" />
                    <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-accent-cyan">surface</p>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-100">
                    Shell visual com linguagem mais forte, glow contido, contraste alto e ritmo de dashboard.
                  </p>
                </div>
                <div className="rounded-[24px] border border-white/8 bg-black/10 p-4">
                  <div className="flex items-center gap-3">
                    <Gauge className="h-5 w-5 text-accent-lime" />
                    <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-accent-lime">coverage</p>
                  </div>
                  <p className="mt-3 text-sm leading-6 text-slate-100">
                    Chat conectado, logs e eventos reais, settings persistentes e mapa dos modulos do projeto.
                  </p>
                </div>
              </div>
            </div>
          </Panel>

          <Panel tone="sky" className="p-6">
            <div className="flex items-center justify-between gap-4">
              <div>
                <Pill label="runtime" tone="sky" />
                <h2 className="mt-3 text-2xl font-semibold tracking-tight">Estado da shell</h2>
              </div>
              <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs text-muted">
                <Waves className="h-4 w-4 text-accent-sky" />
                {isRefreshing ? "Atualizando" : "Sincronizado"}
              </div>
            </div>

            <div className="mt-5 grid gap-3 sm:grid-cols-2">
              <div className="rounded-[22px] border border-white/8 bg-black/10 p-4">
                <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-muted">score</p>
                <p className="mt-2 text-3xl font-semibold text-accent-cyan">{dashboard?.health.score ?? "--"}</p>
              </div>
              <div className="rounded-[22px] border border-white/8 bg-black/10 p-4">
                <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-muted">events</p>
                <p className="mt-2 text-3xl font-semibold text-accent-amber">{dashboard?.events.length ?? 0}</p>
              </div>
              <div className="rounded-[22px] border border-white/8 bg-black/10 p-4 sm:col-span-2">
                <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-muted">project root</p>
                <p className="mt-2 break-all text-sm leading-6 text-slate-100">{dashboard?.project_root ?? "carregando..."}</p>
              </div>
            </div>

            {errorMessage ? (
              <div className="mt-4 rounded-[22px] border border-accent-rose/30 bg-accent-rose/10 p-4 text-sm text-accent-rose">
                {errorMessage}
              </div>
            ) : null}
          </Panel>
        </header>

        <main className="grid gap-6 xl:grid-cols-[1.08fr_0.92fr]">
          <div className="flex flex-col gap-6">
            <ChatConsole
              command={command}
              isSending={isSending}
              messages={messages}
              pendingConfirmation={pendingConfirmation}
              quickActions={quickActions}
              onChange={setCommand}
              onSend={() => {
                void handleSend();
              }}
              onQuickAction={(value) => {
                setCommand(value);
                void executeCommand(value);
              }}
              onConfirmPending={() => {
                void handleConfirmPending();
              }}
            />
            <ModuleGrid modules={dashboard?.modules ?? []} />
          </div>

          <div className="flex flex-col gap-6">
            <EventRail health={dashboard?.health} events={dashboard?.events ?? []} logs={deferredLogs} />
            <SettingsForm
              initialSettings={settings}
              isSaving={isSaving}
              onSave={(nextSettings) => {
                void handleSaveSettings(nextSettings);
              }}
            />
          </div>
        </main>
      </div>
    </div>
  );
}
