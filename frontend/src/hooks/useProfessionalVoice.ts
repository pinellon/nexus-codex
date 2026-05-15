import { useCallback, useEffect, useRef, useState } from "react";

import { apiBase, fetchVoiceChunks, fetchVoiceProfiles, fetchVoiceTestAudio, stopProfessionalVoice, type VoiceProfile } from "@/lib/api";

type SpeakOptions = {
  provider?: string;
  profile?: string;
  onGenerating?: () => void;
  onSpeaking?: () => void;
  onDone?: () => void;
  onError?: (message: string) => void;
};

function sanitizeForBrowserSpeech(text: string) {
  return (text || "")
    .replace(/```[\s\S]*?```/g, " codigo omitido ")
    .replace(/`([^`]+)`/g, "$1")
    .replace(/https?:\/\/\S+/g, "link")
    .replace(/R\$/g, " reais ")
    .replace(/[*_#>|~]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function browserSpeak(text: string, onDone?: () => void, onError?: (message: string) => void) {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) {
    onError?.("Seu navegador nao oferece fala local.");
    onDone?.();
    return;
  }
  const content = sanitizeForBrowserSpeech(text);
  if (!content) {
    onDone?.();
    return;
  }
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(content);
  const voices = window.speechSynthesis.getVoices();
  const voice = voices.find((item) => item.lang.toLowerCase().startsWith("pt-br")) ?? voices.find((item) => item.lang.toLowerCase().startsWith("pt"));
  if (voice) {
    utterance.voice = voice;
  }
  utterance.lang = "pt-BR";
  utterance.rate = 1;
  utterance.pitch = 1;
  utterance.onend = () => onDone?.();
  utterance.onerror = () => {
    onError?.("Nao consegui reproduzir a fala local.");
    onDone?.();
  };
  window.speechSynthesis.speak(utterance);
}

export function useProfessionalVoice(initial?: { provider?: string; profile?: string }) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentProvider, setCurrentProvider] = useState(initial?.provider || "auto");
  const [currentProfile, setCurrentProfile] = useState(initial?.profile || "jarvis");
  const [profiles, setProfiles] = useState<VoiceProfile[]>([]);
  const [error, setError] = useState("");
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const cancelledRef = useRef(false);
  const runIdRef = useRef(0);

  useEffect(() => {
    void fetchVoiceProfiles()
      .then((payload) => setProfiles(payload.profiles))
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    if (initial?.provider) {
      setCurrentProvider(initial.provider);
    }
    if (initial?.profile) {
      setCurrentProfile(initial.profile);
    }
  }, [initial?.profile, initial?.provider]);

  const stop = useCallback(() => {
    cancelledRef.current = true;
    runIdRef.current += 1;
    audioRef.current?.pause();
    audioRef.current = null;
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
    }
    setIsSpeaking(false);
    setIsGenerating(false);
    void stopProfessionalVoice().catch(() => undefined);
  }, []);

  const playAudioUrl = useCallback((url: string, runId: number) => {
    return new Promise<void>((resolve, reject) => {
      if (cancelledRef.current || runIdRef.current !== runId) {
        resolve();
        return;
      }
      const audio = new Audio(`${apiBase}${url}`);
      audioRef.current = audio;
      audio.onended = () => resolve();
      audio.onerror = () => reject(new Error("Falha ao reproduzir audio gerado."));
      void audio.play().catch(reject);
    });
  }, []);

  const speak = useCallback(
    async (text: string, options: SpeakOptions = {}) => {
      const content = text.trim();
      if (!content) {
        options.onDone?.();
        return false;
      }

      stop();
      cancelledRef.current = false;
      const runId = runIdRef.current + 1;
      runIdRef.current = runId;
      const provider = options.provider || currentProvider;
      const profile = options.profile || currentProfile;
      setError("");
      setIsGenerating(true);
      options.onGenerating?.();

      try {
        const payload = await fetchVoiceChunks({ text: content, provider, profile });
        if (cancelledRef.current || runIdRef.current !== runId) {
          return false;
        }
        setIsGenerating(false);
        setIsSpeaking(true);
        options.onSpeaking?.();
        for (const chunk of payload.chunks) {
          if (cancelledRef.current || runIdRef.current !== runId) {
            break;
          }
          await playAudioUrl(chunk.audio_url, runId);
          await new Promise((resolve) => window.setTimeout(resolve, 80));
        }
        setIsSpeaking(false);
        options.onDone?.();
        return true;
      } catch (caughtError) {
        const message = caughtError instanceof Error ? caughtError.message : "Falha ao gerar voz profissional.";
        setError(message);
        setIsGenerating(false);
        setIsSpeaking(true);
        options.onError?.(message);
        browserSpeak(
          content,
          () => {
            setIsSpeaking(false);
            options.onDone?.();
          },
          (fallbackMessage) => setError(fallbackMessage),
        );
        return false;
      }
    },
    [currentProfile, currentProvider, playAudioUrl, stop],
  );

  const testVoice = useCallback(
    async (options: { provider?: string; profile?: string } = {}) => {
      stop();
      const runId = runIdRef.current + 1;
      runIdRef.current = runId;
      setIsGenerating(true);
      try {
        const blob = await fetchVoiceTestAudio({
          provider: options.provider || currentProvider,
          profile: options.profile || currentProfile,
        });
        const url = URL.createObjectURL(blob);
        setIsGenerating(false);
        setIsSpeaking(true);
        await new Promise<void>((resolve, reject) => {
          const audio = new Audio(url);
          audioRef.current = audio;
          audio.onended = () => resolve();
          audio.onerror = () => reject(new Error("Falha ao tocar teste de voz."));
          void audio.play().catch(reject);
        });
        URL.revokeObjectURL(url);
        if (runIdRef.current === runId) {
          setIsSpeaking(false);
        }
      } catch (caughtError) {
        const message = caughtError instanceof Error ? caughtError.message : "Falha ao testar voz.";
        setError(message);
        setIsGenerating(false);
        setIsSpeaking(false);
      }
    },
    [currentProfile, currentProvider, stop],
  );

  return {
    isSpeaking,
    isGenerating,
    currentProvider,
    currentProfile,
    profiles,
    error,
    speak,
    stop,
    clearQueue: stop,
    testVoice,
    setProfile: setCurrentProfile,
    setProvider: setCurrentProvider,
  };
}

export type ProfessionalVoiceController = ReturnType<typeof useProfessionalVoice>;
