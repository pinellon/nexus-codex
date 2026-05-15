import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  CircleDashed,
  ClipboardCheck,
  Headphones,
  RefreshCcw,
  Settings,
  ShieldCheck,
  Stethoscope,
  TerminalSquare,
  XCircle,
} from "lucide-react";

import type { DashboardModule, DashboardPayload, RuntimeStatus } from "@/lib/api";

type DoctorViewProps = {
  dashboard: DashboardPayload | null;
  runtimeStatus: RuntimeStatus | null;
  settings: Record<string, unknown>;
  onOpenSettings: () => void;
  onRefresh: () => void;
  onTestVoice: () => void;
  onOpenLogs: () => void;
  onOpenFinance: () => void;
  onOpenConversation: () => void;
};

type StatusTone = "success" | "warning" | "danger" | "neutral";

const PRODUCTION_ITEMS = [
  "Instalacao facil criada",
  "Token local configurado",
  "Voz testada",
  "Obsidian conectado",
  "Financeiro funcional",
  "Modo conversa funcional",
  "Logs ativos",
  "README profissional",
  "Build do frontend passando",
  "Testes do backend passando",
];

function statusTone(status: string, configured?: boolean): StatusTone {
  const normalized = status.toLowerCase();
  if (normalized === "online" || normalized === "ready" || normalized === "ok") {
    return "success";
  }
  if (normalized === "offline" || normalized === "error" || configured === false) {
    return "danger";
  }
  if (["partial", "guarded", "paused", "blocked"].includes(normalized)) {
    return "warning";
  }
  return "neutral";
}

function toneClasses(tone: StatusTone) {
  if (tone === "success") {
    return {
      border: "border-emerald-400/20",
      bg: "bg-emerald-400/10",
      text: "text-emerald-200",
      icon: CheckCircle2,
    };
  }
  if (tone === "warning") {
    return {
      border: "border-amber-400/20",
      bg: "bg-amber-400/10",
      text: "text-amber-200",
      icon: AlertTriangle,
    };
  }
  if (tone === "danger") {
    return {
      border: "border-rose-400/20",
      bg: "bg-rose-400/10",
      text: "text-rose-200",
      icon: XCircle,
    };
  }
  return {
    border: "border-white/10",
    bg: "bg-white/[0.04]",
    text: "text-slate-300",
    icon: CircleDashed,
  };
}

function formatPercent(value: number | undefined | null) {
  return `${Math.round(Number(value || 0))}%`;
}

function buildProblems(dashboard: DashboardPayload | null) {
  if (!dashboard) {
    return ["Dashboard ainda nao carregado."];
  }

  const problems = new Set<string>();
  dashboard.health.missing.forEach((item) => problems.add(item));
  dashboard.health.warnings.forEach((item) => problems.add(item));

  dashboard.modules.forEach((module) => {
    const tone = statusTone(module.status, module.configured);
    if (tone === "danger" || tone === "warning") {
      problems.add(`${module.title}: ${module.detail}`);
    }
  });

  if (!problems.size) {
    problems.add("Nenhuma pendencia critica encontrada agora.");
  }
  return Array.from(problems).slice(0, 10);
}

function productionReady(label: string, dashboard: DashboardPayload | null, settings: Record<string, unknown>) {
  const modules = dashboard?.modules ?? [];
  const byId = new Map(modules.map((module) => [module.id, module]));
  if (label === "Token local configurado") {
    return Boolean(String(settings.local_api_token ?? "").trim());
  }
  if (label === "Obsidian conectado") {
    return Boolean(byId.get("memory")?.configured);
  }
  if (label === "Financeiro funcional") {
    return true;
  }
  if (label === "Modo conversa funcional") {
    return Boolean(byId.get("chat")?.configured || byId.get("voice")?.status === "online");
  }
  if (label === "Logs ativos") {
    return Boolean(dashboard?.events?.length || dashboard?.logs?.length);
  }
  if (label === "Build do frontend passando" || label === "Testes do backend passando") {
    return Number(dashboard?.health.score ?? 0) >= 70;
  }
  return false;
}

