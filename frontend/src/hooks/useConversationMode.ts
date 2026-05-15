import { useEffect, useMemo, useRef, useState } from "react";

import {
  fetchConversationState,
  listenVoiceOnce,
  resetConversationSession,
  saveConversationNote,
  sendConversationMessage,
  type ConversationMessageResponse,
  type ConversationSession,
  type ConversationState,
} from "@/lib/api";
import { normalizePreferredDeviceId, verifyMicrophoneAccess } from "@/lib/browser-audio";
import { useProfessionalVoice } from "@/hooks/useProfessionalVoice";

export type OrbState = ConversationState;

type BrowserSpeechRecognitionAlternative = {
  transcript: string;
};

type BrowserSpeechRecognitionResult = {
  0: BrowserSpeechRecognitionAlternative;
  isFinal: boolean;
  length: number;
};

type BrowserSpeechRecognitionEvent = {
  resultIndex: number;
  results: ArrayLike<BrowserSpeechRecognitionResult>;
};

type BrowserSpeechRecognitionErrorEvent = {
  error: string;
};

type BrowserSpeechRecognitionInstance = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  onstart: (() => void) | null;
  onresult: ((event: BrowserSpeechRecognitionEvent) => void) | null;
  onerror: ((event: BrowserSpeechRecognitionErrorEvent) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};

type BrowserSpeechRecognitionConstructor = new () => BrowserSpeechRecognitionInstance;

function resolveSpeechRecognitionConstructor(): BrowserSpeechRecognitionConstructor | null {
  if (typeof window === "undefined") {
    return null;
  }
  const speechWindow = window as typeof window & {
    SpeechRecognition?: BrowserSpeechRecognitionConstructor;
    webkitSpeechRecognition?: BrowserSpeechRecognitionConstructor;
  };
  return speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition ?? null;
}

