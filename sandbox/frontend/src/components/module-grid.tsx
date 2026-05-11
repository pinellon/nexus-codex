import { motion } from "framer-motion";

import type { DashboardModule } from "@/lib/api";
import { Panel } from "@/components/ui/panel";
import { Pill } from "@/components/ui/pill";

type ModuleGridProps = {
  modules: DashboardModule[];
};

export function ModuleGrid({ modules }: ModuleGridProps) {
  return (
    <Panel tone="amber" className="p-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <Pill label="module map" tone="amber" />
          <h2 className="mt-3 text-2xl font-semibold tracking-tight">Cobertura da interface nova</h2>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            Cada bloco representa uma superficie do projeto que pode ser migrada para a shell web.
          </p>
        </div>
        <div className="rounded-full border border-white/10 bg-white/5 px-3 py-2 font-mono text-xs uppercase tracking-[0.24em] text-muted">
          {modules.length} modulos
        </div>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {modules.map((module, index) => (
          <motion.article
            key={module.id}
            initial={{ opacity: 0, y: 16 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ delay: index * 0.05, duration: 0.28 }}
            className="rounded-[24px] border border-white/8 bg-elevated/50 p-4"
          >
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-muted">{module.id}</p>
                <h3 className="mt-2 text-lg font-semibold">{module.title}</h3>
              </div>
              <Pill label={module.status} tone={module.tone} />
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-200">{module.description}</p>
          </motion.article>
        ))}
      </div>
    </Panel>
  );
}
