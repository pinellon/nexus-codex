import { useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import { Panel } from "@/components/ui/panel";
import { Pill } from "@/components/ui/pill";
import { normalizePreferredDeviceId, verifyMicrophoneAccess } from "@/lib/browser-audio";

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

type AudioDevice = {
  deviceId: string;
  kind: MediaDeviceKind;
  label: string;
};

type AudioStatusTone = "neutral" | "success" | "warning" | "danger";

type BrowserAudioSelectElement = HTMLAudioElement & {
  setSinkId?: (sinkId: string) => Promise<void>;
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

function statusClass(tone: AudioStatusTone) {
  if (tone === "success") {
    return "border-emerald-400/20 bg-emerald-400/10 text-emerald-200";
  }
  if (tone === "warning") {
    return "border-amber-400/20 bg-amber-400/10 text-amber-200";
  }
  if (tone === "danger") {
    return "border-rose-400/20 bg-rose-400/10 text-rose-200";
  }
  return "border-white/8 bg-white/[0.03] text-slate-300";
}

function deviceDisplayLabel(device: AudioDevice, index: number) {
  if (device.label.trim()) {
    return device.label.trim();
  }
  return `${device.kind === "audioinput" ? "Microfone" : "Saida"} ${index + 1}`;
}

export function SettingsForm({ initialSettings, isSaving, onSave }: SettingsFormProps) {
  const [form, setForm] = useState<Record<string, unknown>>(initialSettings);
  const [devices, setDevices] = useState<AudioDevice[]>([]);
  const [audioStatus, setAudioStatus] = useState<{ tone: AudioStatusTone; text: string }>({
    tone: "neutral",
    text: "Carregando dispositivos do navegador...",
  });
  const [isRefreshingDevices, setIsRefreshingDevices] = useState(false);
  const [isTestingInput, setIsTestingInput] = useState(false);
  const [isTestingOutput, setIsTestingOutput] = useState(false);
  const audioRef = useRef<BrowserAudioSelectElement | null>(null);

  useEffect(() => {
    setForm(initialSettings);
  }, [initialSettings]);

  const inputDevices = useMemo(() => devices.filter((device) => device.kind === "audioinput"), [devices]);
  const outputDevices = useMemo(() => devices.filter((device) => device.kind === "audiooutput"), [devices]);

  async function refreshDevices(requestPermission = false) {
    if (typeof navigator === "undefined" || !navigator.mediaDevices?.enumerateDevices) {
      setAudioStatus({
        tone: "danger",
        text: "Seu navegador nao oferece listagem de dispositivos de audio nesta interface.",
      });
      return;
    }

    setIsRefreshingDevices(true);
    try {
      if (requestPermission && navigator.mediaDevices.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach((track) => track.stop());
      }

      const listed = await navigator.mediaDevices.enumerateDevices();
      const nextDevices = listed
        .filter((device) => device.kind === "audioinput" || device.kind === "audiooutput")
        .map((device) => ({
          deviceId: device.deviceId,
          kind: device.kind,
          label: device.label || "",
        }));

      setDevices(nextDevices);

      if (!nextDevices.length) {
        setAudioStatus({
          tone: "warning",
          text: "Nenhum dispositivo de audio apareceu no navegador. Verifique permissoes do Windows e do browser.",
        });
        return;
      }

      const hasLabels = nextDevices.some((device) => device.label.trim());
      setAudioStatus({
        tone: hasLabels ? "success" : "warning",
        text: hasLabels
          ? "Dispositivos carregados. Escolha o microfone e a saida desejados abaixo."
          : "Os dispositivos apareceram sem nome. Clique em detectar dispositivos para liberar permissao do navegador.",
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Falha ao listar dispositivos.";
      setAudioStatus({
        tone: "danger",
        text: `Nao consegui acessar seus dispositivos de audio: ${message}`,
      });
    } finally {
      setIsRefreshingDevices(false);
    }
  }

  useEffect(() => {
    void refreshDevices(false);
  }, []);

  async function handleTestInput() {
    setIsTestingInput(true);
    try {
      const selectedDeviceId = normalizePreferredDeviceId(form.browser_voice_input_device);
      const probe = await verifyMicrophoneAccess(selectedDeviceId);
      setAudioStatus({
        tone: probe.ok ? "success" : "danger",
        text: probe.ok
          ? selectedDeviceId
            ? "Microfone selecionado acessado com sucesso. Se o Nexus ainda ouvir o dispositivo errado, defina esse mesmo microfone como padrao no navegador/Windows."
            : "Microfone padrao acessado com sucesso."
          : probe.message,
      });
    } finally {
      setIsTestingInput(false);
    }
  }

  async function handleTestOutput() {
    if (typeof window === "undefined") {
      return;
    }

    setIsTestingOutput(true);
    try {
      const AudioContextCtor = window.AudioContext || (window as typeof window & { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
      if (!AudioContextCtor) {
        setAudioStatus({
          tone: "danger",
          text: "Seu navegador nao oferece teste local de saida de audio nesta interface.",
        });
        return;
      }

      const selectedOutputId = normalizePreferredDeviceId(form.browser_voice_output_device);
      const audio = audioRef.current ?? new Audio();
      audioRef.current = audio;
      audio.muted = false;

      const context = new AudioContextCtor();
      const destination = context.createMediaStreamDestination();
      const gain = context.createGain();
      const oscillator = context.createOscillator();
      oscillator.type = "sine";
      oscillator.frequency.value = 660;
      gain.gain.value = 0.06;
      oscillator.connect(gain);
      gain.connect(destination);
      audio.srcObject = destination.stream;

      if (selectedOutputId && typeof audio.setSinkId === "function") {
        await audio.setSinkId(selectedOutputId);
      }

      await audio.play();
      oscillator.start();
      await new Promise((resolve) => window.setTimeout(resolve, 450));
      oscillator.stop();
      await new Promise((resolve) => window.setTimeout(resolve, 120));
      audio.pause();
      audio.srcObject = null;
      await context.close();

      setAudioStatus({
        tone: "success",
        text: selectedOutputId
          ? "Toque de teste enviado para a saida escolhida. A fala do navegador ainda pode seguir a saida padrao do sistema."
          : "Toque de teste reproduzido na saida padrao.",
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Falha ao testar a saida de audio.";
      setAudioStatus({
        tone: "danger",
        text: `Nao consegui testar a saida escolhida: ${message}`,
      });
    } finally {
      setIsTestingOutput(false);
    }
  }

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

        <Field label="backend input device" help="Indice do microfone usado pelo fallback local do backend. No seu PC, o fone Microfone Realtek estava como 1.">
          <input
            value={String(form.voice_input_device ?? "")}
            onChange={(event) => setForm((current) => ({ ...current, voice_input_device: event.target.value }))}
            placeholder="ex: 1"
            className="w-full rounded-2xl border border-white/8 bg-transparent px-4 py-3 text-sm text-white outline-none"
          />
        </Field>

        <Field label="backend output device" help="Indice da saida local preferida para engines desktop. No seu PC, Realtek 2nd output estava como 4.">
          <input
            value={String(form.voice_output_device ?? "")}
            onChange={(event) => setForm((current) => ({ ...current, voice_output_device: event.target.value }))}
            placeholder="ex: 4"
            className="w-full rounded-2xl border border-white/8 bg-transparent px-4 py-3 text-sm text-white outline-none"
          />
        </Field>

        <Field label="browser voice input" help="Microfone usado pelo navegador. O backend continua usando o indice local em voice input device.">
          <select
            value={String(form.browser_voice_input_device ?? "")}
            onChange={(event) => setForm((current) => ({ ...current, browser_voice_input_device: event.target.value }))}
            className="w-full rounded-2xl border border-white/8 bg-[#0c1422]/80 px-4 py-3 text-sm text-white outline-none"
          >
            <option value="">Microfone padrao do navegador</option>
            {inputDevices.map((device, index) => (
              <option key={`${device.deviceId}-${index}`} value={device.deviceId}>
                {deviceDisplayLabel(device, index)}
              </option>
            ))}
          </select>
        </Field>

        <Field label="browser voice output" help="Saida de audio usada pelos testes do navegador quando o browser permitir escolher o destino.">
          <select
            value={String(form.browser_voice_output_device ?? "")}
            onChange={(event) => setForm((current) => ({ ...current, browser_voice_output_device: event.target.value }))}
            className="w-full rounded-2xl border border-white/8 bg-[#0c1422]/80 px-4 py-3 text-sm text-white outline-none"
          >
            <option value="">Saida padrao do sistema</option>
            {outputDevices.map((device, index) => (
              <option key={`${device.deviceId}-${index}`} value={device.deviceId}>
                {deviceDisplayLabel(device, index)}
              </option>
            ))}
          </select>
        </Field>

        <Field label="professional voice" help="Provider principal da voz profissional usada pelo Modo Jarvis.">
          <select
            value={String(form.professional_voice_provider ?? "auto")}
            onChange={(event) => setForm((current) => ({ ...current, professional_voice_provider: event.target.value }))}
            className="w-full rounded-2xl border border-white/8 bg-[#0c1422]/80 px-4 py-3 text-sm text-white outline-none"
          >
            <option value="auto">Auto</option>
            <option value="openai">OpenAI TTS</option>
            <option value="elevenlabs">ElevenLabs</option>
            <option value="edge">Edge TTS</option>
            <option value="browser_fallback">Navegador</option>
          </select>
        </Field>

        <Field label="voice profile" help="Estilo de fala padrao para conversa natural.">
          <select
            value={String(form.professional_voice_profile ?? "jarvis")}
            onChange={(event) => setForm((current) => ({ ...current, professional_voice_profile: event.target.value }))}
            className="w-full rounded-2xl border border-white/8 bg-[#0c1422]/80 px-4 py-3 text-sm text-white outline-none"
          >
            <option value="jarvis">Jarvis</option>
            <option value="natural">Natural</option>
            <option value="professor">Professor</option>
            <option value="rapido">Rapido</option>
            <option value="calmo">Calmo</option>
          </select>
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

        <Field label="local api token" help="Protege rotas sensiveis da API web local via cabecalho X-NEXUS-TOKEN.">
          <input
            type="password"
            value={String(form.local_api_token ?? "")}
            onChange={(event) => setForm((current) => ({ ...current, local_api_token: event.target.value }))}
            className="w-full rounded-2xl border border-white/8 bg-transparent px-4 py-3 text-sm text-white outline-none"
          />
        </Field>
      </div>

      <div className="mt-4 rounded-[22px] border border-white/8 bg-black/10 p-4">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.28em] text-muted">browser audio</p>
            <p className="mt-2 max-w-3xl text-sm text-slate-300">
              Use esse painel para detectar dispositivos, validar o microfone escolhido e testar a saida. No modo web, o reconhecimento de voz do navegador costuma seguir o microfone padrao do browser ou do Windows, entao vale alinhar a selecao aqui com o dispositivo padrao do sistema.
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" className="shell-chip" disabled={isRefreshingDevices} onClick={() => void refreshDevices(true)}>
              {isRefreshingDevices ? "Detectando..." : "Detectar dispositivos"}
            </button>
            <button type="button" className="shell-chip" disabled={isTestingInput} onClick={() => void handleTestInput()}>
              {isTestingInput ? "Testando microfone..." : "Testar microfone"}
            </button>
            <button type="button" className="shell-chip" disabled={isTestingOutput} onClick={() => void handleTestOutput()}>
              {isTestingOutput ? "Testando saida..." : "Testar saida"}
            </button>
          </div>
        </div>

        <div className={`mt-4 rounded-2xl border px-4 py-3 text-sm ${statusClass(audioStatus.tone)}`}>
          {audioStatus.text}
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4 text-sm text-slate-300">
            <p className="text-white">Entradas detectadas: {inputDevices.length}</p>
            <p className="mt-2 text-slate-400">
              {inputDevices.length
                ? inputDevices.map((device, index) => deviceDisplayLabel(device, index)).slice(0, 3).join(" • ")
                : "Nenhum microfone apareceu ainda."}
            </p>
          </div>
          <div className="rounded-2xl border border-white/8 bg-white/[0.03] p-4 text-sm text-slate-300">
            <p className="text-white">Saidas detectadas: {outputDevices.length}</p>
            <p className="mt-2 text-slate-400">
              {outputDevices.length
                ? outputDevices.map((device, index) => deviceDisplayLabel(device, index)).slice(0, 3).join(" • ")
                : "Nenhuma saida apareceu ainda."}
            </p>
          </div>
        </div>
      </div>

      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {[
          ["ui_sounds", "UI sounds"],
          ["ui_animations", "UI animations"],
          ["obsidian_enabled", "Obsidian enabled"],
          ["mind_allow_autonomous", "Autonomous mind"],
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