function normalizeTranscript(text: string) {
  return (text || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

function defaultNoteTitle(session: ConversationSession | null, fallback = "Resumo de conversa") {
  if (session?.current_topic?.trim()) {
    return `Resumo de ${session.current_topic.trim()}`;
  }
  return fallback;
}

type UseConversationModeOptions = {
  preferredInputDeviceId?: string;
  voiceProvider?: string;
  voiceProfile?: string;
};

export function useConversationMode(options: UseConversationModeOptions = {}) {
  const [active, setActive] = useState(false);
  const [state, setState] = useState<ConversationState>("idle");
  const [transcript, setTranscript] = useState("");
  const [lastResponse, setLastResponse] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [studyMode, setStudyMode] = useState(true);
  const [error, setError] = useState("");
  const [session, setSession] = useState<ConversationSession | null>(null);
  const [intent, setIntent] = useState("general_chat");
  const [topic, setTopic] = useState("");
  const [savedNotePath, setSavedNotePath] = useState<string | null>(null);
  const [speakingLevel, setSpeakingLevel] = useState(0);

  const recognitionCtor = useMemo(() => resolveSpeechRecognitionConstructor(), []);
  const recognitionRef = useRef<BrowserSpeechRecognitionInstance | null>(null);
  const restartTimerRef = useRef<number | null>(null);
  const requestRef = useRef(false);
  const ignoreRecognitionEndRef = useRef(false);
  const speakingMeterTimerRef = useRef<number | null>(null);
  const activeRef = useRef(active);
  const pausedRef = useRef(false);
  const speakingRef = useRef(false);
  const sessionIdRef = useRef(sessionId);
  const studyModeRef = useRef(studyMode);
  const mountedRef = useRef(true);
  const lastSubmittedRef = useRef("");
  const transcriptRef = useRef("");
  const microphoneReadyRef = useRef(false);
  const preferredInputDeviceId = normalizePreferredDeviceId(options.preferredInputDeviceId);
  const professionalVoice = useProfessionalVoice({
    provider: options.voiceProvider || "auto",
    profile: options.voiceProfile || "jarvis",
  });

  useEffect(() => {
    activeRef.current = active;
  }, [active]);

  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  useEffect(() => {
    studyModeRef.current = studyMode;
  }, [studyMode]);

  useEffect(() => {
    transcriptRef.current = transcript;
  }, [transcript]);

  useEffect(() => {
    microphoneReadyRef.current = false;
  }, [preferredInputDeviceId]);

  useEffect(() => {
    mountedRef.current = true;
    void fetchConversationState()
      .then((payload) => {
        if (!mountedRef.current || !payload.session) {
          return;
        }
        setSession(payload.session);
        setSessionId(payload.session.session_id);
        setStudyMode(payload.session.study_mode_enabled);
      })
      .catch(() => undefined);

    return () => {
      mountedRef.current = false;
      clearRestartTimer();
      clearSpeakingMeter();
      stopRecognition(true);
      professionalVoice.stop();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const voiceSupported = true;

  function clearRestartTimer() {
    if (restartTimerRef.current !== null) {
      window.clearTimeout(restartTimerRef.current);
      restartTimerRef.current = null;
    }
  }

  function clearSpeakingMeter() {
    if (speakingMeterTimerRef.current !== null) {
      window.clearInterval(speakingMeterTimerRef.current);
      speakingMeterTimerRef.current = null;
    }
    setSpeakingLevel(0);
  }

  function stopRecognition(forceAbort = false) {
    clearRestartTimer();
    ignoreRecognitionEndRef.current = true;
    if (forceAbort) {
      recognitionRef.current?.abort();
    } else {
      recognitionRef.current?.stop();
    }
    recognitionRef.current = null;
  }

  function cancelSpeech() {
    professionalVoice.stop();
    speakingRef.current = false;
    clearSpeakingMeter();
  }

  function scheduleListening(delay = 180) {
    if (!activeRef.current || pausedRef.current || requestRef.current || speakingRef.current) {
      return;
    }
    clearRestartTimer();
    restartTimerRef.current = window.setTimeout(() => {
      restartTimerRef.current = null;
      void beginListening();
    }, delay);
  }

  function startSpeakingMeter() {
    clearSpeakingMeter();
    setSpeakingLevel(0.5);
    speakingMeterTimerRef.current = window.setInterval(() => {
      setSpeakingLevel(0.35 + Math.random() * 0.65);
    }, 180);
  }

  function setConversationState(nextState: ConversationState) {
    setState(nextState);
  }

  async function speakResponse(text: string) {
    const content = text.trim();
    if (!content) {
      setConversationState("ready");
      scheduleListening(180);
      return;
    }

    cancelSpeech();
    speakingRef.current = true;
    startSpeakingMeter();
    await professionalVoice.speak(content, {
      onGenerating: () => setConversationState("generating_audio"),
      onSpeaking: () => setConversationState("speaking"),
      onDone: () => {
        speakingRef.current = false;
        clearSpeakingMeter();
        setConversationState("ready");
        scheduleListening(220);
      },
      onError: (message) => {
        setError(message);
      },
    });
  }

  async function handleConversationResponse(payload: ConversationMessageResponse) {
    setSessionId(payload.session_id);
    setSession(payload.session);
    setStudyMode(payload.session.study_mode_enabled);
    setIntent(payload.intent);
    setTopic(payload.topic);
    setLastResponse(payload.response);
    setSavedNotePath(payload.saved_note_path);
    setError(payload.ok ? "" : payload.response);

    if (payload.should_speak) {
      await speakResponse(payload.response);
      return;
    }

    setConversationState(payload.state);
    if (payload.state === "ready") {
      scheduleListening(180);
    }
  }

  async function sendText(text: string, options: { saveToObsidian?: boolean } = {}) {
    const cleaned = text.trim();
    if (!cleaned) {
      setError("Diga ou escreva algo para continuar.");
      setConversationState("error");
      return null;
    }

    stopRecognition(true);
    cancelSpeech();
    requestRef.current = true;
    setTranscript(cleaned);
    transcriptRef.current = cleaned;
    setConversationState("thinking");
    setError("");
    setSavedNotePath(null);

    try {
      const payload = await sendConversationMessage({
        text: cleaned,
        session_id: sessionIdRef.current || undefined,
        study_mode: studyModeRef.current,
        save_to_obsidian: options.saveToObsidian ?? false,
      });
      lastSubmittedRef.current = normalizeTranscript(cleaned);
      await handleConversationResponse(payload);
      return payload;
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "Falha ao falar com o modo conversa.";
      setError(message);
      setConversationState("error");
      scheduleListening(500);
      return null;
    } finally {
      requestRef.current = false;
    }
  }

  async function beginSystemListening() {
    if (!activeRef.current || pausedRef.current || requestRef.current || speakingRef.current || recognitionRef.current) {
      return;
    }

    requestRef.current = true;
    setConversationState("listening");
    setError("");
    try {
      const payload = await listenVoiceOnce({
        timeout: 5,
        phrase_time_limit: 8,
      });
      if (!payload.ok) {
        setError(payload.error || "Nao consegui ouvir pelo microfone do sistema.");
        setConversationState("error");
        scheduleListening(650);
        return;
      }

      const heard = (payload.text || "").trim();
      if (!heard) {
        setConversationState("ready");
        scheduleListening(220);
        return;
      }

      setTranscript(heard);
      transcriptRef.current = heard;
      requestRef.current = false;
      await sendText(heard);
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "Falha ao ouvir pelo microfone do sistema.";
      setError(message);
      setConversationState("error");
      scheduleListening(650);
    } finally {
      requestRef.current = false;
    }
  }

  async function beginListening() {
    const Recognition = recognitionCtor;
    if (!Recognition) {
      await beginSystemListening();
      return;
    }
    if (!microphoneReadyRef.current) {
      const probe = await verifyMicrophoneAccess(preferredInputDeviceId);
      if (!probe.ok) {
        await beginSystemListening();
        return;
      }
      microphoneReadyRef.current = true;
    }
    if (!activeRef.current || pausedRef.current || requestRef.current || speakingRef.current || recognitionRef.current) {
      return;
    }

    clearRestartTimer();
    const recognition = new Recognition();
    let finalTranscript = "";
    recognition.lang = "pt-BR";
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    recognitionRef.current = recognition;
    ignoreRecognitionEndRef.current = false;

    recognition.onstart = () => {
      setConversationState("listening");
      setError("");
    };

    recognition.onresult = (event) => {
      const parts: string[] = [];
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index];
        const currentText = result?.[0]?.transcript ?? "";
        if (currentText.trim()) {
          parts.push(currentText.trim());
          if (result.isFinal) {
            finalTranscript = `${finalTranscript} ${currentText}`.trim();
          }
        }
      }
      const merged = (finalTranscript || parts.join(" ")).trim();
      if (merged) {
        transcriptRef.current = merged;
        setTranscript(merged);
      }
    };

    recognition.onerror = (event) => {
      recognitionRef.current = null;
      if (event.error === "aborted") {
        return;
      }
      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        microphoneReadyRef.current = false;
        void beginSystemListening();
        return;
      }
      if (event.error === "audio-capture") {
        microphoneReadyRef.current = false;
        void beginSystemListening();
        return;
      }
      if (event.error !== "no-speech") {
        setError("Nao consegui ouvir voce agora.");
        setConversationState("error");
      }
      scheduleListening(420);
    };

    recognition.onend = () => {
      recognitionRef.current = null;
      if (ignoreRecognitionEndRef.current) {
        ignoreRecognitionEndRef.current = false;
        return;
      }
      const merged = finalTranscript.trim() || transcriptRef.current.trim();
      if (!merged) {
        scheduleListening(220);
        return;
      }
      const normalized = normalizeTranscript(merged);
      if (normalized && normalized === lastSubmittedRef.current) {
        scheduleListening(250);
        return;
      }
      void sendText(merged);
    };

    recognition.start();
  }

  async function startConversation() {
    setActive(true);
    activeRef.current = true;
    pausedRef.current = false;
    setError("");
    setConversationState("ready");
    await beginListening();
  }

  function stopConversation() {
    activeRef.current = false;
    pausedRef.current = false;
    setActive(false);
    stopRecognition(true);
    cancelSpeech();
    setConversationState("idle");
  }

  function pauseConversation() {
    if (!activeRef.current) {
      return;
    }
    pausedRef.current = true;
    stopRecognition(true);
    cancelSpeech();
    setConversationState("paused");
  }

  async function resumeConversation() {
    if (!activeRef.current) {
      await startConversation();
      return;
    }
    pausedRef.current = false;
    setConversationState("ready");
    scheduleListening(120);
  }

  async function resetConversation() {
    if (sessionIdRef.current) {
      await resetConversationSession(sessionIdRef.current);
    }
    setSession(null);
    setSessionId("");
    sessionIdRef.current = "";
    setTranscript("");
    transcriptRef.current = "";
    setLastResponse("");
    setIntent("general_chat");
    setTopic("");
    setSavedNotePath(null);
    setError("");
    setConversationState(activeRef.current ? "ready" : "idle");
    if (activeRef.current && !pausedRef.current) {
      scheduleListening(150);
    }
  }

  function toggleStudyMode() {
    setStudyMode((current) => !current);
  }

  async function saveCurrentNote(title?: string) {
    if (!sessionIdRef.current || !lastResponse.trim()) {
      setError("Ainda nao tenho um resumo pronto para salvar.");
      setConversationState("error");
      return null;
    }
    try {
      const payload = await saveConversationNote({
        session_id: sessionIdRef.current,
        title: title?.trim() || defaultNoteTitle(session),
        content: lastResponse,
      });
      setSavedNotePath(payload.path);
      setError(payload.ok ? "" : "Nao consegui salvar no Obsidian.");
      setConversationState(payload.ok ? "ready" : "error");
      return payload.path;
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Falha ao salvar nota.");
      setConversationState("error");
      return null;
    }
  }

  return {
    active,
    state,
    transcript,
    lastResponse,
    sessionId,
    studyMode,
    isListening: state === "listening",
    isThinking: state === "thinking",
    isSpeaking: state === "speaking",
    error,
    session,
    intent,
    topic,
    savedNotePath,
    speakingLevel,
    voiceSupported,
    professionalVoice,
    startConversation,
    stopConversation,
    pauseConversation,
    resumeConversation,
    sendText,
    resetConversation,
    toggleStudyMode,
    saveCurrentNote,
  };
}

export type ConversationModeController = ReturnType<typeof useConversationMode>;
