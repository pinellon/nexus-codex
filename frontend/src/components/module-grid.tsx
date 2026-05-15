import { motion } from "framer-motion";
import {
  Code2,
  Database,
  MessageSquare,
  MonitorSmartphone,
  Music4,
  ScanSearch,
  type LucideIcon,
} from "lucide-react";

import type { DashboardModule } from "@/lib/api";
import { Panel } from "@/components/ui/panel";
import { Pill } from "@/components/ui/pill";

type ModuleGridProps = {
  modules: DashboardModule[];
};

const iconMap: Record<string, LucideIcon> = {
  "code-2": Code2,
  database: Database,
  "message-square": MessageSquare,
  "monitor-smartphone": MonitorSmartphone,
  "music-4": Music4,
  "scan-search": ScanSearch,
};

export function ModuleGrid({ modules }: ModuleGridProps) {
  const groupedModules = modules.reduce<Record<string, DashboardModule[]>>((accumulator, module) => {
    const key = module.sector || "Outros";
    accumulator[key] = accumulator[key] ? [...accumulator[key], module] : [module];
    return accumulator;
  }, {});

  return (
    <Panel tone="amber" className="p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Pill label="setores do sistema" tone="amber" />
          <h2 className="mt-3 text-2xl font-semibold tracking-tight">Mapa organizado do NEXUS</h2>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            Cada bloco agora mostra o setor correto, o tipo da area e exemplos de comandos mais naturais.
          </p>
        </div>
        <div className="rounded-full border border-white/10 bg-white/5 px-3 py-2 font-mono text-xs uppercase tracking-[0.24em] text-muted">
          {modules.length} modulos
        </div>
      </div>

      <div className="mt-5 grid gap-6">
        {Object.entries(groupedModules).map(([sector, sectorModules]) => (
          <section key={sector} className="rounded-[28px] border border-white/8 bg-black/10 p-4 md:p-5">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-muted">{sector}</p>
                <h3 className="mt-2 text-xl font-semibold">{sectorModules.length === 1 ? "Area dedicada" : "Areas relacionadas"}</h3>
              </div>
              <div className="rounded-full border border-white/10 bg-white/5 px-3 py-2 text-xs text-muted">
                {sectorModules.length} bloco{sectorModules.length > 1 ? "s" : ""}
              </div>
            </div>

            <div className="mt-4 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
              {sectorModules.map((module, index) => {
                const Icon = iconMap[module.icon] ?? MessageSquare;

                return (
                  <motion.article
                    key={module.id}
                    initial={{ opacity: 0, y: 16 }}
                    whileInView={{ opacity: 1, y: 0 }}
                    viewport={{ once: true, amount: 0.2 }}
                    transition={{ delay: index * 0.05, duration: 0.28 }}
                    className="rounded-[24px] border border-white/8 bg-elevated/50 p-4"
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="min-w-0">
                        <div className="flex items-center gap-3">
                          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border border-white/10 bg-white/5">
                            <Icon className="h-5 w-5 text-slate-100" />
                          </span>
                          <div>
                            <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-muted">{module.id}</p>
                            <h4 className="mt-1 text-lg font-semibold">{module.title}</h4>
                          </div>
                        </div>
                      </div>
                      <Pill label={module.status} tone={module.tone} />
                    </div>
                    <p className="mt-3 text-sm leading-6 text-slate-200">{module.description}</p>

                    <div className="mt-4 flex flex-wrap gap-2">
                      {module.examples.map((example) => (
                        <span
                          key={example}
                          className="rounded-full border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-200"
                        >
                          {example}
                        </span>
                      ))}
                    </div>
                  </motion.article>
                );
              })}
            </div>
          </section>
        ))}
      </div>
    </Panel>
  );
}
