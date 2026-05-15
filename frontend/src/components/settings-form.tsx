import { useEffect, useState, type ReactNode } from "react";

import { Panel } from "@/components/ui/panel";
import { Pill } from "@/components/ui/pill";

type SettingsFormProps = {
  initialSettings: Record<string, unknown>;
  isSaving: boolean;
  onSave: (nextSettings: Record<string, unknown>) => void;
};

type FieldProps = {
  label: string;
  help: string;
  children: ReactNode;
};

function Field({ label, help, children }: FieldProps) {
  return (
    <label className="block rounded-[22px] border border-white/8 bg-black/10 p-4">
      <span className="font-mono text-[11px] uppercase tracking-[0.28em] text-muted">{label}</span>
      <p className="mt-2 text-sm text-muted">{help}</p>
      <div className="mt-4">{children}</div>
    </label>
  );
}

export function SettingsForm({ initialSettings, isSaving, onSave }: SettingsFormProps) {
  const [form, setForm] = useState<Record<string, unknown>>(initialSettings);

  useEffect(() => {
    setForm(initialSettings);
  }, [initialSettings]);

  return (
    <Panel tone="sky" className="p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <Pill label="settings bridge" tone="sky" />
          <h2 className="mt-3 text-2xl font-semibold tracking-tight">Configuracoes vivas</h2>
          <p className="mt-2 max-w-2xl text-sm text-muted">
            Esse painel salva direto em `data/settings.json` usando a API nova.
          </p>
        </div>
        <button
          type="button"
          onClick={() => onSave(form)}
          disabled={isSaving}
          className="rounded-full bg-accent-sky px-5 py-3 text-sm font-semibold text-slate-950 transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSaving ? "Salvando..." : "Salvar"}
        </button>
      </div>

      <div className="mt-5 grid gap-4 md:grid-cols-2">
        <Field label="wake word" help="Palavra de ativacao usada pelo roteador de voz.">
          <input
            value={String(form.wake_word ?? "")}
            onChange={(event) => setForm((current) => ({ ...current, wake_word: event.target.value }))}
            className="w-full rounded-2xl border border-white/8 bg-transparent px-4 py-3 text-sm text-white outline-none"
          />
        </Field>

        <Field label="voice language" help="Idioma principal do loop de voz.">
          <input
            value={String(form.voice_language ?? "")}
            onChange={(event) => setForm((current) => ({ ...current, voice_language: event.target.value }))}
            className="w-full rounded-2xl border border-white/8 bg-transparent px-4 py-3 text-sm text-white outline-none"
          />
        </Field>

        <Field label="listen timeout" help="Segundos de espera antes de desistir de ouvir.">
          <input
            type="number"
            min={1}
            value={String(form.voice_listen_timeout ?? 5)}
            onChange={(event) =>
              setForm((current) => ({ ...current, voice_listen_timeout: Number(event.target.value || 5) }))
            }
            className="w-full rounded-2xl border border-white/8 bg-transparent px-4 py-3 text-sm text-white outline-none"
          />
        </Field>

        <Field label="phrase limit" help="Limite maximo de segundos por frase capturada.">
          <input
            type="number"
            min={1}
            value={String(form.voice_phrase_time_limit ?? 10)}
            onChange={(event) =>
              setForm((current) => ({ ...current, voice_phrase_time_limit: Number(event.target.value || 10) }))
            }
            className="w-full rounded-2xl border border-white/8 bg-transparent px-4 py-3 text-sm text-white outline-none"
          />
        </Field>

        <Field label="default media" help="Plataforma preferida para reproduzir musica.">
          <input
            value={String(form.default_media ?? "")}
            onChange={(event) => setForm((current) => ({ ...current, default_media: event.target.value }))}
            className="w-full rounded-2xl border border-white/8 bg-transparent px-4 py-3 text-sm text-white outline-none"
          />
        </Field>

        <Field label="obsidian path" help="Vault usado pela memoria contextual.">
          <input
            value={String(form.obsidian_vault_path ?? "")}
            onChange={(event) => setForm((current) => ({ ...current, obsidian_vault_path: event.target.value }))}
            className="w-full rounded-2xl border border-white/8 bg-transparent px-4 py-3 text-sm text-white outline-none"
          />
        </Field>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {[
          ["ui_sounds", "UI sounds"],
          ["ui_animations", "UI animations"],
          ["obsidian_enabled", "Obsidian enabled"],
          ["voice_confirm_commands", "Voice confirm"],
          ["voice_require_wake_word", "Wake word required"],
          ["speak_responses", "Speak responses"],
        ].map(([key, label]) => (
          <label key={key} className="flex items-center justify-between gap-4 rounded-[22px] border border-white/8 bg-black/10 px-4 py-4">
            <span className="text-sm text-slate-100">{label}</span>
            <input
              type="checkbox"
              checked={Boolean(form[key])}
              onChange={(event) => setForm((current) => ({ ...current, [key]: event.target.checked }))}
              className="h-4 w-4 accent-cyan-400"
            />
          </label>
        ))}
      </div>
    </Panel>
  );
}
