import type { HealthReport, SessionEvent } from "@/lib/api";
import { Panel } from "@/components/ui/panel";
import { Pill } from "@/components/ui/pill";

type EventRailProps = {
  health?: HealthReport;
  events: SessionEvent[];
  logs: string[];
};

export function EventRail({ health, events, logs }: EventRailProps) {
  return (
    <Panel tone="lime" className="p-6">
      <div className="flex flex-col gap-5">
        <div>
          <Pill label="telemetry" tone="lime" />
          <h2 className="mt-3 text-2xl font-semibold tracking-tight">Saude, eventos e logs</h2>
        </div>

        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-[22px] border border-white/8 bg-black/10 p-4">
            <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-muted">score</p>
            <p className="mt-3 text-3xl font-semibold text-accent-lime">{health?.score ?? "--"}</p>
          </div>
          <div className="rounded-[22px] border border-white/8 bg-black/10 p-4">
            <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-muted">status</p>
            <p className="mt-3 text-lg font-semibold text-white">{health?.status ?? "aguardando"}</p>
          </div>
          <div className="rounded-[22px] border border-white/8 bg-black/10 p-4">
            <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-muted">warnings</p>
            <p className="mt-3 text-3xl font-semibold text-accent-amber">{health?.warnings.length ?? 0}</p>
          </div>
        </div>

        <div className="grid gap-4 xl:grid-cols-[1.05fr_0.95fr]">
          <section className="rounded-[24px] border border-white/8 bg-bg/55 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-accent-lime">event bus</p>
              <span className="text-xs text-muted">{events.length} eventos</span>
            </div>
            <div className="mt-4 max-h-[19rem] space-y-3 overflow-y-auto pr-1">
              {events.length ? (
                events.map((event) => (
                  <article key={`${event.timestamp}-${event.kind}-${event.message}`} className="rounded-2xl border border-white/8 bg-white/5 p-3">
                    <div className="flex items-center justify-between gap-3 font-mono text-[11px] uppercase tracking-[0.2em] text-muted">
                      <span>{event.kind}</span>
                      <span>{event.timestamp}</span>
                    </div>
                    <p className="mt-2 text-sm text-slate-100">{event.message}</p>
                  </article>
                ))
              ) : (
                <p className="text-sm text-muted">Nenhum evento recente.</p>
              )}
            </div>
          </section>

          <section className="rounded-[24px] border border-white/8 bg-bg/55 p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-accent-sky">logs</p>
              <span className="text-xs text-muted">{logs.length} linhas</span>
            </div>
            <pre className="mt-4 max-h-[19rem] overflow-y-auto whitespace-pre-wrap rounded-2xl border border-white/8 bg-black/25 p-3 font-mono text-xs leading-6 text-slate-200">
              {logs.length ? logs.join("\n") : "Sem logs recentes."}
            </pre>
          </section>
        </div>
      </div>
    </Panel>
  );
}
