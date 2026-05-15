export type BrowserAudioProbeResult = {
  ok: boolean;
  message: string;
};

function stopStream(stream: MediaStream) {
  stream.getTracks().forEach((track) => track.stop());
}

export function normalizePreferredDeviceId(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

export function describeMicrophoneError(error: unknown, hasPreferredDevice: boolean) {
  const name = typeof error === "object" && error && "name" in error ? String((error as { name?: string }).name || "") : "";
  if (name === "NotAllowedError" || name === "SecurityError") {
    return "Permissao de microfone negada no navegador.";
  }
  if (name === "NotFoundError") {
    return hasPreferredDevice
      ? "Nao encontrei o microfone selecionado nas configuracoes."
      : "Nao encontrei nenhum microfone disponivel neste navegador.";
  }
  if (name === "OverconstrainedError") {
    return "O microfone escolhido nao esta mais disponivel. Escolha outro dispositivo nas configuracoes.";
  }
  if (name === "NotReadableError") {
    return "Seu microfone existe, mas esta ocupado por outro app ou bloqueado pelo sistema.";
  }
  return hasPreferredDevice
    ? "Nao consegui abrir o microfone selecionado nas configuracoes."
    : "Nao consegui abrir o microfone neste navegador.";
}

export async function verifyMicrophoneAccess(preferredInputDeviceId?: string): Promise<BrowserAudioProbeResult> {
  if (typeof navigator === "undefined" || !navigator.mediaDevices?.getUserMedia) {
    return {
      ok: false,
      message: "Seu navegador nao oferece acesso direto ao microfone nesta interface.",
    };
  }

  const preferred = normalizePreferredDeviceId(preferredInputDeviceId);
  try {
    const stream = await navigator.mediaDevices.getUserMedia(
      preferred
        ? {
            audio: {
              deviceId: { exact: preferred },
            },
          }
        : { audio: true },
    );
    stopStream(stream);
    return {
      ok: true,
      message: preferred ? "Microfone selecionado validado com sucesso." : "Microfone validado com sucesso.",
    };
  } catch (error) {
    return {
      ok: false,
      message: describeMicrophoneError(error, Boolean(preferred)),
    };
  }
}
