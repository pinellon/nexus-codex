import { Square, Volume2 } from "lucide-react";

import type { ProfessionalVoiceController } from "@/hooks/useProfessionalVoice";

const PROVIDERS = [
  { id: "auto", label: "Auto" },
  { id: "openai", label: "OpenAI TTS" },
  { id: "elevenlabs", label: "ElevenLabs" },
  { id: "edge", label: "Edge TTS" },
  { id: "browser_fallback", label: "Navegador" },
];

export function VoiceSettingsPanel({ voice }: { voice: ProfessionalVoiceController }) {
  const status = voice.isGenerating ? "Gerando audio" : voice.isSpeaking ? "Falando" : voice.error ? "Erro" : "Pronto";

  return (
    <div className="rounded-[22px] border border-white/8 bg-black/10 p-4">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-muted">voz profissional</p>
          <p className="mt-2 text-sm leading-6 text-slate-300">
            Perfil, provedor e teste da fala usada pelo Modo Jarvis.
          </p>
        </div>
        <div className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1 text-xs text-slate-300">{status}</div>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <label className="block">
          <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">perfil</span>
          <select
            value={voice.currentProfile}
            onChange={(event) => voice.setProfile(event.target.value)}
            className="mt-2 w-full rounded-2xl border border-white/8 bg-[#0c1422]/80 px-4 py-3 text-sm text-white outline-none"
          >
            {voice.profiles.length ? (
              voice.profiles.map((profile) => (
                <option key={profile.id} value={profile.id}>
                  {profile.label}
                </option>
              ))
            ) : (
              <>
                <option value="jarvis">Jarvis</option>
                <option value="natural">Natural</option>
                <option value="professor">Professor</option>
                <option value="rapido">Rapido</option>
                <option value="calmo">Calmo</option>
              </>
            )}
          </select>
        </label>

        <label className="block">
          <span className="font-mono text-[10px] uppercase tracking-[0.22em] text-slate-500">provider</span>
          <select
            value={voice.currentProvider}
            onChange={(event) => voice.setProvider(event.target.value)}
            className="mt-2 w-full rounded-2xl border border-white/8 bg-[#0c1422]/80 px-4 py-3 text-sm text-white outline-none"
          >
            {PROVIDERS.map((provider) => (
              <option key={provider.id} value={provider.id}>
                {provider.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      <div className="mt-4 flex flex-wrap gap-2">
        <button
          type="button"
          className="shell-chip"
          disabled={voice.isGenerating || voice.isSpeaking}
          onClick={() => void voice.testVoice()}
        >
          <Volume2 className="h-4 w-4" />
          Testar voz
        </button>
        <button type="button" className="shell-chip" disabled={!voice.isGenerating && !voice.isSpeaking} onClick={voice.stop}>
          <Square className="h-4 w-4" />
          Parar voz
        </button>
      </div>

      {voice.error ? (
        <div className="mt-4 rounded-2xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-200">
          {voice.error}
        </div>
      ) : null}
    </div>
  );
}