function ModuleStatusCard({ module }: { module: DashboardModule }) {
  const tone = statusTone(module.status, module.configured);
  const classes = toneClasses(tone);
  const Icon = classes.icon;

  return (
    <article className="rounded-2xl border border-white/10 bg-white/[0.04] p-5 shadow-2xl shadow-black/10 backdrop-blur-xl">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="font-mono text-[11px] uppercase tracking-[0.24em] text-slate-500">{module.sector}</p>
          <h3 className="mt-2 text-base font-semibold text-white">{module.title}</h3>
          <p className="mt-2 text-sm leading-6 text-slate-400">{module.description}</p>
        </div>
        <span className={`inline-flex shrink-0 items-center gap-2 rounded-full border px-3 py-1 text-xs ${classes.border} ${classes.bg} ${classes.text}`}>
          <Icon className="h-4 w-4" />
          {module.status}
        </span>
      </div>

      <div className="mt-4 space-y-3 text-sm leading-6">
        <p className="text-slate-300">{module.detail}</p>
        <p className="text-slate-500">Permissao: {module.permission}</p>
      </div>

      <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
        <span className={`rounded-full border px-3 py-1 text-xs ${module.configured ? "border-emerald-400/20 bg-emerald-400/10 text-emerald-200" : "border-amber-400/20 bg-amber-400/10 text-amber-200"}`}>
          {module.configured ? "Configurado" : "Pendente"}
        </span>
        <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-slate-300">
          {module.action_label}
        </span>
      </div>
    </article>
  );
}

export function DoctorView({
  dashboard,
  runtimeStatus,
  settings,
  onOpenSettings,
  onRefresh,
  onTestVoice,
  onOpenLogs,
  onOpenFinance,
  onOpenConversation,
}: DoctorViewProps) {
  const modules = dashboard?.modules ?? [];
  const configuredCount = modules.filter((module) => module.configured).length;
  const pendingCount = Math.max(0, modules.length - configuredCount);
  const problems = buildProblems(dashboard);
  const productionDone = PRODUCTION_ITEMS.filter((item) => productionReady(item, dashboard, settings)).length;

  if (!dashboard) {
    return (
      <section className="space-y-6 px-4 py-8 lg:px-12">
        <div className="rounded-[28px] border border-white/10 bg-white/[0.04] p-8 text-center shadow-2xl shadow-black/20 backdrop-blur-xl">
          <Stethoscope className="mx-auto h-10 w-10 text-cyan-300" />
          <h2 className="mt-4 text-2xl font-semibold text-white">Nexus Doctor</h2>
          <p className="mt-3 text-sm leading-7 text-slate-400">Carregando diagnostico do sistema.</p>
          <button type="button" className="shell-primary-button mx-auto mt-6" onClick={onRefresh}>
            <RefreshCcw className="h-4 w-4" />
            Atualizar
          </button>
        </div>
      </section>
    );
  }

  return (
    <section className="space-y-6 px-4 py-8 lg:px-12">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="shell-eyebrow text-cyan-300">Nexus Doctor</p>
          <h2 className="mt-2 text-3xl font-semibold tracking-tight text-white">Diagnostico do sistema</h2>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-slate-400">
            Saude, modulos, permissoes e prontidao para uso diario ou demonstracao.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="shell-chip" onClick={onRefresh}>
            <RefreshCcw className="h-4 w-4" />
            Atualizar diagnostico
          </button>
          <button type="button" className="shell-primary-button" onClick={onOpenSettings}>
            <Settings className="h-4 w-4" />
            Abrir configuracoes
          </button>
        </div>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <div className="rounded-[28px] border border-white/10 bg-white/[0.04] p-6 shadow-2xl shadow-black/20 backdrop-blur-xl">
          <div className="flex flex-wrap items-center justify-between gap-6">
            <div>
              <p className="shell-eyebrow">saude geral</p>
              <div className="mt-3 flex items-end gap-3">
                <span className="text-6xl font-semibold tracking-tight text-white">{formatPercent(dashboard.health.score)}</span>
                <span className="mb-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-sm text-cyan-200">
                  {dashboard.health.status}
                </span>
              </div>
            </div>
            <ShieldCheck className="h-16 w-16 text-cyan-300/80" />
          </div>

          <div className="mt-6 grid gap-3 md:grid-cols-5">
            {[
              ["Configurados", configuredCount],
              ["Pendentes", pendingCount],
              ["CPU", formatPercent(runtimeStatus?.cpu)],
              ["RAM", formatPercent(runtimeStatus?.ram)],
              ["Disco", formatPercent(runtimeStatus?.disk)],
            ].map(([label, value]) => (
              <div key={label} className="rounded-2xl border border-white/10 bg-black/10 p-4">
                <p className="shell-eyebrow">{label}</p>
                <p className="mt-2 text-2xl font-semibold text-white">{value}</p>
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-[28px] border border-white/10 bg-white/[0.04] p-6 shadow-2xl shadow-black/20 backdrop-blur-xl">
          <p className="shell-eyebrow text-amber-300">problemas encontrados</p>
          <div className="mt-4 space-y-3">
            {problems.map((problem) => (
              <div key={problem} className="flex gap-3 rounded-2xl border border-white/10 bg-black/10 p-3 text-sm leading-6 text-slate-300">
                <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-300" />
                <span>{problem}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid gap-3 md:grid-cols-3 xl:grid-cols-6">
        <button type="button" className="shell-chip justify-center" onClick={onTestVoice}>
          <Headphones className="h-4 w-4" />
          Testar voz
        </button>
        <button type="button" className="shell-chip justify-center" onClick={onOpenConversation}>
          <Activity className="h-4 w-4" />
          Conversa natural
        </button>
        <button type="button" className="shell-chip justify-center" onClick={onOpenLogs}>
          <TerminalSquare className="h-4 w-4" />
          Abrir logs
        </button>
        <button type="button" className="shell-chip justify-center" onClick={onOpenFinance}>
          <ClipboardCheck className="h-4 w-4" />
          Financeiro
        </button>
        <button type="button" className="shell-chip justify-center" onClick={onOpenSettings}>
          <Settings className="h-4 w-4" />
          Configuracoes
        </button>
        <button type="button" className="shell-chip justify-center" onClick={onRefresh}>
          <RefreshCcw className="h-4 w-4" />
          Revalidar
        </button>
      </div>

      <div className="grid gap-4 xl:grid-cols-[1fr_360px]">
        <div>
          <div className="mb-4 flex items-center justify-between gap-4">
            <h3 className="text-xl font-semibold text-white">Checklist de modulos</h3>
            <span className="text-sm text-slate-400">{modules.length} modulos monitorados</span>
          </div>
          <div className="grid gap-4 2xl:grid-cols-2">
            {modules.map((module) => (
              <ModuleStatusCard key={module.id} module={module} />
            ))}
          </div>
        </div>

        <aside className="rounded-[28px] border border-white/10 bg-white/[0.04] p-6 shadow-2xl shadow-black/20 backdrop-blur-xl">
          <p className="shell-eyebrow text-emerald-300">venda / producao</p>
          <h3 className="mt-3 text-xl font-semibold text-white">
            {productionDone}/{PRODUCTION_ITEMS.length} prontos
          </h3>
          <div className="mt-5 space-y-3">
            {PRODUCTION_ITEMS.map((item) => {
              const ready = productionReady(item, dashboard, settings);
              return (
                <div key={item} className="flex items-center gap-3 text-sm text-slate-300">
                  {ready ? <CheckCircle2 className="h-4 w-4 text-emerald-300" /> : <CircleDashed className="h-4 w-4 text-slate-500" />}
                  <span>{item}</span>
                </div>
              );
            })}
          </div>
        </aside>
      </div>
    </section>
  );
}
