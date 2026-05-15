import { useDeferredValue, useEffect, useMemo, useRef, useState, useTransition } from "react";
import { AnimatePresence, motion, useMotionValue, useReducedMotion, useSpring, useTransform } from "framer-motion";
import {
  Activity,
  Bell,
  Brain,
  Calendar,
  CheckCircle2,
  CircleDollarSign,
  Eye,
  FolderKanban,
  Grip,
  Headphones,
  HelpCircle,
  Link2,
  MessageCircle,
  Mic,
  MicOff,
  MonitorUp,
  Paperclip,
  Search,
  Settings,
  SlidersHorizontal,
  Sparkles,
  Trophy,
  Volume2,
  ZoomIn,
  ZoomOut,
  RefreshCcw,
  ExternalLink,
  type LucideIcon,
} from "lucide-react";

import { SettingsForm } from "@/components/settings-form";
import {
  analyzeMedia,
  apiBase,
  clearMindRestartFlag,
  captureVisionCamera,
  captureVisionScreen,
  fetchAutomationCatalog,
  fetchDashboard,
  fetchMemoryGraph,
  fetchMindState,
  fetchRuntimeStatus,
  fetchSettings,
  fetchVisionStatus,
  refreshMindProof,
  rollbackMind,
  runMindCycle,
  runVisionCameraAction,
  runVisionScreenAction,
  saveSettings,
  saveMindSettings,
  sendChat,
  startMind,
  stopMind,
  type AutomationSection,
  type DashboardModule,
  type DashboardPayload,
  type MindState,
  type MemoryGraphPayload,
  type RuntimeStatus,
  type SessionEvent,
  type VisionFrame,
  type VisionResponse,
  type VisionStatus,
} from "@/lib/api";

type ChatMessage = {
  id: string;
  role: "assistant" | "user" | "system";
  content: string;
  meta?: string;
};

type AttachmentDraft = {
  id: string;
  file: File;
  kind: "image" | "text" | "other";
  label: string;
  sizeLabel: string;
};

type VoiceMode = "conversation" | "dictation";

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

type ViewId = "chat" | "automation" | "brain" | "vision" | "mind" | "tasks" | "reminders" | "finance" | "telemetry" | "settings";
type BrainMode = "brain" | "diary" | "dump";
type TaskFilter = "all" | "normal" | "recurring";
type ReminderTab = "upcoming" | "today" | "expired" | "history";
type FinanceFilter = "all" | "variable" | "recurring" | "installments";
type SettingsTab = "profile" | "updates" | "integrations" | "system";
type ProfileContrast = "normal" | "high";
type FontScale = "normal" | "large";

type NavItem = {
  id: ViewId;
  label: string;
  icon: LucideIcon;
};

type BrainNode = {
  id: string;
  label: string;
  x: number;
  y: number;
  size: number;
  tone: "core" | "area" | "tag";
  group: string;
  path: string;
  nodeType: "vault" | "area" | "note" | "tag";
};

type TaskRow = {
  title: string;
  area: string;
  date: string;
  time: string;
  tone: "warning" | "danger" | "ok";
  recurring: boolean;
  project: string;
  status: "late" | "next" | "nodate";
};

type ReminderRow = {
  title: string;
  time: string;
  date: string;
  kind: "normal" | "recurring";
  status: "upcoming" | "today" | "expired" | "history";
};

type FinanceRow = {
  title: string;
  category: string;
  value: string;
  tone: "income" | "expense";
  date: string;
  type: "variable" | "recurring" | "installments";
  late: boolean;
};

type UpdateEntry = {
  id: string;
  date: string;
  title: string;
  body: string[];
  actionLabel?: string;
  actionUrl?: string;
};

type QuickChip = {
  label: string;
  command: string;
};

type BrainGraphData = {
  nodes: BrainNode[];
  edges: MemoryGraphPayload["edges"];
  areas: string[];
  tags: string[];
  noteTags: Map<string, string[]>;
};

type OrbNode = {
  id: string;
  x: number;
  y: number;
  size: number;
  glow: number;
  opacity: number;
  driftX: number;
  driftY: number;
  pulseDuration: number;
};

type OrbEdge = {
  id: string;
  from: OrbNode;
  to: OrbNode;
  opacity: number;
  duration: number;
};

const navItems: NavItem[] = [
  { id: "chat", label: "Chat", icon: MessageCircle },
  { id: "automation", label: "Automacao", icon: SlidersHorizontal },
  { id: "brain", label: "Memoria", icon: Brain },
  { id: "vision", label: "Visao", icon: Eye },
  { id: "mind", label: "Mind", icon: Sparkles },
  { id: "tasks", label: "Painel", icon: FolderKanban },
  { id: "reminders", label: "Alertas", icon: Bell },
  { id: "finance", label: "Financeiro", icon: CircleDollarSign },
  { id: "telemetry", label: "Atividade", icon: Activity },
  { id: "settings", label: "Configuracoes", icon: Settings },
];

const quickActions: QuickChip[] = [
  { label: "Quero ouvir Luan Santana", command: "quero ouvir luan santana" },
  { label: "Status da casa", command: "status da casa" },
  { label: "Descreva a tela", command: "descreve a tela" },
  { label: "Diagnóstico do projeto", command: "diagnostico do projeto" },
];

const quickFlowCards: Array<{
  title: string;
  description: string;
  command?: string;
  icon: LucideIcon;
  action?: "briefing" | "updates" | "finance";
}> = [
  {
    title: "Modo Foco",
    description: "Organize prioridades e reduza distrações.",
    command: "ativar modo foco",
    icon: Brain,
  },
  {
    title: "Análise Visual",
    description: "Envie uma imagem para avaliação rápida.",
    command: "descreve a tela",
    icon: Eye,
  },
  {
    title: "Status da Casa",
    description: "Veja alertas, dispositivos e rotinas.",
    command: "status da casa",
    icon: MonitorUp,
  },
  {
    title: "Briefing Diário",
    description: "Resumo rápido do que importa hoje.",
    icon: Calendar,
    action: "briefing",
  },
  {
    title: "Criar Tarefa",
    description: "Transforme uma ideia em ação agendada.",
    command: "criar tarefa",
    icon: CheckCircle2,
  },
  {
    title: "Organizar Financeiro",
    description: "Revise gastos, metas e pendências.",
    icon: CircleDollarSign,
    action: "finance",
  },
];

const taskRows: TaskRow[] = [
  {
    title: "Pesquisar visualizacao para particulas do cerebro",
    area: "Nexus",
    date: "29/04",
    time: "09:00",
    tone: "warning",
    recurring: false,
    project: "IA visual",
    status: "late",
  },
  {
    title: "Estruturar modulo de voz do Nexus",
    area: "Voice",
    date: "29/04",
    time: "09:00",
    tone: "danger",
    recurring: false,
    project: "Core",
    status: "late",
  },
  {
    title: "Criar IA estilo JARVIS",
    area: "Brain",
    date: "27/05",
    time: "09:00",
    tone: "danger",
    recurring: false,
    project: "Experimentos",
    status: "next",
  },
  {
    title: "Refinar comandos de abrir e fechar",
    area: "Desktop",
    date: "sem data",
    time: "--:--",
    tone: "warning",
    recurring: false,
    project: "Comandos",
    status: "nodate",
  },
  {
    title: "Trabalho (Dia Sim)",
    area: "Rotina",
    date: "sem data",
    time: "--:--",
    tone: "ok",
    recurring: true,
    project: "Pessoal",
    status: "nodate",
  },
  {
    title: "Revisar mapa do cerebro",
    area: "Obsidian",
    date: "03/06",
    time: "20:00",
    tone: "ok",
    recurring: true,
    project: "Conhecimento",
    status: "next",
  },
];

const reminderRows: ReminderRow[] = [
  { title: "Comecar automacao do Nexus no Obsidian", time: "20:30", date: "28/04", kind: "normal", status: "expired" },
  { title: "Comecar automacao do Nexus", time: "20:30", date: "28/04", kind: "normal", status: "expired" },
  { title: "Pagar Luiz", time: "09:00", date: "05/05", kind: "normal", status: "expired" },
  { title: "Pagar Joao", time: "09:00", date: "05/05", kind: "normal", status: "expired" },
  { title: "Rever anotacoes de viagem", time: "14:00", date: "12/05", kind: "normal", status: "today" },
  { title: "Enviar resumo para diario", time: "21:30", date: "14/05", kind: "recurring", status: "upcoming" },
];

const financeRows: FinanceRow[] = [
  { title: "Ajuste de saldo", category: "Pagamentos", value: "-R$ 1.023", tone: "expense", date: "05/05", type: "variable", late: false },
  { title: "Entrada programada", category: "Outros · Nubank", value: "+R$ 980", tone: "income", date: "05/05", type: "recurring", late: false },
  { title: "Entrada na conta", category: "Outros · Nubank", value: "+R$ 222", tone: "income", date: "01/05", type: "variable", late: false },
  { title: "Pagamento celular", category: "Contas fixas · Nubank", value: "-R$ 280", tone: "expense", date: "01/05", type: "recurring", late: true },
  { title: "Notebook parcelado", category: "Compras · Cartao", value: "-R$ 390", tone: "expense", date: "12/05", type: "installments", late: false },
];

const nexusUpdates: UpdateEntry[] = [
  {
    id: "profile",
    date: "14 abr 2026 · 13:17",
    title: "Meu Perfil com acessibilidade rapida",
    body: ["Se quiser aumentar o contraste ou o tamanho da fonte, e so acessar Meu Perfil nas configuracoes."],
  },
  {
    id: "video",
    date: "14 abr 2026 · 12:21",
    title: "Nexus esta mudando",
    body: ["Confira neste video todas as novidades que preparamos para voce."],
    actionLabel: "Abrir video",
    actionUrl: "https://youtu.be/_27xMh5UNaI",
  },
  {
    id: "internet",
    date: "14 abr 2026 · 12:21",
    title: "Novo: busca na internet dentro do Nexus",
    body: [
      "Agora voce pode pedir para o Nexus pesquisar na internet.",
      "Exemplo: pesquise sobre 5 pontos turisticos em Curitiba, salve como anotacoes e me lembre daqui 1 mes de rever isso.",
    ],
  },
  {
    id: "engine",
    date: "12 fev 2026 · 06:24",
    title: "Novo motor de inteligencia - Fevereiro 2026",
    body: [
      "Interpretacao muito mais precisa do contexto e do que voce escreve.",
      "Respostas mais detalhadas e organizadas, inclusive em canais externos.",
      "Financeiro retrabalhado e secoes visuais mais claras em habitos, financas e conhecimento.",
      "Leitura de PDFs, imagem, voz e atualizacao de interface mais estavel.",
    ],
  },
  {
    id: "integrations",
    date: "12 fev 2026 · 06:22",
    title: "Telegram e Alexa",
    body: [
      "Agora o Nexus tambem pode ser usado por Telegram e Alexa.",
      "As mensagens enviadas ficam no chat como historico, assim como no WhatsApp.",
    ],
  },
  {
    id: "knowledge",
    date: "31 jan 2026 · 08:51",
    title: "Secao Conhecimento",
    body: [
      "A nova secao Conhecimento agrupa areas e cadernos conectados por tags e relacoes manuais.",
      "Diario e brain dump foram movidos para dentro dessa secao e podem ser vistos em grafo.",
    ],
  },
  {
    id: "core-upgrade",
    date: "23 jan 2026 · 08:22",
    title: "Melhorias fundamentais",
    body: [
      "Performance muito mais rapida para qualquer acao.",
      "Brain dump, lembretes recorrentes e descricao nas tarefas agora fazem parte do fluxo base.",
    ],
  },
  {
    id: "push",
    date: "31 jul 2025 · 14:52",
    title: "Notificacoes push e WhatsApp",
    body: [
      "Com WhatsApp e push, fica muito mais dificil esquecer lembretes importantes.",
      "A ativacao continua centralizada em Meu Perfil.",
    ],
  },
  {
    id: "suggestions",
    date: "04 jul 2025 · 08:38",
    title: "Envie suas sugestoes",
    body: [
      "Relate bugs, sugira funcionalidades, compartilhe melhorias de UX e proponha integracoes para o Nexus.",
    ],
  },
];

const orbNodes: OrbNode[] = Array.from({ length: 44 }, (_unused, index) => {
  const angle = (Math.PI * 2 * index) / 44;
  const radialBias = index % 4 === 0 ? 1.06 : index % 3 === 0 ? 0.92 : 1;
  const radialNoise = Math.sin(index * 1.73) * 18 + Math.cos(index * 0.61) * 13 + Math.sin(index * 0.37 + 0.4) * 8;
  const tangentNoise = Math.cos(index * 1.29) * 8;
  const radius = 162 * radialBias + radialNoise;
  const tangentAngle = angle + Math.PI / 2;

  return {
    id: `orb-${index}`,
    x: 210 + Math.cos(angle) * radius + Math.cos(tangentAngle) * tangentNoise,
    y: 210 + Math.sin(angle) * radius + Math.sin(tangentAngle) * tangentNoise,
    size: 1.8 + ((index * 7) % 11) * 0.24,
    glow: 4.4 + (index % 5) * 1.15,
    opacity: 0.48 + (index % 4) * 0.1,
    driftX: Math.sin(index * 1.11) * (1.2 + (index % 3) * 0.45),
    driftY: Math.cos(index * 1.37) * (1.1 + (index % 4) * 0.32),
    pulseDuration: 3.1 + (index % 7) * 0.42,
  };
});

const orbEdges: OrbEdge[] = orbNodes.flatMap((node, index) => {
  const next = orbNodes[(index + 1) % orbNodes.length];
  const shortChord = orbNodes[(index + 4 + (index % 2)) % orbNodes.length];
  const longChord = orbNodes[(index + 9 + (index % 3)) % orbNodes.length];
  const edges: OrbEdge[] = [
    {
      id: `${node.id}-edge`,
      from: node,
      to: next,
      opacity: 0.1 + (index % 4) * 0.018,
      duration: 3.6 + (index % 6) * 0.35,
    },
  ];

  if (index % 2 === 0) {
    edges.push({
      id: `${node.id}-short`,
      from: node,
      to: shortChord,
      opacity: 0.065 + (index % 3) * 0.012,
      duration: 4.4 + (index % 5) * 0.4,
    });
  }

  if (index % 5 === 0) {
    edges.push({
      id: `${node.id}-long`,
      from: node,
      to: longChord,
      opacity: 0.045 + (index % 4) * 0.01,
      duration: 5.1 + (index % 4) * 0.45,
    });
  }

  return edges;
});

const textAttachmentExtensions = new Set(["txt", "md", "markdown", "json", "csv", "py", "js", "ts", "tsx", "jsx", "html", "css", "log", "yml", "yaml"]);

function classifyAttachment(file: File): AttachmentDraft["kind"] {
  if (file.type.startsWith("image/")) {
    return "image";
  }
  const extension = file.name.split(".").pop()?.toLowerCase() ?? "";
  if (file.type.startsWith("text/") || textAttachmentExtensions.has(extension)) {
    return "text";
  }
  return "other";
}

function formatFileSize(bytes: number) {
  if (bytes >= 1024 * 1024) {
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  }
  if (bytes >= 1024) {
    return `${Math.round(bytes / 1024)} KB`;
  }
  return `${bytes} B`;
}

function appendTranscript(current: string, next: string) {
  const base = current.trim();
  const chunk = next.trim();
  if (!chunk) {
    return base;
  }
  return base ? `${base} ${chunk}` : chunk;
}

function resolveSpeechRecognitionConstructor(): BrowserSpeechRecognitionConstructor | null {
  if (typeof window === "undefined") {
    return null;
  }
  const speechWindow = window as Window & {
    SpeechRecognition?: BrowserSpeechRecognitionConstructor;
    webkitSpeechRecognition?: BrowserSpeechRecognitionConstructor;
  };
  return speechWindow.SpeechRecognition ?? speechWindow.webkitSpeechRecognition ?? null;
}

const bootMessage: ChatMessage = {
  id: "boot",
  role: "assistant",
  content:
    "Nova shell visual online. O chat continua ligado ao backend Python e agora a interface esta organizada como um cockpit pessoal.",
  meta: "bootstrap",
};

function sanitizeChatText(text: string) {
  return (text || "")
    .replace(/\b(?:USER|ASSISTANT|SYSTEM)\s*:\s*/gi, "")
    .replace(/\b(?:DRAFT|CONFIRMED|BOOTSTRAP|WEB\/ERROR|SETTINGS\/SAVE|SETTINGS\/ERROR)\b/gi, "")
    .replace(/\{[^{}]*'TEXT'[^{}]*\}/gi, "")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeVoiceText(text: string) {
  return (text || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function buildConversationCards(messages: ChatMessage[]) {
  const cleanMessages = messages
    .filter((message) => message.role === "user" || message.role === "assistant")
    .map((message) => ({ ...message, content: sanitizeChatText(message.content) }))
    .filter((message) => message.content);

  const cards: Array<{ prompt: string; response: string }> = [];
  let pendingPrompt: string | null = null;

  for (const message of cleanMessages) {
    if (message.role === "user") {
      pendingPrompt = message.content;
      continue;
    }
    if (message.role === "assistant" && pendingPrompt) {
      cards.push({ prompt: pendingPrompt, response: message.content });
      pendingPrompt = null;
    }
  }

  return cards.slice(-3).reverse();
}

function asMessageId() {
  return Math.random().toString(36).slice(2, 10);
}

function visionFrameUrl(frame: VisionFrame | null) {
  if (!frame) {
    return "";
  }
  return `data:${frame.media_type};base64,${frame.base64_data}`;
}

function eventToSessionEvent(event: MessageEvent<string>): SessionEvent | null {
  try {
    const payload = JSON.parse(event.data) as {
      kind: string;
      message: string;
      data?: Record<string, unknown>;
    };

    return {
      timestamp: typeof payload.data?.timestamp === "string" ? payload.data.timestamp : new Date().toISOString(),
      kind: payload.kind,
      message: payload.message,
      data: payload.data ?? {},
    };
  } catch {
    return null;
  }
}

function toneClass(tone: string) {
  if (tone === "income" || tone === "online" || tone === "ready" || tone === "ok") {
    return "text-[#2fe1b1]";
  }
  if (tone === "danger" || tone === "expense" || tone === "recording") {
    return "text-[#f37588]";
  }
  if (tone === "warning" || tone === "guarded" || tone === "plug-in") {
    return "text-[#f0bb50]";
  }
  return "text-[#54d8ff]";
}

const GRAPH_WIDTH = 980;
const GRAPH_HEIGHT = 680;
const GRAPH_CENTER = { x: GRAPH_WIDTH / 2, y: GRAPH_HEIGHT / 2 };

function normalizeBrainText(text: string) {
  return (text || "")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim();
}

function hashBrainValue(text: string) {
  let hash = 0;
  for (let index = 0; index < text.length; index += 1) {
    hash = (hash * 31 + text.charCodeAt(index)) >>> 0;
  }
  return hash;
}

function matchesBrainMode(node: MemoryGraphPayload["nodes"][number], mode: BrainMode) {
  if (node.node_type !== "note") {
    return true;
  }
  const haystack = normalizeBrainText(`${node.label} ${node.path}`);
  if (mode === "diary") {
    return /diario/.test(haystack);
  }
  if (mode === "dump") {
    return /brain dump|dump/.test(haystack);
  }
  return true;
}

function buildBrainGraph(
  memoryGraph: MemoryGraphPayload | null,
  options: {
    mode: BrainMode;
    showTags: boolean;
    search: string;
    areaFilter: string;
    tagFilter: string;
    linkedOnly: boolean;
    layoutSeed: number;
  },
): BrainGraphData {
  if (!memoryGraph?.enabled) {
    return { nodes: [], edges: [], areas: [], tags: [], noteTags: new Map() };
  }

  const allNodes = memoryGraph.nodes;
  const tagNodeById = new Map(allNodes.filter((node) => node.node_type === "tag").map((node) => [node.id, node]));
  const noteTags = new Map<string, string[]>();
  const linkedNotes = new Set<string>();
  for (const edge of memoryGraph.edges) {
    if (edge.relation === "tagged") {
      const tagNode = tagNodeById.get(edge.target);
      const list = noteTags.get(edge.source) ?? [];
      if (tagNode) {
        list.push(tagNode.label);
      }
      noteTags.set(edge.source, list);
    }
    if (edge.relation === "links") {
      linkedNotes.add(edge.source);
      linkedNotes.add(edge.target);
    }
  }

  const allNotes = allNodes.filter((node) => node.node_type === "note");
  const areas = Array.from(new Set(allNotes.map((node) => node.group))).sort((left, right) => left.localeCompare(right));
  const tags = Array.from(new Set(Array.from(noteTags.values()).flat())).sort((left, right) => left.localeCompare(right));
  const searchNeedle = normalizeBrainText(options.search);

  const visibleNotes = allNotes.filter((node) => {
    if (!matchesBrainMode(node, options.mode)) {
      return false;
    }
    if (options.areaFilter !== "all" && node.group !== options.areaFilter) {
      return false;
    }
    const tagsForNote = noteTags.get(node.id) ?? [];
    if (options.tagFilter !== "all" && !tagsForNote.includes(options.tagFilter)) {
      return false;
    }
    if (options.linkedOnly && !linkedNotes.has(node.id)) {
      return false;
    }
    if (searchNeedle) {
      const searchable = normalizeBrainText(`${node.label} ${node.path} ${tagsForNote.join(" ")}`);
      return searchable.includes(searchNeedle);
    }
    return true;
  });

  const visibleNoteIds = new Set(visibleNotes.map((node) => node.id));
  const visibleAreaIds = new Set(
    allNodes
      .filter((node) => node.node_type === "area" && visibleNotes.some((note) => note.group === node.label))
      .map((node) => node.id),
  );
  const visibleTagIds = new Set<string>();
  for (const edge of memoryGraph.edges) {
    if (edge.relation === "tagged" && visibleNoteIds.has(edge.source) && options.showTags) {
      visibleTagIds.add(edge.target);
    }
  }

  const includedIds = new Set<string>();
  for (const node of allNodes) {
    if (node.node_type === "vault") {
      includedIds.add(node.id);
    }
    if (node.node_type === "area" && visibleAreaIds.has(node.id)) {
      includedIds.add(node.id);
    }
    if (node.node_type === "note" && visibleNoteIds.has(node.id)) {
      includedIds.add(node.id);
    }
    if (node.node_type === "tag" && visibleTagIds.has(node.id)) {
      includedIds.add(node.id);
    }
  }

  const edges = memoryGraph.edges.filter((edge) => {
    if (!includedIds.has(edge.source) || !includedIds.has(edge.target)) {
      return false;
    }
    if (!options.showTags && edge.relation === "tagged") {
      return false;
    }
    return true;
  });

  const sourceNodes = allNodes.filter((node) => includedIds.has(node.id));
  const vaultNode = sourceNodes.find((node) => node.node_type === "vault");
  const areaNodes = sourceNodes.filter((node) => node.node_type === "area");
  const noteNodes = sourceNodes.filter((node) => node.node_type === "note");
  const tagNodes = sourceNodes.filter((node) => node.node_type === "tag");
  const positioned: BrainNode[] = [];
  const areaAnchors = new Map<string, { x: number; y: number }>();

  if (vaultNode) {
    positioned.push({
      id: vaultNode.id,
      label: vaultNode.label,
      x: GRAPH_CENTER.x,
      y: GRAPH_CENTER.y,
      size: 24,
      tone: "core",
      group: vaultNode.group,
      path: vaultNode.path,
      nodeType: "vault",
    });
  }

  areaNodes.forEach((node, index) => {
    const hash = hashBrainValue(`${node.id}:${options.layoutSeed}`);
    const angle = (Math.PI * 2 * index) / Math.max(areaNodes.length, 1) + (hash % 40) * 0.01;
    const radiusX = 180 + (hash % 60);
    const radiusY = 120 + ((hash >> 3) % 70);
    const anchor = {
      x: GRAPH_CENTER.x + Math.cos(angle) * radiusX,
      y: GRAPH_CENTER.y + Math.sin(angle) * radiusY,
    };
    areaAnchors.set(node.label, anchor);
    positioned.push({
      id: node.id,
      label: node.label,
      x: anchor.x,
      y: anchor.y,
      size: 15,
      tone: "area",
      group: node.group,
      path: node.path,
      nodeType: "area",
    });
  });

  noteNodes.forEach((node, index) => {
    const anchor = areaAnchors.get(node.group) ?? GRAPH_CENTER;
    const hash = hashBrainValue(`${node.id}:${options.layoutSeed}`);
    const angle = ((hash % 360) * Math.PI) / 180;
    const radius = 85 + (hash % 160);
    const driftX = ((hash >> 3) % 44) - 22;
    const driftY = ((hash >> 8) % 36) - 18;
    positioned.push({
      id: node.id,
      label: node.label.slice(0, 28),
      x: anchor.x + Math.cos(angle) * radius + driftX,
      y: anchor.y + Math.sin(angle) * radius * 0.72 + driftY,
      size: Math.max(9, Math.min(node.size + 1, 16)),
      tone: "area",
      group: node.group,
      path: node.path,
      nodeType: "note",
    });
  });

  const positionedNotes = positioned.filter((node) => node.nodeType === "note");

  tagNodes.forEach((node, index) => {
    const relatedNotes = graphEdgesForTag(node.id, edges, positionedNotes);
    const basePoint =
      relatedNotes.length > 0
        ? {
            x: relatedNotes.reduce((sum, item) => sum + item.x, 0) / relatedNotes.length,
            y: relatedNotes.reduce((sum, item) => sum + item.y, 0) / relatedNotes.length,
          }
        : GRAPH_CENTER;
    const hash = hashBrainValue(`${node.id}:${options.layoutSeed}`);
    const angle = ((hash % 360) * Math.PI) / 180;
    const radius = 70 + (hash % 90);
    positioned.push({
      id: node.id,
      label: node.label,
      x: basePoint.x + Math.cos(angle) * radius,
      y: basePoint.y + Math.sin(angle) * radius * 0.7,
      size: Math.max(7, Math.min(node.size, 12)),
      tone: "tag",
      group: node.group,
      path: node.path,
      nodeType: "tag",
    });
  });

  return {
    nodes: positioned,
    edges,
    areas,
    tags,
    noteTags,
  };
}

function formatDayLabel(offset: number) {
  return ["SEG", "TER", "QUA", "QUI", "SEX", "SAB", "DOM"][offset % 7];
}

function openExternal(url: string) {
  window.open(url, "_blank", "noopener,noreferrer");
}

function cycleOption(current: string, options: string[]) {
  const currentIndex = options.indexOf(current);
  if (currentIndex === -1) {
    return options[0] ?? current;
  }
  return options[(currentIndex + 1) % options.length] ?? current;
}

function splitFinanceCategory(category: string) {
  const [group, bank] = category.split("·").map((item) => item.trim());
  return {
    group: group || "Sem categoria",
    bank: bank || "Sem banco",
  };
}

async function copyText(text: string) {
  if (typeof navigator === "undefined" || !navigator.clipboard) {
    throw new Error("Clipboard indisponivel neste navegador.");
  }
  await navigator.clipboard.writeText(text);
}

function graphEdgesForTag(tagId: string, edges: MemoryGraphPayload["edges"], noteNodes: BrainNode[]) {
  const noteMap = new Map(noteNodes.map((node) => [node.id, node]));
  return edges
    .filter((edge) => edge.relation === "tagged" && edge.target === tagId)
    .map((edge) => noteMap.get(edge.source))
    .filter((node): node is BrainNode => Boolean(node));
}

function ShellCard({
  title,
  eyebrow,
  right,
  children,
  className = "",
}: {
  title?: string;
  eyebrow?: string;
  right?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <section className={`shell-card ${className}`}>
      {(title || eyebrow || right) && (
        <div className="mb-5 flex items-start justify-between gap-4">
          <div>
            {eyebrow ? <p className="shell-eyebrow">{eyebrow}</p> : null}
            {title ? <h3 className="mt-2 text-xl font-semibold text-white">{title}</h3> : null}
          </div>
          {right}
        </div>
      )}
      {children}
    </section>
  );
}

function Sidebar({
  activeView,
  onSelect,
  onHelp,
}: {
  activeView: ViewId;
  onSelect: (view: ViewId) => void;
  onHelp: () => void;
}) {
  return (
    <aside className="shell-sidebar">
      <div className="flex flex-1 flex-col gap-3">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = item.id === activeView;
          return (
            <button
              key={item.id}
              type="button"
              onClick={() => onSelect(item.id)}
              className={`shell-nav-button ${active ? "shell-nav-button-active" : ""}`}
              aria-label={item.label}
              title={item.label}
            >
              <span className="shell-nav-line" />
              <Icon className="h-5 w-5" />
            </button>
          );
        })}
      </div>
      <div className="border-t border-white/8 pt-4">
        <button type="button" className="shell-nav-button" aria-label="Ajuda" title="Ajuda" onClick={onHelp}>
          <span className="shell-nav-line" />
          <HelpCircle className="h-5 w-5" />
        </button>
      </div>
    </aside>
  );
}

function InteractiveOrb({ onBriefing }: { onBriefing: () => void }) {
  const prefersReducedMotion = useReducedMotion();
  const [hasFinePointer, setHasFinePointer] = useState(true);
  const [isBlinking, setIsBlinking] = useState(false);
  const [pulseTick, setPulseTick] = useState(0);
  const targetRef = useRef({ x: 0, y: 0 });
  const lastMoveAtRef = useRef(Date.now());
  const pointerXTarget = useMotionValue(0);
  const pointerYTarget = useMotionValue(0);
  const focusTarget = useMotionValue(0);
  const pointerX = useSpring(pointerXTarget, { stiffness: 112, damping: 18, mass: 0.58 });
  const pointerY = useSpring(pointerYTarget, { stiffness: 112, damping: 18, mass: 0.58 });
  const focusLevel = useSpring(focusTarget, { stiffness: 86, damping: 20, mass: 0.65 });

  useEffect(() => {
    const media = window.matchMedia("(pointer:fine)");
    const apply = () => setHasFinePointer(media.matches);
    apply();
    media.addEventListener?.("change", apply);
    return () => media.removeEventListener?.("change", apply);
  }, []);

  useEffect(() => {
    if (prefersReducedMotion) {
      pointerXTarget.set(0);
      pointerYTarget.set(0);
      focusTarget.set(0);
      return;
    }

    let frameId = 0;
    const loop = () => {
      const now = Date.now();
      const idle = !hasFinePointer || now - lastMoveAtRef.current > 1500;
      if (idle) {
        const time = now / 1000;
        pointerXTarget.set(Math.sin(time * 0.65) * 0.15);
        pointerYTarget.set(Math.cos(time * 0.42) * 0.1);
        focusTarget.set(0.08);
      } else {
        pointerXTarget.set(targetRef.current.x);
        pointerYTarget.set(targetRef.current.y);
      }

      frameId = window.requestAnimationFrame(loop);
    };

    frameId = window.requestAnimationFrame(loop);
    return () => window.cancelAnimationFrame(frameId);
  }, [focusTarget, hasFinePointer, pointerXTarget, pointerYTarget, prefersReducedMotion]);

  useEffect(() => {
    if (prefersReducedMotion) {
      return;
    }
    let timerId = 0;
    const scheduleBlink = () => {
      const nextDelay = 2600 + Math.random() * 4200;
      timerId = window.setTimeout(() => {
        setIsBlinking(true);
        window.setTimeout(() => setIsBlinking(false), 160);
        scheduleBlink();
      }, nextDelay);
    };
    scheduleBlink();
    return () => window.clearTimeout(timerId);
  }, [prefersReducedMotion]);

  const hoverStrength = useTransform(() => Math.min(focusLevel.get() * 0.72 + Math.hypot(pointerX.get(), pointerY.get()) * 1.05, 1));
  const irisX = useTransform(pointerX, (value) => value * 28);
  const irisY = useTransform(pointerY, (value) => value * 18);
  const sceneX = useTransform(pointerX, (value) => value * 12);
  const sceneY = useTransform(pointerY, (value) => value * 12);
  const coreX = useTransform(pointerX, (value) => value * 24);
  const coreY = useTransform(pointerY, (value) => value * 20);
  const glowScale = useTransform(hoverStrength, [0, 1], [1, 1.08]);
  const haloOpacity = useTransform(hoverStrength, [0, 1], [0.68, 0.88]);
  const haloScale = useTransform(hoverStrength, [0, 1], [1, 1.03]);
  const focusScale = useTransform(hoverStrength, [0, 1], [1, 1.08]);
  const focusOpacity = useTransform(hoverStrength, [0, 1], [0.22, 0.56]);
  const pupilScale = useTransform(hoverStrength, [0, 1], [1, 0.91]);
  const scannerDuration = prefersReducedMotion ? 0 : 7.4;

  return (
    <div
      className="relative mx-auto flex h-[min(86vw,560px)] w-[min(86vw,560px)] items-center justify-center"
      onMouseMove={(event) => {
        const rect = event.currentTarget.getBoundingClientRect();
        const rawX = (event.clientX - rect.left - rect.width / 2) / (rect.width / 2);
        const rawY = (event.clientY - rect.top - rect.height / 2) / (rect.height / 2);
        const centerX = rect.left + rect.width / 2;
        const centerY = rect.top + rect.height / 2;
        const distance = Math.hypot(event.clientX - centerX, event.clientY - centerY);
        const limit = 0.5;
        targetRef.current = {
          x: Math.max(-limit, Math.min(limit, rawX * 0.56)),
          y: Math.max(-limit, Math.min(limit, rawY * 0.46)),
        };
        lastMoveAtRef.current = Date.now();
        focusTarget.set(Math.max(0, 1 - distance / (rect.width * 0.42)));
      }}
      onMouseLeave={() => {
        targetRef.current = { x: 0, y: 0 };
        lastMoveAtRef.current = 0;
        focusTarget.set(0);
      }}
      onClick={() => setPulseTick((current) => current + 1)}
    >
      <motion.div
        className="absolute inset-0 rounded-full"
        style={{
          x: sceneX,
          y: sceneY,
          scale: glowScale,
        }}
      >
        <motion.div
          className="orb-network-layer"
          animate={prefersReducedMotion ? undefined : { rotate: [0, 0.72, 0] }}
          transition={prefersReducedMotion ? undefined : { duration: 30, ease: "linear", repeat: Number.POSITIVE_INFINITY }}
        >
          <div className="orb-ring opacity-50" />
          <motion.div
            className="orb-halo"
            style={{
              opacity: haloOpacity,
              scale: haloScale,
            }}
          />
          <svg viewBox="0 0 420 420" className="absolute inset-0 h-full w-full overflow-visible">
            {orbEdges.map((edge, index) => (
              <line
                key={edge.id}
                className="orb-edge"
                x1={edge.from.x}
                y1={edge.from.y}
                x2={edge.to.x}
                y2={edge.to.y}
                stroke={`rgba(48, 211, 255, ${edge.opacity})`}
                strokeWidth={0.8 + (index % 5) * 0.06}
                style={
                  prefersReducedMotion
                    ? undefined
                    : {
                        animationDuration: `${edge.duration}s`,
                        animationDelay: `${(index % 7) * 0.22}s`,
                      }
                }
              />
            ))}
            {orbNodes.map((node, index) => (
              <g
                key={node.id}
                className="orb-node-cluster"
                style={
                  prefersReducedMotion
                    ? undefined
                    : {
                        animationDuration: `${node.pulseDuration}s`,
                        animationDelay: `${index * 0.05}s`,
                        opacity: node.opacity,
                      }
                }
              >
                <circle className="orb-node-solid" cx={node.x} cy={node.y} r={node.size} fill={`rgba(62, 223, 255, ${Math.min(0.95, node.opacity + 0.16)})`} />
                <circle className="orb-node-glow" cx={node.x} cy={node.y} r={node.glow} fill={`rgba(62, 223, 255, ${node.opacity * 0.14})`} />
              </g>
            ))}
          </svg>
        </motion.div>
      </motion.div>

      <motion.div
        style={{
          x: coreX,
          y: coreY,
        }}
        animate={prefersReducedMotion ? undefined : { scale: [1, 1.012, 1] }}
        transition={prefersReducedMotion ? undefined : { duration: 4.8, repeat: Number.POSITIVE_INFINITY, ease: "easeInOut" }}
        className="orb-core"
      >
        <motion.div
          className="orb-core-aura"
          animate={prefersReducedMotion ? undefined : { scale: [1, 1.03, 1], opacity: [0.46, 0.58, 0.48] }}
          transition={prefersReducedMotion ? undefined : { duration: 5.8, ease: "easeInOut", repeat: Number.POSITIVE_INFINITY }}
        />
        <motion.div
          className="orb-core-focus"
          style={{
            scale: focusScale,
            opacity: focusOpacity,
          }}
        />
        <motion.div
          className="orb-energy-pulse"
          animate={prefersReducedMotion ? undefined : { scale: [1, 1.06, 1], opacity: [0.32, 0.46, 0.32] }}
          transition={prefersReducedMotion ? undefined : { duration: 5.2, ease: "easeInOut", repeat: Number.POSITIVE_INFINITY }}
        />
        <motion.div
          className="orb-inner-ring orb-inner-ring-a"
          animate={prefersReducedMotion ? undefined : { rotate: 360 }}
          transition={prefersReducedMotion ? undefined : { duration: 24, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
        />
        <motion.div
          className="orb-inner-ring orb-inner-ring-b"
          animate={prefersReducedMotion ? undefined : { rotate: -360 }}
          transition={prefersReducedMotion ? undefined : { duration: 34, repeat: Number.POSITIVE_INFINITY, ease: "linear" }}
        />
        <AnimatePresence>
          {pulseTick > 0 ? (
            <motion.span
              key={pulseTick}
              className="orb-click-pulse"
              initial={{ scale: 0.72, opacity: 0.55 }}
              animate={{ scale: 1.5, opacity: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.9, ease: "easeOut" }}
            />
          ) : null}
        </AnimatePresence>
        <div className="mx-auto flex flex-col items-center justify-center gap-4 px-4 text-center">
          <p className="shell-eyebrow text-center">boa tarde</p>
          <div className="nexus-eye-shell">
            <motion.div
              className="nexus-eye"
              animate={{
                scaleY: isBlinking ? 0.14 : 1,
              }}
              transition={{ duration: isBlinking ? 0.14 : 0.3, ease: "easeInOut" }}
            >
              <motion.div
                className="nexus-eye-scanner"
                animate={prefersReducedMotion ? undefined : { x: ["-120%", "140%"] }}
                transition={prefersReducedMotion ? undefined : { duration: scannerDuration, ease: "easeInOut", repeat: Number.POSITIVE_INFINITY, repeatDelay: 2.2 }}
              />
              <div className="nexus-eye-reflection" />
              <motion.div
                className="nexus-eye-iris"
                style={{
                  x: irisX,
                  y: irisY,
                }}
              >
                <div className="nexus-eye-iris-ring" />
                <motion.div
                  className="nexus-eye-pupil"
                  style={{
                    scale: pupilScale,
                  }}
                />
              </motion.div>
              {!prefersReducedMotion
                ? Array.from({ length: 3 }, (_unused, index) => (
                    <motion.span
                      key={`orbital-${index}`}
                      className={`nexus-eye-orbit orbit-${index + 1}`}
                      animate={{ rotate: index % 2 === 0 ? 360 : -360 }}
                      transition={{ duration: 12 + index * 6, ease: "linear", repeat: Number.POSITIVE_INFINITY }}
                    />
                  ))
                : null}
            </motion.div>
          </div>
          <button type="button" className="orb-briefing" onClick={onBriefing}>
            <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
            <span>ver briefing diário</span>
          </button>
        </div>
      </motion.div>
    </div>
  );
}

function ChatDock({
  command,
  isSending,
  onChange,
  onSend,
}: {
  command: string;
  isSending: boolean;
  onChange: (value: string) => void;
  onSend: () => void;
}) {
  return (
    <div className="shell-input-wrap">
      <textarea
        value={command}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={(event) => {
          if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
            event.preventDefault();
            onSend();
          }
        }}
        rows={1}
        placeholder="Digite um comando, peça uma análise ou escolha uma ação..."
        className="shell-input"
      />
      <div className="shell-input-actions">
        <Paperclip className="h-4 w-4" />
        <Headphones className="h-4 w-4" />
        <Volume2 className="h-4 w-4" />
        <Mic className="h-4 w-4" />
        <button type="button" onClick={onSend} disabled={isSending} className="shell-send-button">
          {isSending ? "enviando" : "Executar"}
        </button>
      </div>
    </div>
  );
}

function ChatCommandDock({
  command,
  attachments,
  isSending,
  isConversationActive,
  isDictating,
  isSpeaking,
  voiceSupported,
  onChange,
  onAttachFiles,
  onToggleConversation,
  onTranscribe,
  onSpeakLastResponse,
  onRemoveAttachment,
  onSend,
}: {
  command: string;
  attachments: AttachmentDraft[];
  isSending: boolean;
  isConversationActive: boolean;
  isDictating: boolean;
  isSpeaking: boolean;
  voiceSupported: boolean;
  onChange: (value: string) => void;
  onAttachFiles: (files: FileList | null) => void;
  onToggleConversation: () => void;
  onTranscribe: () => void;
  onSpeakLastResponse: () => void;
  onRemoveAttachment: (id: string) => void;
  onSend: () => void;
}) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const statusText = isDictating
    ? "Ouvindo seu comando por voz..."
    : isConversationActive
      ? "Modo conversa por voz ativo. O Nexus escuta, responde e volta a ouvir."
      : attachments.length
        ? `${attachments.length} mídia(s) pronta(s) para análise.`
        : voiceSupported
          ? "Anexe mídia, fale um comando único no microfone ou abra a conversa por voz."
          : "Anexe mídia ou use o chat por texto neste navegador.";

  return (
    <div className="space-y-3">
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept="image/*,.txt,.md,.markdown,.json,.csv,.py,.js,.ts,.tsx,.jsx,.html,.css,.log,.yml,.yaml"
        className="hidden"
        onChange={(event) => {
          onAttachFiles(event.target.files);
          event.currentTarget.value = "";
        }}
      />
      <div className="shell-input-wrap">
        <textarea
          value={command}
          onChange={(event) => onChange(event.target.value)}
          onKeyDown={(event) => {
            if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
              event.preventDefault();
              onSend();
            }
          }}
          rows={1}
          placeholder="Digite um comando, peça uma análise ou escolha uma ação..."
          className="shell-input"
        />
        <div className="shell-input-actions">
          <button type="button" className="shell-tool-button" title="Anexar mídia" aria-label="Anexar mídia" onClick={() => fileInputRef.current?.click()}>
            <Paperclip className="h-4 w-4" />
          </button>
          <button
            type="button"
            className={`shell-tool-button ${isConversationActive ? "shell-tool-button-active" : ""}`}
            title={isConversationActive ? "Encerrar conversa por voz" : "Falar com o Nexus"}
            aria-label="Falar com o Nexus"
            onClick={onToggleConversation}
          >
            <Headphones className="h-4 w-4" />
          </button>
          <button
            type="button"
            className={`shell-tool-button ${isSpeaking ? "shell-tool-button-active" : ""}`}
            title="Ouvir última resposta"
            aria-label="Ouvir última resposta"
            onClick={onSpeakLastResponse}
          >
            <Volume2 className="h-4 w-4" />
          </button>
          <button
            type="button"
            className={`shell-tool-button ${isDictating ? "shell-tool-button-active" : ""}`}
            title={isDictating ? "Parar captura de voz" : "Falar e executar"}
            aria-label="Falar e executar"
            onClick={onTranscribe}
          >
            {isDictating ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
          </button>
          <button type="button" onClick={onSend} disabled={isSending} className="shell-send-button">
            {isSending ? "enviando" : "Executar"}
          </button>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <p className="shell-input-status">{statusText}</p>
        {attachments.map((attachment) => (
          <span key={attachment.id} className="shell-attachment-chip">
            <span className="font-medium text-white">{attachment.label}</span>
            <span>{attachment.sizeLabel}</span>
            <button type="button" className="shell-attachment-remove" onClick={() => onRemoveAttachment(attachment.id)}>
              remover
            </button>
          </span>
        ))}
      </div>
    </div>
  );
}

function ChatLanding({
  dashboard,
  messages,
  command,
  attachments,
  isSending,
  isConversationActive,
  isDictating,
  isSpeaking,
  voiceSupported,
  pendingConfirmation,
  quickActionItems,
  onChange,
  onAttachFiles,
  onToggleConversation,
  onTranscribe,
  onSpeakLastResponse,
  onRemoveAttachment,
  onQuickAction,
  onSend,
  onConfirmPending,
  onBriefing,
  onOpenUpdates,
  onOpenFinance,
}: {
  dashboard: DashboardPayload | null;
  messages: ChatMessage[];
  command: string;
  attachments: AttachmentDraft[];
  isSending: boolean;
  isConversationActive: boolean;
  isDictating: boolean;
  isSpeaking: boolean;
  voiceSupported: boolean;
  pendingConfirmation: string | null;
  quickActionItems: QuickChip[];
  onChange: (value: string) => void;
  onAttachFiles: (files: FileList | null) => void;
  onToggleConversation: () => void;
  onTranscribe: () => void;
  onSpeakLastResponse: () => void;
  onRemoveAttachment: (id: string) => void;
  onQuickAction: (value: string) => void;
  onSend: () => void;
  onConfirmPending: () => void;
  onBriefing: () => void;
  onOpenUpdates: () => void;
  onOpenFinance: () => void;
}) {
  const conversationCards = useMemo(() => buildConversationCards(messages), [messages]);

  return (
    <section className="relative flex min-h-[calc(100vh-3rem)] flex-col overflow-hidden px-4 py-8 sm:px-6 lg:px-12 lg:py-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(32,145,184,0.16),transparent_26%),radial-gradient(circle_at_80%_100%,rgba(60,80,180,0.12),transparent_30%)]" />
      <div className="pointer-events-none absolute inset-0 opacity-50">
        {Array.from({ length: 90 }, (_unused, index) => (
          <span
            key={`star-${index}`}
            className="star-dot"
            style={{
              left: `${(index * 13) % 100}%`,
              top: `${(index * 19) % 100}%`,
              animationDelay: `${(index % 7) * 0.8}s`,
            }}
          />
        ))}
      </div>

      <div className="relative z-10 mx-auto flex w-full max-w-[1180px] flex-col items-center">
        <div className="mb-6 flex w-full max-w-4xl flex-wrap items-center justify-center gap-3">
          {quickActionItems.map((item) => (
            <button key={item.command} type="button" onClick={() => onQuickAction(item.command)} className="shell-chip">
              {item.label}
            </button>
          ))}
        </div>

        <InteractiveOrb onBriefing={onBriefing} />

        <div className="-mt-10 w-full max-w-4xl">
          <ChatCommandDock
            command={command}
            attachments={attachments}
            isSending={isSending}
            isConversationActive={isConversationActive}
            isDictating={isDictating}
            isSpeaking={isSpeaking}
            voiceSupported={voiceSupported}
            onChange={onChange}
            onAttachFiles={onAttachFiles}
            onToggleConversation={onToggleConversation}
            onTranscribe={onTranscribe}
            onSpeakLastResponse={onSpeakLastResponse}
            onRemoveAttachment={onRemoveAttachment}
            onSend={onSend}
          />
          <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
            <button
              type="button"
              onClick={() => {
                const latestPrompt = conversationCards[0]?.prompt;
                if (latestPrompt) {
                  onQuickAction(latestPrompt);
                }
              }}
              className="shell-inline-action !rounded-2xl !py-3 text-center"
            >
              Continuar última conversa
            </button>
            <button type="button" onClick={onOpenUpdates} className="shell-inline-action !rounded-2xl !py-3 text-center">
              Ver novidades
            </button>
            <button type="button" onClick={() => document.getElementById("quick-flows")?.scrollIntoView({ behavior: "smooth", block: "start" })} className="shell-inline-action !rounded-2xl !py-3 text-center">
              Abrir central de comandos
            </button>
          </div>
        </div>

        <div className="mt-8 grid w-full items-stretch gap-4 xl:grid-cols-[1.16fr_0.84fr]">
          <ShellCard eyebrow="Histórico recente" title="Últimas conversas" className="flex min-h-[420px] flex-col overflow-hidden">
            <p className="-mt-1 mb-4 text-sm text-slate-300">Continue rapidamente de onde você parou.</p>
            <div className="scroll-panel flex-1 space-y-3 overflow-y-auto pr-1">
              {conversationCards.length ? (
                conversationCards.map((item, index) => (
                  <article key={`${item.prompt}-${index}`} className="rounded-3xl border border-white/8 bg-white/[0.03] px-4 py-4">
                    <p className="text-[11px] uppercase tracking-[0.18em] text-slate-400">última conversa</p>
                    <p className="mt-3 text-sm font-medium text-white">Você pediu</p>
                    <p className="mt-1 text-sm leading-6 text-slate-200">"{item.prompt}"</p>
                    <p className="mt-3 text-sm font-medium text-white">Resposta do sistema</p>
                    <p className="mt-1 text-sm leading-6 text-slate-300">"{item.response}"</p>
                    <button type="button" className="mt-4 shell-chip" onClick={() => onQuickAction(item.prompt)}>
                      Retomar conversa
                    </button>
                  </article>
                ))
              ) : (
                <article className="rounded-3xl border border-white/8 bg-white/[0.03] px-4 py-4">
                  <p className="text-sm leading-6 text-slate-300">As próximas interações do chat vão aparecer aqui de forma limpa, sem códigos internos.</p>
                </article>
              )}
            </div>
          </ShellCard>

          <div className="grid min-h-[420px] gap-4 grid-rows-[auto_1fr]">
            <ShellCard eyebrow="Sistema" title="Status do sistema">
              <p className="-mt-1 mb-4 text-sm text-slate-300">Monitoramento geral da operação.</p>
              <div className="grid grid-cols-2 gap-5">
                <div>
                  <p className="text-sm text-slate-300">Saúde geral</p>
                  <p className="mt-2 text-4xl font-semibold text-[#54d8ff]">{dashboard?.health.score ?? "--"}%</p>
                  <p className="mt-2 text-sm text-slate-500">NEXUS operacional</p>
                </div>
                <div>
                  <p className="text-sm text-slate-300">Eventos ativos</p>
                  <p className="mt-2 text-4xl font-semibold text-[#f0bb50]">{dashboard?.events.length ?? 0}</p>
                  <p className="mt-2 text-sm text-slate-500">Monitoramento em tempo real</p>
                </div>
              </div>
              <p className="mt-4 text-sm text-slate-300">Sistema estável e sincronizado.</p>
            </ShellCard>

            {pendingConfirmation ? (
              <ShellCard eyebrow="Confirmação" title="Ação aguardando resposta">
                <p className="text-sm leading-6 text-slate-200">{pendingConfirmation}</p>
                <button type="button" onClick={onConfirmPending} className="mt-4 shell-primary-button">
                  Confirmar comando
                </button>
              </ShellCard>
            ) : (
              <ShellCard eyebrow="Ações rápidas" title="Fluxos prontos" className="flex flex-col">
                <p className="-mt-1 mb-4 text-sm text-slate-300">Escolha uma ação rápida para começar.</p>
                <div id="quick-flows" className="grid flex-1 gap-3 sm:grid-cols-2 xl:grid-cols-1">
                  {quickFlowCards.map((item) => {
                    const Icon = item.icon;
                    return (
                      <button
                        key={item.title}
                        type="button"
                        className="shell-inline-action"
                        onClick={() => {
                          if (item.command) {
                            onQuickAction(item.command);
                            return;
                          }
                          if (item.action === "briefing") {
                            onBriefing();
                            return;
                          }
                          if (item.action === "updates") {
                            onOpenUpdates();
                            return;
                          }
                          if (item.action === "finance") {
                            onOpenFinance();
                          }
                        }}
                      >
                        <div className="flex items-start gap-3">
                          <span className="mt-0.5 rounded-xl border border-white/10 bg-white/[0.05] p-2 text-[#54d8ff]">
                            <Icon className="h-4 w-4" />
                          </span>
                          <span>
                            <span className="block text-sm font-semibold text-white">{item.title}</span>
                            <span className="mt-1 block text-xs leading-5 text-slate-400">{item.description}</span>
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </ShellCard>
            )}
          </div>
        </div>
      </div>
    </section>
  );
}

function BrainView({
  memoryGraph,
}: {
  memoryGraph: MemoryGraphPayload | null;
}) {
  const [selectedNode, setSelectedNode] = useState<string>("");
  const [brainMode, setBrainMode] = useState<BrainMode>("brain");
  const [showTags, setShowTags] = useState(true);
  const [graphScale, setGraphScale] = useState(1);
  const [searchQuery, setSearchQuery] = useState("");
  const [areaFilter, setAreaFilter] = useState("all");
  const [tagFilter, setTagFilter] = useState("all");
  const [linkedOnly, setLinkedOnly] = useState(false);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [animatedNodes, setAnimatedNodes] = useState<BrainNode[]>([]);
  const [layoutSeed, setLayoutSeed] = useState(0);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const searchInputRef = useRef<HTMLInputElement | null>(null);
  const dragStateRef = useRef<
    | { type: "node"; nodeId: string; pointerId: number }
    | { type: "pan"; pointerId: number; startX: number; startY: number; panX: number; panY: number }
    | { type: "idle" }
  >({ type: "idle" });
  const panRef = useRef(pan);
  const scaleRef = useRef(graphScale);
  const nodesRef = useRef<BrainNode[]>([]);

  const graph = useMemo(
    () =>
      buildBrainGraph(memoryGraph, {
        mode: brainMode,
        showTags,
        search: searchQuery,
        areaFilter,
        tagFilter,
        linkedOnly,
        layoutSeed,
      }),
    [areaFilter, brainMode, layoutSeed, linkedOnly, memoryGraph, searchQuery, showTags, tagFilter],
  );
  const centerNodeId = graph.nodes.find((node) => node.nodeType === "vault")?.id ?? graph.nodes[0]?.id ?? "";
  const selectedPresent = graph.nodes.some((node) => node.id === selectedNode);
  const selected = (selectedPresent ? graph.nodes.find((node) => node.id === selectedNode) : undefined) ?? graph.nodes[0];
  const graphEdges = graph.edges;
  const connectedEdges = selected ? graphEdges.filter((edge) => edge.source === selected.id || edge.target === selected.id) : [];
  const connectedIds = new Set(connectedEdges.flatMap((edge) => [edge.source, edge.target]));
  const animatedNodeMap = new Map(animatedNodes.map((node) => [node.id, node]));
  const displayedSelected = selected ? animatedNodeMap.get(selected.id) ?? selected : undefined;
  const incomingLinks =
    selected?.nodeType === "note"
      ? graphEdges
          .filter((edge) => edge.relation === "links" && edge.target === selected.id)
          .map((edge) => graph.nodes.find((node) => node.id === edge.source))
          .filter((node): node is BrainNode => Boolean(node))
      : [];
  const outgoingLinks =
    selected?.nodeType === "note"
      ? graphEdges
          .filter((edge) => edge.relation === "links" && edge.source === selected.id)
          .map((edge) => graph.nodes.find((node) => node.id === edge.target))
          .filter((node): node is BrainNode => Boolean(node))
      : [];
  const selectedTags =
    selected?.nodeType === "note"
      ? graphEdges
          .filter((edge) => edge.relation === "tagged" && edge.source === selected.id)
          .map((edge) => graph.nodes.find((node) => node.id === edge.target))
          .filter((node): node is BrainNode => Boolean(node))
      : [];
  const areaCounts = graph.nodes
    .filter((node) => node.nodeType === "note")
    .reduce<Record<string, number>>((accumulator, node) => {
      accumulator[node.group] = (accumulator[node.group] ?? 0) + 1;
      return accumulator;
    }, {});
  const topArea = Object.entries(areaCounts).sort((left, right) => right[1] - left[1])[0];
  const tagCounts = graph.nodes
    .filter((node) => node.nodeType === "note")
    .flatMap((node) => graph.noteTags.get(node.id) ?? [])
    .reduce<Record<string, number>>((accumulator, tag) => {
      accumulator[tag] = (accumulator[tag] ?? 0) + 1;
      return accumulator;
    }, {});
  const topTag = Object.entries(tagCounts).sort((left, right) => right[1] - left[1])[0];
  const hottestNote = graph.nodes
    .filter((node) => node.nodeType === "note")
    .map((node) => ({
      node,
      degree: graphEdges.filter((edge) => edge.source === node.id || edge.target === node.id).length,
    }))
    .sort((left, right) => right.degree - left.degree)[0];
  const labels = {
    brain: "Mapa completo da memoria do Nexus, com notas reais, tags, areas e ligacoes do vault.",
    diary: "Filtro focado no diario para navegar pensamentos por contexto e backlinks.",
    dump: "Filtro do brain dump para capturar ideias soltas e como elas se conectam.",
  };

  useEffect(() => {
    panRef.current = pan;
  }, [pan]);

  useEffect(() => {
    scaleRef.current = graphScale;
  }, [graphScale]);

  useEffect(() => {
    if (!selectedPresent && centerNodeId) {
      setSelectedNode(centerNodeId);
    }
  }, [centerNodeId, selectedPresent]);

  useEffect(() => {
    if (!graph.nodes.length) {
      nodesRef.current = [];
      setAnimatedNodes([]);
      return;
    }

    const previousPositions = new Map(nodesRef.current.map((node) => [node.id, node]));
    const liveNodes = graph.nodes.map((node) => {
      const previous = previousPositions.get(node.id);
      return {
        ...node,
        x: previous?.x ?? node.x,
        y: previous?.y ?? node.y,
      };
    });
    nodesRef.current = liveNodes;
    setAnimatedNodes(liveNodes.map((node) => ({ ...node })));

    const velocity = new Map(liveNodes.map((node) => [node.id, { x: 0, y: 0 }]));
    const anchors = new Map(graph.nodes.map((node) => [node.id, { x: node.x, y: node.y }]));
    let frameId = 0;

    const tick = () => {
      const nodes = nodesRef.current;
      const nodeMap = new Map(nodes.map((node) => [node.id, node]));

      for (let index = 0; index < nodes.length; index += 1) {
        for (let inner = index + 1; inner < nodes.length; inner += 1) {
          const left = nodes[index];
          const right = nodes[inner];
          const dx = right.x - left.x;
          const dy = right.y - left.y;
          const distance = Math.max(Math.hypot(dx, dy), 1);
          const repel = (left.nodeType === "tag" || right.nodeType === "tag" ? 1600 : 2600) / (distance * distance);
          const forceX = (dx / distance) * repel;
          const forceY = (dy / distance) * repel;
          const leftVelocity = velocity.get(left.id)!;
          const rightVelocity = velocity.get(right.id)!;
          leftVelocity.x -= forceX;
          leftVelocity.y -= forceY;
          rightVelocity.x += forceX;
          rightVelocity.y += forceY;
        }
      }

      for (const edge of graph.edges) {
        const source = nodeMap.get(edge.source);
        const target = nodeMap.get(edge.target);
        if (!source || !target) {
          continue;
        }
        const dx = target.x - source.x;
        const dy = target.y - source.y;
        const distance = Math.max(Math.hypot(dx, dy), 1);
        const desired = edge.relation === "contains" ? 110 : edge.relation === "links" ? 145 : 170;
        const spring = edge.relation === "links" ? 0.004 : edge.relation === "tagged" ? 0.0026 : 0.003;
        const pull = (distance - desired) * spring;
        const forceX = (dx / distance) * pull;
        const forceY = (dy / distance) * pull;
        const sourceVelocity = velocity.get(source.id)!;
        const targetVelocity = velocity.get(target.id)!;
        sourceVelocity.x += forceX;
        sourceVelocity.y += forceY;
        targetVelocity.x -= forceX;
        targetVelocity.y -= forceY;
      }

      for (const node of nodes) {
        const anchor = anchors.get(node.id)!;
        const currentVelocity = velocity.get(node.id)!;
        currentVelocity.x += (anchor.x - node.x) * (node.nodeType === "vault" ? 0.018 : 0.0045);
        currentVelocity.y += (anchor.y - node.y) * (node.nodeType === "vault" ? 0.018 : 0.0045);
        currentVelocity.x *= 0.92;
        currentVelocity.y *= 0.92;

        if (dragStateRef.current.type === "node" && dragStateRef.current.nodeId === node.id) {
          currentVelocity.x = 0;
          currentVelocity.y = 0;
          continue;
        }

        node.x = Math.max(30, Math.min(GRAPH_WIDTH - 30, node.x + currentVelocity.x));
        node.y = Math.max(30, Math.min(GRAPH_HEIGHT - 30, node.y + currentVelocity.y));
      }

      setAnimatedNodes(nodes.map((node) => ({ ...node })));
      frameId = window.requestAnimationFrame(tick);
    };

    frameId = window.requestAnimationFrame(tick);
    return () => {
      window.cancelAnimationFrame(frameId);
    };
  }, [graph.edges, graph.nodes]);

  function screenToWorld(clientX: number, clientY: number) {
    const svg = svgRef.current;
    if (!svg) {
      return { x: GRAPH_CENTER.x, y: GRAPH_CENTER.y };
    }
    const rect = svg.getBoundingClientRect();
    const localX = ((clientX - rect.left) / rect.width) * GRAPH_WIDTH;
    const localY = ((clientY - rect.top) / rect.height) * GRAPH_HEIGHT;
    return {
      x: (localX - panRef.current.x) / scaleRef.current,
      y: (localY - panRef.current.y) / scaleRef.current,
    };
  }

  function focusNode(nodeId: string) {
    const targetNode = nodesRef.current.find((node) => node.id === nodeId) ?? graph.nodes.find((node) => node.id === nodeId);
    setSelectedNode(nodeId);
    if (!targetNode) {
      return;
    }
    setPan({
      x: GRAPH_CENTER.x - targetNode.x * scaleRef.current,
      y: GRAPH_CENTER.y - targetNode.y * scaleRef.current,
    });
  }

  function zoomAroundPoint(nextScale: number, clientX?: number, clientY?: number) {
    const clamped = Math.max(0.65, Math.min(2.2, Number(nextScale.toFixed(2))));
    if (clientX === undefined || clientY === undefined || !svgRef.current) {
      setGraphScale(clamped);
      return;
    }
    const rect = svgRef.current.getBoundingClientRect();
    const pointX = ((clientX - rect.left) / rect.width) * GRAPH_WIDTH;
    const pointY = ((clientY - rect.top) / rect.height) * GRAPH_HEIGHT;
    const worldX = (pointX - panRef.current.x) / scaleRef.current;
    const worldY = (pointY - panRef.current.y) / scaleRef.current;
    setGraphScale(clamped);
    setPan({
      x: pointX - worldX * clamped,
      y: pointY - worldY * clamped,
    });
  }

  return (
    <section className="space-y-6 px-4 py-8 lg:px-12">
      <div className="grid gap-4 xl:grid-cols-[0.95fr_1.35fr]">
        <ShellCard eyebrow="memoria viva" title="Modo cerebral">
          <div className="flex items-start gap-6">
            <div className="brain-score-ring">
              <span className="text-4xl font-semibold text-white">{graph.nodes.filter((node) => node.nodeType === "note").length}</span>
              <span className="text-[11px] uppercase tracking-[0.26em] text-slate-500">notas</span>
            </div>
            <div>
              <p className="max-w-md text-sm leading-7 text-slate-300">{labels[brainMode]}</p>
              <div className="mt-4 flex flex-wrap gap-4 text-sm text-slate-400">
                <span>{graph.nodes.filter((node) => node.nodeType === "area").length} areas</span>
                <span>{graph.nodes.filter((node) => node.nodeType === "tag").length} tags</span>
                <span>{graphEdges.filter((edge) => edge.relation === "links").length} links reais</span>
                <span>{showTags ? "tags visiveis" : "tags ocultas"}</span>
              </div>
            </div>
          </div>
        </ShellCard>

        <ShellCard eyebrow="padroes e contexto" title={memoryGraph?.vault_name || "Memoria desconectada"} right={<span className="text-sm text-slate-400">{memoryGraph?.stats.notes ?? 0} notas totais</span>}>
          <div className="grid gap-4 md:grid-cols-3">
            <div className="rounded-[22px] border border-white/6 bg-white/[0.03] p-4">
              <p className="shell-eyebrow">area dominante</p>
              <p className="mt-3 text-xl font-semibold text-white">{topArea?.[0] ?? "sem dados"}</p>
              <p className="mt-2 text-sm text-slate-400">{topArea ? `${topArea[1]} notas visiveis` : "ajuste os filtros para analisar"}</p>
            </div>
            <div className="rounded-[22px] border border-white/6 bg-white/[0.03] p-4">
              <p className="shell-eyebrow">tag em destaque</p>
              <p className="mt-3 text-xl font-semibold text-[#54d8ff]">{topTag?.[0] ?? "sem tags"}</p>
              <p className="mt-2 text-sm text-slate-400">{topTag ? `${topTag[1]} notas relacionadas` : "tags aparecem quando houver relacoes"}</p>
            </div>
            <div className="rounded-[22px] border border-white/6 bg-white/[0.03] p-4">
              <p className="shell-eyebrow">nucleo ativo</p>
              <p className="mt-3 text-xl font-semibold text-white">{hottestNote?.node.label ?? "sem foco"}</p>
              <p className="mt-2 text-sm text-slate-400">{hottestNote ? `${hottestNote.degree} conexoes visiveis` : "sem links no filtro atual"}</p>
            </div>
          </div>
        </ShellCard>
      </div>

      <ShellCard eyebrow="filtros avancados" title="Explorar memoria">
        <div className="grid gap-4 xl:grid-cols-[1.2fr_1fr]">
          <div className="space-y-4">
            <div className="relative">
              <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
              <input
                ref={searchInputRef}
                value={searchQuery}
                onChange={(event) => setSearchQuery(event.target.value)}
                placeholder="Filtrar por titulo, pasta, tag ou palavra-chave"
                className="w-full rounded-full border border-white/10 bg-[#0d1421] py-3 pl-11 pr-4 text-sm text-white outline-none transition focus:border-[#54d8ff]/40"
              />
            </div>
            <div className="flex flex-wrap gap-2">
              {[
                ["brain", "Cerebro"],
                ["diary", "Diario"],
                ["dump", "Brain dump"],
              ].map(([value, label]) => (
                <button
                  key={value}
                  type="button"
                  className={`shell-pill-button ${brainMode === value ? "shell-pill-button-active" : ""}`}
                  onClick={() => {
                    setBrainMode(value as BrainMode);
                    setSelectedNode(centerNodeId);
                  }}
                >
                  {label}
                </button>
              ))}
              <button type="button" className={`shell-pill-button ${showTags ? "shell-pill-button-active" : ""}`} onClick={() => setShowTags((current) => !current)}>
                {showTags ? "Tags on" : "Tags off"}
              </button>
              <button type="button" className={`shell-pill-button ${linkedOnly ? "shell-pill-button-active" : ""}`} onClick={() => setLinkedOnly((current) => !current)}>
                so conectadas
              </button>
            </div>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <p className="mb-3 shell-eyebrow">pastas</p>
              <div className="flex flex-wrap gap-2">
                <button type="button" className={`shell-chip ${areaFilter === "all" ? "shell-chip-active" : ""}`} onClick={() => setAreaFilter("all")}>
                  todas
                </button>
                {graph.areas.map((area) => (
                  <button key={area} type="button" className={`shell-chip ${areaFilter === area ? "shell-chip-active" : ""}`} onClick={() => setAreaFilter(area)}>
                    {area}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <p className="mb-3 shell-eyebrow">tags</p>
              <div className="flex max-h-[112px] flex-wrap gap-2 overflow-y-auto pr-2">
                <button type="button" className={`shell-chip ${tagFilter === "all" ? "shell-chip-active" : ""}`} onClick={() => setTagFilter("all")}>
                  todas
                </button>
                {graph.tags.map((tag) => (
                  <button key={tag} type="button" className={`shell-chip ${tagFilter === tag ? "shell-chip-active" : ""}`} onClick={() => setTagFilter(tag)}>
                    {tag}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </ShellCard>

      <div className="grid gap-5 xl:grid-cols-[1.55fr_0.75fr]">
        <ShellCard className="overflow-hidden">
          <div className="mb-4 flex items-center justify-between gap-4 text-sm text-slate-400">
            <div className="flex flex-wrap gap-5">
              <span>arraste nos para reorganizar</span>
              <span>arraste o fundo para mover</span>
              <span>scroll para zoom</span>
            </div>
            <div className="flex items-center gap-2">
              <button type="button" className="shell-chip" onClick={() => zoomAroundPoint(graphScale - 0.12)}>
                <ZoomOut className="h-4 w-4" />
              </button>
              <button type="button" className="shell-chip" onClick={() => zoomAroundPoint(graphScale + 0.12)}>
                <ZoomIn className="h-4 w-4" />
              </button>
              <button
                type="button"
                className="shell-chip"
                onClick={() => {
                  setGraphScale(1);
                  setPan({ x: 0, y: 0 });
                  setSelectedNode(centerNodeId);
                }}
              >
                <RefreshCcw className="h-4 w-4" />
              </button>
            </div>
          </div>

          <div className="brain-canvas-shell relative -mx-2 overflow-hidden rounded-[40px] px-2 py-1">
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_45%,rgba(75,130,220,0.18),transparent_26%),radial-gradient(circle_at_18%_20%,rgba(51,195,230,0.12),transparent_24%),radial-gradient(circle_at_82%_80%,rgba(106,116,255,0.12),transparent_28%)]" />
            <div className="pointer-events-none absolute inset-0 rounded-[40px] bg-[linear-gradient(180deg,rgba(4,8,18,0.1),rgba(4,8,18,0.45))]" />
            {!memoryGraph?.enabled ? (
              <div className="flex h-[620px] items-center justify-center rounded-[26px] border border-dashed border-white/10 bg-white/[0.02] text-center">
                <div className="max-w-md space-y-3 px-6">
                  <p className="text-lg font-semibold text-white">Memoria ainda nao conectada</p>
                  <p className="text-sm leading-6 text-slate-400">
                    O modo Cerebro depende do vault real do Obsidian. Quando o caminho estiver ativo, esta tela vira o mapa vivo de conhecimento do Nexus.
                  </p>
                </div>
              </div>
            ) : (
              <svg
                ref={svgRef}
                viewBox={`0 0 ${GRAPH_WIDTH} ${GRAPH_HEIGHT}`}
                className="brain-canvas h-[620px] w-full cursor-grab touch-none select-none"
                onWheel={(event) => {
                  event.preventDefault();
                  zoomAroundPoint(graphScale + (event.deltaY < 0 ? 0.12 : -0.12), event.clientX, event.clientY);
                }}
                onPointerDown={(event) => {
                  if (event.target !== svgRef.current) {
                    return;
                  }
                  dragStateRef.current = {
                    type: "pan",
                    pointerId: event.pointerId,
                    startX: event.clientX,
                    startY: event.clientY,
                    panX: panRef.current.x,
                    panY: panRef.current.y,
                  };
                  svgRef.current?.setPointerCapture(event.pointerId);
                }}
                onPointerMove={(event) => {
                  const dragState = dragStateRef.current;
                  if (dragState.type === "node") {
                    const draggedNode = nodesRef.current.find((node) => node.id === dragState.nodeId);
                    if (!draggedNode) {
                      return;
                    }
                    const nextPosition = screenToWorld(event.clientX, event.clientY);
                    draggedNode.x = nextPosition.x;
                    draggedNode.y = nextPosition.y;
                    setAnimatedNodes(nodesRef.current.map((node) => ({ ...node })));
                    return;
                  }
                  if (dragState.type === "pan") {
                    const deltaX = event.clientX - dragState.startX;
                    const deltaY = event.clientY - dragState.startY;
                    setPan({
                      x: dragState.panX + deltaX,
                      y: dragState.panY + deltaY,
                    });
                  }
                }}
                onPointerUp={(event) => {
                  if (dragStateRef.current.type !== "idle") {
                    svgRef.current?.releasePointerCapture(event.pointerId);
                  }
                  dragStateRef.current = { type: "idle" };
                }}
                onPointerLeave={() => {
                  if (dragStateRef.current.type === "node") {
                    dragStateRef.current = { type: "idle" };
                  }
                }}
              >
                <defs>
                  <radialGradient id="brain-core-glow">
                    <stop offset="0%" stopColor="rgba(101, 116, 255, 0.34)" />
                    <stop offset="100%" stopColor="rgba(101, 116, 255, 0)" />
                  </radialGradient>
                </defs>
                <rect x="0" y="0" width={GRAPH_WIDTH} height={GRAPH_HEIGHT} fill="transparent" />
                <g transform={`translate(${pan.x} ${pan.y}) scale(${graphScale})`}>
                  <circle cx={GRAPH_CENTER.x} cy={GRAPH_CENTER.y} r="360" fill="url(#brain-core-glow)" />
                  {graphEdges.map((edge) => {
                    const source = animatedNodeMap.get(edge.source) ?? graph.nodes.find((node) => node.id === edge.source);
                    const target = animatedNodeMap.get(edge.target) ?? graph.nodes.find((node) => node.id === edge.target);
                    if (!source || !target) {
                      return null;
                    }
                    const highlighted = selected ? edge.source === selected.id || edge.target === selected.id : false;
                    return (
                      <line
                        key={`edge-${edge.source}-${edge.target}-${edge.relation}`}
                        x1={source.x}
                        y1={source.y}
                        x2={target.x}
                        y2={target.y}
                        stroke={
                          edge.relation === "links"
                            ? highlighted
                              ? "rgba(128, 116, 255, 0.78)"
                              : "rgba(128, 116, 255, 0.28)"
                            : edge.relation === "tagged"
                              ? highlighted
                                ? "rgba(47, 225, 177, 0.62)"
                                : "rgba(47, 225, 177, 0.18)"
                              : highlighted
                                ? "rgba(84, 216, 255, 0.5)"
                                : "rgba(84, 216, 255, 0.12)"
                        }
                        strokeDasharray={edge.relation === "tagged" ? "3 7" : "0"}
                        strokeWidth={highlighted ? 1.8 : 1.1}
                      />
                    );
                  })}
                  {animatedNodes.map((node) => {
                    const active = node.id === selected?.id;
                    const related = active || connectedIds.has(node.id);
                    const fill =
                      node.nodeType === "vault"
                        ? "rgba(88, 117, 255, 0.95)"
                        : node.nodeType === "area"
                          ? "rgba(104, 117, 255, 0.72)"
                          : node.nodeType === "note"
                            ? "rgba(130, 148, 255, 0.66)"
                            : "rgba(74, 187, 255, 0.56)";

                    return (
                      <g
                        key={node.id}
                        className="cursor-pointer"
                        onPointerDown={(event) => {
                          event.stopPropagation();
                          dragStateRef.current = { type: "node", nodeId: node.id, pointerId: event.pointerId };
                          svgRef.current?.setPointerCapture(event.pointerId);
                          setSelectedNode(node.id);
                        }}
                        onDoubleClick={() => focusNode(node.id)}
                        onClick={() => setSelectedNode(node.id)}
                      >
                        <circle cx={node.x} cy={node.y} r={node.size + (active ? 12 : related ? 5 : 0)} fill={active ? "rgba(84, 216, 255, 0.14)" : "rgba(84, 216, 255, 0.05)"} />
                        <circle cx={node.x} cy={node.y} r={node.size} fill={fill} />
                        <text
                          x={node.x}
                          y={node.y + node.size + 18}
                          textAnchor="middle"
                          fill={active ? "rgba(245, 248, 255, 0.98)" : related ? "rgba(201, 216, 240, 0.88)" : "rgba(168, 180, 202, 0.62)"}
                          fontSize={active ? 14 : 11.5}
                        >
                          {node.label}
                        </text>
                      </g>
                    );
                  })}
                </g>
              </svg>
            )}

            <div className="absolute bottom-6 left-6 rounded-[22px] border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-slate-300">
              <div className="space-y-2">
                <div className="flex items-center gap-3">
                  <span className="h-3 w-3 rounded-full bg-[#6a74ff]" />
                  <span>Area / pasta</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="h-3 w-3 rounded-full bg-[#4abbff]" />
                  <span>Tag</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="h-3 w-3 rounded-full bg-[#93a0ff]" />
                  <span>Nota / caderno</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="h-px w-6 bg-[#785dff]" />
                  <span>Link entre notas</span>
                </div>
              </div>
            </div>

            <div className="absolute right-5 top-5 flex flex-col gap-3 rounded-[18px] border border-white/10 bg-white/[0.04] p-3 text-slate-300">
              <button
                type="button"
                className="brain-tool-button"
                title="Focar busca"
                onClick={() => searchInputRef.current?.focus()}
              >
                <Search className="h-4 w-4" />
              </button>
              <button
                type="button"
                className="brain-tool-button"
                title="Centralizar mapa"
                onClick={() => {
                  setPan({ x: 0, y: 0 });
                  setGraphScale(1);
                  setSelectedNode(centerNodeId);
                }}
              >
                <Grip className="h-4 w-4" />
              </button>
              <button
                type="button"
                className={`brain-tool-button ${layoutSeed > 0 ? "brain-tool-button-active" : ""}`}
                title="Soltar o grafo"
                onClick={() => setLayoutSeed((current) => current + 1)}
              >
                <Sparkles className="h-4 w-4" />
              </button>
              <button
                type="button"
                className={`brain-tool-button ${linkedOnly ? "brain-tool-button-active" : ""}`}
                title="Mostrar so conectadas"
                onClick={() => setLinkedOnly((current) => !current)}
              >
                <Link2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        </ShellCard>

        <div className="grid gap-5">
          <ShellCard eyebrow="selecionado" title={selected?.label ?? "NEXUS"}>
            <div className="space-y-4 text-sm text-slate-300">
              <p>
                {selected?.nodeType === "vault"
                  ? "Vault principal da memoria do Nexus. Ele concentra as areas e o mapa inteiro."
                  : selected?.nodeType === "area"
                    ? "Area da memoria. Use para focar uma pasta inteira e navegar pelas notas relacionadas."
                    : selected?.nodeType === "note"
                      ? "Nota real do Obsidian. Aqui voce consegue ver backlinks, saidas e tags conectadas."
                      : "Tag usada para agrupar conhecimento e revelar padroes no grafo."}
              </p>
              <div className="rounded-[20px] border border-white/6 bg-white/[0.02] p-4">
                <p className="shell-eyebrow">caminho</p>
                <p className="mt-3 break-all text-sm leading-6 text-slate-200">{selected?.path || memoryGraph?.vault_path || "sem caminho"}</p>
              </div>
              <div className="grid gap-4 md:grid-cols-2">
                <div className="rounded-[20px] border border-white/6 bg-white/[0.02] p-4">
                  <p className="shell-eyebrow">tipo</p>
                  <p className="mt-3 text-lg font-semibold text-[#54d8ff]">
                    {selected?.nodeType === "vault" ? "vault" : selected?.nodeType === "area" ? "area" : selected?.nodeType === "note" ? "nota" : "tag"}
                  </p>
                </div>
                <div className="rounded-[20px] border border-white/6 bg-white/[0.02] p-4">
                  <p className="shell-eyebrow">conexoes</p>
                  <p className="mt-3 text-lg font-semibold text-white">{connectedEdges.length}</p>
                </div>
              </div>
              <div className="rounded-[20px] border border-white/6 bg-white/[0.02] p-4">
                <p className="shell-eyebrow">tags da nota</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {selectedTags.length ? (
                    selectedTags.map((tag) => (
                      <button key={tag.id} type="button" className="shell-chip" onClick={() => focusNode(tag.id)}>
                        {tag.label}
                      </button>
                    ))
                  ) : (
                    <span className="text-sm text-slate-500">sem tags conectadas na selecao atual</span>
                  )}
                </div>
              </div>
              <div className="rounded-[20px] border border-white/6 bg-white/[0.02] p-4">
                <p className="shell-eyebrow">links inversos</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {incomingLinks.length ? (
                    incomingLinks.map((node) => (
                      <button key={node.id} type="button" className="shell-inline-action !w-auto !rounded-full !px-4 !py-2" onClick={() => focusNode(node.id)}>
                        {node.label}
                      </button>
                    ))
                  ) : (
                    <span className="text-sm text-slate-500">ninguem cita esta nota no filtro atual</span>
                  )}
                </div>
              </div>
              <div className="rounded-[20px] border border-white/6 bg-white/[0.02] p-4">
                <p className="shell-eyebrow">esta nota aponta para</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {outgoingLinks.length ? (
                    outgoingLinks.map((node) => (
                      <button key={node.id} type="button" className="shell-inline-action !w-auto !rounded-full !px-4 !py-2" onClick={() => focusNode(node.id)}>
                        {node.label}
                      </button>
                    ))
                  ) : (
                    <span className="text-sm text-slate-500">sem saidas diretas no filtro atual</span>
                  )}
                </div>
              </div>
              <div className="rounded-[20px] border border-white/6 bg-white/[0.02] p-4">
                <p className="shell-eyebrow">acoes</p>
                <div className="mt-3 grid gap-2">
                  <button type="button" className="shell-primary-button w-full" onClick={() => focusNode(centerNodeId)}>
                    voltar ao centro
                  </button>
                  {displayedSelected ? (
                    <button type="button" className="shell-chip w-full" onClick={() => focusNode(displayedSelected.id)}>
                      centralizar selecao
                    </button>
                  ) : null}
                </div>
              </div>
            </div>
          </ShellCard>
        </div>
      </div>
    </section>
  );
}

function TasksView({ modules }: { modules: DashboardModule[] }) {
  const [taskFilter, setTaskFilter] = useState<TaskFilter>("all");
  const [showProjectBadgeOnly, setShowProjectBadgeOnly] = useState(false);
  const [selectedTaskDay, setSelectedTaskDay] = useState(11);
  const done = modules.filter((module) => module.status === "ready").length;
  const filteredTasks = taskRows.filter((task) => {
    if (taskFilter === "recurring" && !task.recurring) {
      return false;
    }
    if (taskFilter === "normal" && task.recurring) {
      return false;
    }
    if (showProjectBadgeOnly && !task.project) {
      return false;
    }
    return true;
  });

  return (
    <section className="space-y-6 px-4 py-8 lg:px-12">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-4xl font-semibold text-white">Tarefas</h2>
          <p className="mt-2 text-sm uppercase tracking-[0.3em] text-[#54d8ff]">live</p>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.1fr_1.7fr]">
        <ShellCard>
          <div className="flex items-start gap-6">
            <div className="brain-score-ring border-[#f0bb50]/50">
              <span className="text-3xl font-semibold text-[#f0bb50]">85</span>
              <span className="text-[11px] uppercase tracking-[0.26em] text-slate-500">saude</span>
            </div>
            <div className="flex-1">
              <p className="text-sm text-slate-300">
                <span className="text-white">{filteredTasks.length}</span> tarefas · <span className="text-[#f37588]">2 atrasadas</span> ·{" "}
                <span className="text-white">{Math.max(filteredTasks.length - done, 0)}</span> pendentes
              </p>
              <p className="mt-3 text-2xl text-white">Quase limpo — 2 atrasadas</p>
              <div className="mt-6 h-px bg-white/10" />
              <div className="mt-5">
                <p className="text-[11px] uppercase tracking-[0.26em] text-slate-500">taxa de conclusao</p>
                <div className="mt-4 h-1.5 rounded-full bg-white/8">
                  <div className="h-1.5 w-[15%] rounded-full bg-[#f37588]" />
                </div>
                <div className="mt-2 flex items-center justify-between text-sm">
                  <span className="text-[#f37588]">atencao necessaria</span>
                  <span className="text-[#f37588]">15%</span>
                </div>
              </div>
            </div>
          </div>
        </ShellCard>

        <ShellCard>
          <div className="grid grid-cols-4 border-b border-white/8 pb-5">
            {[
              ["total", filteredTasks.length],
              ["atrasadas", filteredTasks.filter((task) => task.status === "late").length],
              ["pendentes", filteredTasks.filter((task) => task.status !== "late").length],
              ["feitas", done],
            ].map(([label, value], index) => (
              <div key={label} className={index < 3 ? "border-r border-white/8 pr-4" : ""}>
                <p className="shell-eyebrow">{label}</p>
                <p className={`mt-2 text-4xl font-semibold ${index === 1 ? "text-[#f37588]" : index === 2 ? "text-[#f0bb50]" : index === 3 ? "text-[#2fe1b1]" : "text-[#54d8ff]"}`}>
                  {value}
                </p>
              </div>
            ))}
          </div>
          <div className="mt-6 h-[196px] rounded-[26px] border border-white/6 bg-white/[0.02] p-4">
            <div className="flex items-center justify-between text-xs uppercase tracking-[0.24em] text-slate-500">
              <span>ultimos 7 dias</span>
              <span>{selectedTaskDay}/05 selecionado</span>
            </div>
          </div>
        </ShellCard>
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.35fr_1fr]">
        <ShellCard>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <div className="flex gap-2">
              {[
                ["all", "Todas"],
                ["normal", "Normais"],
                ["recurring", "Recorrentes"],
              ].map(([value, label]) => (
                <button key={value} type="button" className={`shell-chip ${taskFilter === value ? "shell-chip-active" : ""}`} onClick={() => setTaskFilter(value as TaskFilter)}>
                  {label}
                </button>
              ))}
            </div>
            <button type="button" className={`shell-chip ${showProjectBadgeOnly ? "shell-chip-active" : ""}`} onClick={() => setShowProjectBadgeOnly((current) => !current)}>
              Todos projetos
            </button>
          </div>
          <div className="overflow-hidden rounded-[26px] border border-white/8">
            <div className="border-b border-[#5f3948] bg-[#281c28]/70 px-5 py-4 text-sm uppercase tracking-[0.24em] text-[#c16d7b]">
              atrasadas e proximas
            </div>
            <div className="divide-y divide-white/6">
              {filteredTasks.map((task) => (
                <div key={`${task.title}-${task.date}`} className="grid gap-4 px-5 py-4 md:grid-cols-[1fr_auto]">
                  <div className="flex items-start gap-3">
                    <span className={`mt-2 h-3 w-3 rounded-full border ${task.tone === "danger" ? "border-[#f37588]" : task.tone === "warning" ? "border-[#f0bb50]" : "border-[#2fe1b1]"}`} />
                    <div>
                      <p className="text-lg text-slate-100">{task.title}</p>
                      <div className="mt-2 flex flex-wrap gap-3 text-sm text-slate-500">
                        <span>{task.area}</span>
                        <span>{task.project}</span>
                        {task.recurring ? <span>recorrente</span> : null}
                      </div>
                    </div>
                  </div>
                  <div className="text-right text-sm text-slate-200">
                    <p>{task.date}</p>
                    <p className="mt-1">{task.time}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </ShellCard>

        <ShellCard title="Maio 2026">
          <div className="grid grid-cols-7 gap-3 text-center text-sm">
            {["D", "S", "T", "Q", "Q", "S", "S"].map((day) => (
              <span key={day} className="pb-3 text-slate-500">
                {day}
              </span>
            ))}
            {Array.from({ length: 35 }, (_unused, index) => {
              const number = index - 3;
              const active = number === selectedTaskDay;
              return (
                <button
                  key={`day-${index}`}
                  type="button"
                  onClick={() => {
                    if (number > 0 && number <= 31) {
                      setSelectedTaskDay(number);
                    }
                  }}
                  className={`rounded-[18px] px-2 py-5 text-slate-300 ${active ? "bg-[#163444] text-[#54d8ff]" : "bg-white/[0.015]"}`}
                >
                  {number > 0 && number <= 31 ? number : ""}
                </button>
              );
            })}
          </div>
        </ShellCard>
      </div>
    </section>
  );
}

function RemindersView({ onQuickReminder }: { onQuickReminder: () => void }) {
  const [reminderKindFilter, setReminderKindFilter] = useState<"all" | "normal" | "recurring">("all");
  const [reminderTab, setReminderTab] = useState<ReminderTab>("expired");
  const filteredReminders = reminderRows.filter((item) => {
    if (reminderKindFilter !== "all" && item.kind !== reminderKindFilter) {
      return false;
    }
    return item.status === reminderTab;
  });

  return (
    <section className="space-y-6 px-4 py-8 lg:px-12">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="text-4xl font-semibold text-white">Lembretes</h2>
          <p className="mt-2 text-sm uppercase tracking-[0.3em] text-[#54d8ff]">live</p>
        </div>
        <button type="button" onClick={onQuickReminder} className="shell-chip">
          criar via chat
        </button>
      </div>

      <div className="grid gap-4 md:grid-cols-4">
        {[
          ["total", String(reminderRows.length), "#f38c3f"],
          ["hoje", String(reminderRows.filter((row) => row.status === "today").length), "#f0bb50"],
          ["expirados", String(reminderRows.filter((row) => row.status === "expired").length), "#f37588"],
          ["dispensados", "0", "#2fe1b1"],
        ].map(([label, value, color]) => (
          <ShellCard key={label}>
            <p className="shell-eyebrow">{label}</p>
            <p className="mt-3 text-5xl font-semibold" style={{ color }}>
              {value}
            </p>
          </ShellCard>
        ))}
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.35fr_1fr]">
        <ShellCard>
          <div className="flex items-start gap-6">
            <div className="brain-score-ring border-[#f0bb50]/50">
              <span className="text-3xl font-semibold text-[#f0bb50]">50</span>
              <span className="text-[11px] uppercase tracking-[0.26em] text-slate-500">saude</span>
            </div>
            <div>
              <p className="text-lg text-slate-200">
                {reminderRows.length} lembretes · {reminderRows.filter((row) => row.status === "expired").length} expirados ·{" "}
                {reminderRows.filter((row) => row.status === "upcoming").length} pendentes ·{" "}
                {reminderRows.filter((row) => row.status === "today").length} hoje
              </p>
              <p className="mt-3 text-xl text-[#f0bb50]">4 expirados precisam atencao</p>
            </div>
          </div>
          <div className="mt-6 flex flex-wrap items-center justify-between gap-3 border-t border-white/8 pt-5">
            <div className="flex gap-2">
              {[
                ["all", "Todas"],
                ["normal", "Normais"],
                ["recurring", "Recorrentes"],
              ].map(([value, label]) => (
                <button key={value} type="button" className={`shell-chip ${reminderKindFilter === value ? "shell-chip-active" : ""}`} onClick={() => setReminderKindFilter(value as "all" | "normal" | "recurring")}>
                  {label}
                </button>
              ))}
            </div>
            <div className="flex gap-2">
              {[
                ["upcoming", "Proximos"],
                ["today", "Hoje"],
                ["expired", "Expirados"],
                ["history", "Historico"],
              ].map(([value, label]) => (
                <button key={value} type="button" className={`shell-chip ${reminderTab === value ? "shell-chip-active" : ""}`} onClick={() => setReminderTab(value as ReminderTab)}>
                  {label}
                </button>
              ))}
            </div>
          </div>
          <div className="mt-4 rounded-[26px] border border-[#5f3948] bg-[#211823]">
            <div className="border-b border-[#5f3948] px-5 py-4 text-sm uppercase tracking-[0.24em] text-[#c16d7b]">
              {reminderTab}
            </div>
            <div className="divide-y divide-white/6">
              {filteredReminders.map((item) => (
                <div key={`${item.title}-${item.date}`} className="grid gap-4 px-5 py-4 md:grid-cols-[1fr_auto]">
                  <div className="flex items-start gap-3">
                    <span className="mt-2 h-3 w-3 rounded-full border border-[#f37588]" />
                    <div>
                      <p className="text-lg text-slate-100">{item.title}</p>
                      <p className="mt-2 text-sm text-slate-500">{item.kind === "recurring" ? "recorrente" : "normal"}</p>
                    </div>
                  </div>
                  <div className="text-right text-sm text-slate-200">
                    <p>{item.time}</p>
                    <p className="mt-1">{item.date}</p>
                  </div>
                </div>
              ))}
              {filteredReminders.length === 0 ? <div className="px-5 py-6 text-sm text-slate-400">Nenhum lembrete nessa combinacao.</div> : null}
            </div>
          </div>
        </ShellCard>

        <ShellCard title="Maio 2026">
          <div className="grid grid-cols-7 gap-3 text-center text-sm">
            {["D", "S", "T", "Q", "Q", "S", "S"].map((day) => (
              <span key={day} className="pb-3 text-slate-500">
                {day}
              </span>
            ))}
            {Array.from({ length: 35 }, (_unused, index) => {
              const number = index - 1;
              const alert = number === 5;
              return (
                <div key={`rem-${index}`} className={`rounded-[18px] px-2 py-5 text-slate-300 ${alert ? "bg-[#3a2a31]" : "bg-white/[0.015]"}`}>
                  {number > 0 && number <= 31 ? number : ""}
                </div>
              );
            })}
          </div>
        </ShellCard>
      </div>
    </section>
  );
}

function FinanceView() {
  const [financeFilter, setFinanceFilter] = useState<FinanceFilter>("all");
  const [selectedFinanceDay, setSelectedFinanceDay] = useState(11);
  const [projectionEnabled, setProjectionEnabled] = useState(false);
  const [lateOnly, setLateOnly] = useState(false);
  const bankOptions = useMemo(() => ["Banco: Todos", ...Array.from(new Set(financeRows.map((row) => `Banco: ${splitFinanceCategory(row.category).bank}`)))], []);
  const categoryOptions = useMemo(() => ["Categoria: Todas", ...Array.from(new Set(financeRows.map((row) => `Categoria: ${splitFinanceCategory(row.category).group}`)))], []);
  const movementOptions = ["Tipo: Todos", "Tipo: Entradas", "Tipo: Saidas"];
  const [bankFilter, setBankFilter] = useState(bankOptions[0] ?? "Banco: Todos");
  const [categoryFilter, setCategoryFilter] = useState(categoryOptions[0] ?? "Categoria: Todas");
  const [movementFilter, setMovementFilter] = useState("Tipo: Todos");

  const filteredFinance = financeRows.filter((item) => {
    if (financeFilter !== "all" && item.type !== financeFilter) {
      return false;
    }
    const meta = splitFinanceCategory(item.category);
    if (bankFilter !== "Banco: Todos" && bankFilter !== `Banco: ${meta.bank}`) {
      return false;
    }
    if (categoryFilter !== "Categoria: Todas" && categoryFilter !== `Categoria: ${meta.group}`) {
      return false;
    }
    if (movementFilter === "Tipo: Entradas" && item.tone !== "income") {
      return false;
    }
    if (movementFilter === "Tipo: Saidas" && item.tone !== "expense") {
      return false;
    }
    if (lateOnly && !item.late) {
      return false;
    }
    return true;
  });

  return (
    <section className="space-y-6 px-4 py-8 lg:px-12">
      <div className="grid gap-6 xl:grid-cols-[0.85fr_1.35fr]">
        <ShellCard>
          <p className="text-6xl font-light text-white">{projectionEnabled ? "R$ 612" : "R$ 331"}</p>
          <div className="mt-7 h-1.5 rounded-full bg-[linear-gradient(90deg,rgba(57,217,255,0.58),rgba(243,117,136,0.58))]" />
          <div className="mt-4 flex gap-6 text-sm">
            <span className="text-[#54d8ff]">{projectionEnabled ? "R$ 2.804" : "R$ 2.404"}</span>
            <span className="text-[#f4a0b1]">{projectionEnabled ? "R$ 2.192" : "R$ 2.073"}</span>
          </div>
        </ShellCard>

        <ShellCard title="Maio 2026" right={<HelpCircle className="h-4 w-4 text-slate-400" />}>
          <svg viewBox="0 0 720 180" className="h-40 w-full">
            <path
              d="M10 120 C 70 90, 90 150, 140 120 S 210 40, 250 118 S 330 120, 710 120"
              fill="none"
              stroke="rgba(45, 225, 203, 0.88)"
              strokeWidth="3"
            />
            <path
              d="M10 90 C 70 160, 90 102, 140 118 S 210 76, 250 120 S 330 120, 710 120"
              fill="none"
              stroke="rgba(244, 128, 152, 0.68)"
              strokeWidth="2.5"
            />
            <line x1="250" y1="18" x2="250" y2="138" stroke="rgba(255,255,255,0.2)" strokeDasharray="4 6" />
            <circle cx="250" cy="120" r="4" fill="rgba(244, 128, 152, 0.9)" />
          </svg>
        </ShellCard>
      </div>

      <div className="flex flex-wrap items-center gap-4">
        {[
          ["all", "Todas"],
          ["variable", "Variaveis"],
          ["recurring", "Recorrentes"],
          ["installments", "Parceladas"],
        ].map(([value, label]) => (
          <button key={value} type="button" className={`shell-pill-button ${financeFilter === value ? "shell-pill-button-active" : ""}`} onClick={() => setFinanceFilter(value as FinanceFilter)}>
            {label}
          </button>
        ))}
        <div className="ml-auto flex flex-wrap items-center gap-3">
          <Search className="h-4 w-4 text-slate-400" />
          <button type="button" className="shell-chip" onClick={() => setBankFilter((current) => cycleOption(current, bankOptions))}>
            {bankFilter}
          </button>
          <button type="button" className="shell-chip" onClick={() => setCategoryFilter((current) => cycleOption(current, categoryOptions))}>
            {categoryFilter}
          </button>
          <button type="button" className="shell-chip" onClick={() => setMovementFilter((current) => cycleOption(current, movementOptions))}>
            {movementFilter}
          </button>
          <button type="button" className={`shell-pill-button ${projectionEnabled ? "shell-pill-button-active" : ""}`} onClick={() => setProjectionEnabled((current) => !current)}>
            Projecao
          </button>
          <button type="button" className={`shell-pill-button ${lateOnly ? "shell-pill-button-active" : ""}`} onClick={() => setLateOnly((current) => !current)}>
            Atrasadas
          </button>
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-[1.35fr_0.9fr]">
        <ShellCard>
          <div className="grid grid-cols-7 gap-4 text-center text-sm">
            {["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sab"].map((day) => (
              <span key={day} className="pb-2 text-slate-500">
                {day}
              </span>
            ))}
            {Array.from({ length: 35 }, (_unused, index) => {
              const number = index + 1;
              const strong = number === selectedFinanceDay;
              const hasChip = number === 1 || number === 5;
              return (
                <button
                  key={`fin-${index}`}
                  type="button"
                  onClick={() => {
                    if (number <= 31) {
                      setSelectedFinanceDay(number);
                    }
                  }}
                  className={`rounded-[18px] px-2 py-5 text-slate-300 ${strong ? "bg-[#173240] text-[#54d8ff]" : "bg-white/[0.015]"}`}
                >
                  {number <= 31 ? number : ""}
                  {hasChip ? <div className="mt-2 text-xs text-[#f37588]">{number === 1 ? "-R$ 666" : "+R$ 937"}</div> : null}
                </button>
              );
            })}
          </div>
        </ShellCard>

        <ShellCard title={lateOnly ? "Atrasadas" : "Todas"} right={<span className="text-sm text-slate-400">{filteredFinance.length}</span>}>
          <div className="space-y-5">
            {filteredFinance.map((row) => (
              <div key={`${row.title}-${row.date}`} className="rounded-[20px] border border-white/6 bg-white/[0.02] px-4 py-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-lg text-slate-100">{row.title}</p>
                    <p className="mt-2 text-sm text-slate-500">{row.category}</p>
                  </div>
                  <div className="text-right">
                    <p className={`text-lg font-semibold ${row.tone === "income" ? "text-[#2fe1b1]" : "text-[#f37588]"}`}>{row.value}</p>
                    <p className="mt-2 text-sm text-slate-500">{row.date}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </ShellCard>
      </div>
    </section>
  );
}

function AutomationView({
  sections,
  runtimeStatus,
  onRunAction,
  onRefresh,
}: {
  sections: AutomationSection[];
  runtimeStatus: RuntimeStatus | null;
  onRunAction: (command: string) => void;
  onRefresh: () => void;
}) {
  const [filter, setFilter] = useState("");
  const filteredSections = useMemo(() => {
    const needle = filter.trim().toLowerCase();
    if (!needle) {
      return sections;
    }
    return sections
      .map((section) => ({
        ...section,
        actions: section.actions.filter((action) => {
          return (
            section.title.toLowerCase().includes(needle)
            || action.label.toLowerCase().includes(needle)
            || action.command.toLowerCase().includes(needle)
          );
        }),
      }))
      .filter((section) => section.actions.length);
  }, [filter, sections]);

  return (
    <section className="space-y-6 px-4 py-8 lg:px-12">
      <div className="grid gap-4 md:grid-cols-4">
        <ShellCard eyebrow="monitor local" title="CPU">
          <p className="text-5xl font-semibold text-[#54d8ff]">{runtimeStatus?.cpu ?? 0}%</p>
          <p className="mt-2 text-sm text-slate-400">uso atual do servidor local</p>
        </ShellCard>
        <ShellCard eyebrow="monitor local" title="RAM">
          <p className="text-5xl font-semibold text-[#2fe1b1]">{runtimeStatus?.ram ?? 0}%</p>
          <p className="mt-2 text-sm text-slate-400">memoria em uso</p>
        </ShellCard>
        <ShellCard eyebrow="monitor local" title="Disco">
          <p className="text-5xl font-semibold text-[#f0bb50]">{runtimeStatus?.disk ?? 0}%</p>
          <p className="mt-2 text-sm text-slate-400">ocupacao do disco</p>
        </ShellCard>
        <ShellCard
          eyebrow="catalogo"
          title="Central de automacoes"
          right={
            <button type="button" className="shell-chip" onClick={onRefresh}>
              atualizar
            </button>
          }
        >
          <p className="text-sm leading-7 text-slate-300">Atalhos do servidor local para abrir apps, controlar volume, navegador e sistema.</p>
          <input
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
            placeholder="buscar automacao..."
            className="mt-4 w-full rounded-[18px] border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500"
          />
        </ShellCard>
      </div>

      <div className="grid gap-5 xl:grid-cols-3">
        {filteredSections.map((section) => (
          <ShellCard key={section.title} eyebrow="automacao" title={section.title}>
            <div className="space-y-3">
              {section.actions.map((action) => (
                <button key={`${section.title}-${action.command}`} type="button" className="shell-inline-action" onClick={() => onRunAction(action.command)}>
                  <div>
                    <span className="block text-sm font-semibold text-white">{action.label}</span>
                    <span className="mt-1 block text-xs leading-5 text-slate-400">{action.command}</span>
                  </div>
                </button>
              ))}
            </div>
          </ShellCard>
        ))}
      </div>
    </section>
  );
}

function VisionView({
  status,
  screenFrame,
  cameraFrame,
  lastResponse,
  selectedCameraIndex,
  busyAction,
  onSelectCamera,
  onRefreshStatus,
  onCaptureScreen,
  onCaptureCamera,
  onRunScreenAction,
  onRunCameraAction,
}: {
  status: VisionStatus | null;
  screenFrame: VisionFrame | null;
  cameraFrame: VisionFrame | null;
  lastResponse: VisionResponse | null;
  selectedCameraIndex: number;
  busyAction: string | null;
  onSelectCamera: (cameraIndex: number) => void;
  onRefreshStatus: () => void;
  onCaptureScreen: () => void;
  onCaptureCamera: () => void;
  onRunScreenAction: (action: "describe" | "read-text" | "analyze-code" | "find-objects" | "ask", question?: string) => void;
  onRunCameraAction: (action: "describe" | "find-objects" | "ask", question?: string) => void;
}) {
  const [screenQuestion, setScreenQuestion] = useState("");
  const [cameraQuestion, setCameraQuestion] = useState("");
  const screenPreview = visionFrameUrl(screenFrame);
  const cameraPreview = visionFrameUrl(cameraFrame);
  const latestPreview = visionFrameUrl(lastResponse?.image ?? null);
  const hasCamera = Boolean(status?.camera_indices.length);

  return (
    <section className="space-y-6 px-4 py-8 lg:px-12">
      <div className="grid gap-4 md:grid-cols-4">
        <ShellCard eyebrow="visao" title="Cameras detectadas">
          <p className="text-5xl font-semibold text-[#54d8ff]">{status?.camera_indices.length ?? 0}</p>
          <p className="mt-2 text-sm text-slate-400">servidor local pronto para captura</p>
        </ShellCard>
        <ShellCard eyebrow="visao" title="Camera padrao">
          <p className="text-5xl font-semibold text-[#2fe1b1]">{selectedCameraIndex}</p>
          <p className="mt-2 text-sm text-slate-400">indice usado nas acoes de camera</p>
        </ShellCard>
        <ShellCard eyebrow="visao" title="Ultima acao">
          <p className="text-lg font-semibold text-white">{lastResponse?.action ?? "sem execucao"}</p>
          <p className={`mt-2 text-sm ${lastResponse?.ok === false ? "text-[#f37588]" : "text-slate-400"}`}>
            {busyAction ? `executando ${busyAction}...` : lastResponse?.ok === false ? "ultima resposta retornou erro" : "aguardando comando"}
          </p>
        </ShellCard>
        <ShellCard
          eyebrow="hardware"
          title="Status do modulo"
          right={
            <button type="button" className="shell-chip" onClick={onRefreshStatus}>
              atualizar
            </button>
          }
        >
          <p className="text-sm leading-7 text-slate-300">
            Cameras disponiveis: {status?.camera_indices.join(", ") || "nenhuma detectada"}
          </p>
        </ShellCard>
      </div>

      <div className="grid gap-5 xl:grid-cols-[1fr_1fr]">
        <ShellCard
          eyebrow="screen"
          title="Tela"
          right={
            <div className="flex flex-wrap gap-2">
              <button type="button" className="shell-chip" onClick={onCaptureScreen} disabled={Boolean(busyAction)}>
                capturar
              </button>
              <button type="button" className="shell-chip" onClick={() => onRunScreenAction("describe")} disabled={Boolean(busyAction)}>
                descrever
              </button>
              <button type="button" className="shell-chip" onClick={() => onRunScreenAction("read-text")} disabled={Boolean(busyAction)}>
                OCR
              </button>
              <button type="button" className="shell-chip" onClick={() => onRunScreenAction("analyze-code")} disabled={Boolean(busyAction)}>
                codigo
              </button>
              <button type="button" className="shell-chip" onClick={() => onRunScreenAction("find-objects")} disabled={Boolean(busyAction)}>
                objetos
              </button>
            </div>
          }
        >
          {screenPreview ? (
            <img
              src={screenPreview}
              alt="Preview da captura de tela"
              className="mb-4 h-[320px] w-full rounded-[24px] border border-white/8 object-cover"
            />
          ) : (
            <div className="mb-4 flex h-[320px] items-center justify-center rounded-[24px] border border-dashed border-white/10 bg-white/[0.02] text-sm text-slate-500">
              Capture a tela para gerar um preview aqui.
            </div>
          )}
          <div className="flex gap-3">
            <input
              value={screenQuestion}
              onChange={(event) => setScreenQuestion(event.target.value)}
              placeholder="pergunte algo sobre a tela..."
              className="flex-1 rounded-[18px] border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500"
            />
            <button
              type="button"
              className="shell-primary-button"
              disabled={Boolean(busyAction)}
              onClick={() => onRunScreenAction("ask", screenQuestion)}
            >
              perguntar
            </button>
          </div>
        </ShellCard>

        <ShellCard
          eyebrow="camera"
          title="Camera"
          right={
            <div className="flex flex-wrap gap-2">
              <button type="button" className="shell-chip" onClick={onCaptureCamera} disabled={Boolean(busyAction) || !hasCamera}>
                capturar
              </button>
              <button type="button" className="shell-chip" onClick={() => onRunCameraAction("describe")} disabled={Boolean(busyAction) || !hasCamera}>
                descrever
              </button>
              <button type="button" className="shell-chip" onClick={() => onRunCameraAction("find-objects")} disabled={Boolean(busyAction) || !hasCamera}>
                objetos
              </button>
            </div>
          }
        >
          <div className="mb-4 flex flex-wrap gap-2">
            {(status?.camera_indices ?? []).map((cameraIndex) => (
              <button
                key={cameraIndex}
                type="button"
                className={`shell-chip ${selectedCameraIndex === cameraIndex ? "shell-chip-active" : ""}`}
                onClick={() => onSelectCamera(cameraIndex)}
              >
                camera {cameraIndex}
              </button>
            ))}
            {!hasCamera ? <span className="text-sm text-slate-500">Nenhuma camera detectada no servidor local.</span> : null}
          </div>
          {cameraPreview ? (
            <img
              src={cameraPreview}
              alt="Preview da camera"
              className="mb-4 h-[320px] w-full rounded-[24px] border border-white/8 object-cover"
            />
          ) : (
            <div className="mb-4 flex h-[320px] items-center justify-center rounded-[24px] border border-dashed border-white/10 bg-white/[0.02] text-sm text-slate-500">
              Capture a camera para gerar um preview aqui.
            </div>
          )}
          <div className="flex gap-3">
            <input
              value={cameraQuestion}
              onChange={(event) => setCameraQuestion(event.target.value)}
              placeholder="pergunte algo sobre a camera..."
              className="flex-1 rounded-[18px] border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500"
            />
            <button
              type="button"
              className="shell-primary-button"
              disabled={Boolean(busyAction) || !hasCamera}
              onClick={() => onRunCameraAction("ask", cameraQuestion)}
            >
              perguntar
            </button>
          </div>
        </ShellCard>
      </div>

      <div className="grid gap-5 xl:grid-cols-[0.85fr_1.15fr]">
        <ShellCard eyebrow="resultado" title="Preview da ultima analise">
          {latestPreview ? (
            <img
              src={latestPreview}
              alt="Ultima imagem analisada"
              className="h-[360px] w-full rounded-[24px] border border-white/8 object-cover"
            />
          ) : (
            <div className="flex h-[360px] items-center justify-center rounded-[24px] border border-dashed border-white/10 bg-white/[0.02] text-sm text-slate-500">
              O preview final da analise aparece aqui.
            </div>
          )}
        </ShellCard>
        <ShellCard eyebrow="resposta" title="Leitura do NEXUS">
          <div className="rounded-[24px] border border-white/6 bg-[#080e18] p-5">
            <p className="whitespace-pre-wrap text-sm leading-7 text-slate-200">
              {lastResponse?.response ?? "Execute uma acao de visao para receber a resposta completa aqui."}
            </p>
          </div>
        </ShellCard>
      </div>
    </section>
  );
}

function MindView({
  state,
  isSaving,
  onSaveSettings,
  onStart,
  onStop,
  onCycle,
  onRollback,
  onRefreshProof,
  onClearRestart,
}: {
  state: MindState | null;
  isSaving: boolean;
  onSaveSettings: (settings: Record<string, unknown>) => void;
  onStart: () => void;
  onStop: () => void;
  onCycle: () => void;
  onRollback: () => void;
  onRefreshProof: () => void;
  onClearRestart: () => void;
}) {
  const [directive, setDirective] = useState("");
  const [mode, setMode] = useState("supervisionado");
  const [interval, setInterval] = useState("5");
  const [autoRestart, setAutoRestart] = useState(false);

  useEffect(() => {
    setDirective(String(state?.settings.directive ?? ""));
    setMode(String(state?.settings.mode ?? "supervisionado"));
    setInterval(String(state?.settings.interval ?? 5));
    setAutoRestart(Boolean(state?.settings.auto_restart ?? false));
  }, [state]);

  const proof = state?.proof;
  const score = state?.score ?? {};

  return (
    <section className="space-y-6 px-4 py-8 lg:px-12">
      <div className="grid gap-4 md:grid-cols-4">
        <ShellCard eyebrow="nexusmind" title="Estado">
          <p className={`text-4xl font-semibold ${state?.running ? "text-[#2fe1b1]" : "text-[#f0bb50]"}`}>{state?.running ? "Ativo" : "Pausado"}</p>
          <p className="mt-2 text-sm text-slate-400">{state?.cycle_active ? "ciclo em andamento" : "aguardando ação"}</p>
        </ShellCard>
        <ShellCard eyebrow="qualidade" title="Score geral">
          <p className="text-4xl font-semibold text-[#54d8ff]">{score.overall ?? "--"}</p>
          <p className="mt-2 text-sm text-slate-400">radon {score.radon ?? "--"} · pylint {score.pylint ?? "--"}</p>
        </ShellCard>
        <ShellCard eyebrow="arquivos" title="Mudanças recentes">
          <p className="text-4xl font-semibold text-white">{state?.changed_files.length ?? 0}</p>
          <p className="mt-2 text-sm text-slate-400">arquivos detectados pelo tracker</p>
        </ShellCard>
        <ShellCard eyebrow="restart" title="Reinício pendente">
          <p className="text-sm leading-7 text-slate-300">{state?.restart.pending_reason ?? "sem reinício pendente"}</p>
          {state?.restart.pending_reason ? (
            <button type="button" className="mt-4 shell-chip" onClick={onClearRestart}>
              limpar aviso
            </button>
          ) : null}
        </ShellCard>
      </div>

      <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
        <ShellCard eyebrow="controle" title="Configuração do ciclo">
          <div className="space-y-4">
            <div>
              <p className="shell-eyebrow">modo</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {["supervisionado", "autônomo", "agressivo"].map((item) => (
                  <button key={item} type="button" className={`shell-chip ${mode === item ? "shell-chip-active" : ""}`} onClick={() => setMode(item)}>
                    {item}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <p className="shell-eyebrow">diretriz</p>
              <textarea
                value={directive}
                onChange={(event) => setDirective(event.target.value)}
                rows={4}
                className="mt-3 w-full rounded-[18px] border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500"
                placeholder="Ex: melhorar observabilidade, reduzir complexidade do chat..."
              />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <p className="shell-eyebrow">intervalo (min)</p>
                <input
                  value={interval}
                  onChange={(event) => setInterval(event.target.value)}
                  className="mt-3 w-full rounded-[18px] border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-white outline-none"
                />
              </div>
              <div>
                <p className="shell-eyebrow">auto-restart</p>
                <button type="button" className={`mt-3 shell-pill-button ${autoRestart ? "shell-pill-button-active" : ""}`} onClick={() => setAutoRestart((current) => !current)}>
                  {autoRestart ? "Ligado" : "Desligado"}
                </button>
              </div>
            </div>
            <div className="flex flex-wrap gap-3">
              <button
                type="button"
                className="shell-primary-button"
                disabled={isSaving}
                onClick={() => onSaveSettings({ directive, mode, interval: Number(interval || 5), auto_restart: autoRestart })}
              >
                {isSaving ? "salvando..." : "salvar configuração"}
              </button>
              <button type="button" className="shell-chip" onClick={state?.running ? onStop : onStart}>
                {state?.running ? "pausar mind" : "iniciar mind"}
              </button>
              <button type="button" className="shell-chip" onClick={onCycle}>
                ciclo manual
              </button>
              <button type="button" className="shell-chip" onClick={onRefreshProof}>
                atualizar evidências
              </button>
              <button type="button" className="shell-chip" onClick={onRollback}>
                rollback git
              </button>
            </div>
            {state?.last_modified_path ? (
              <div className="rounded-[18px] border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-slate-300">
                Último arquivo tocado: <span className="text-white">{state.last_modified_path}</span>
              </div>
            ) : null}
            {state?.last_error ? (
              <div className="rounded-[18px] border border-[#6d3244] bg-[#2a151c]/80 px-4 py-3 text-sm text-[#f3a5b3]">{state.last_error}</div>
            ) : null}
          </div>
        </ShellCard>

        <ShellCard eyebrow="log" title="Mente & histórico">
          <div className="grid gap-4">
            <div className="rounded-[20px] border border-white/6 bg-[#080e18] p-4 font-mono text-xs leading-6 text-slate-300">
              {(state?.logs ?? []).slice(-18).map((line, index) => (
                <p key={`${index}-${line}`} className="border-b border-white/4 py-1 last:border-b-0">
                  {line}
                </p>
              ))}
            </div>
            <div className="grid gap-4 md:grid-cols-2">
              <div className="rounded-[20px] border border-white/6 bg-white/[0.02] p-4">
                <p className="shell-eyebrow">arquivos modificados</p>
                <div className="mt-3 space-y-2 text-sm text-slate-300">
                  {(state?.changed_files ?? []).slice(0, 8).map((item) => (
                    <p key={`${item.path}-${item.action}`}>{item.action.toUpperCase()} · {item.path}</p>
                  ))}
                </div>
              </div>
              <div className="rounded-[20px] border border-white/6 bg-white/[0.02] p-4">
                <p className="shell-eyebrow">ciclos anteriores</p>
                <div className="mt-3 space-y-2 text-sm text-slate-300">
                  {(state?.history ?? []).slice(0, 6).map((item) => (
                    <p key={`${item.timestamp}-${item.summary}`}>{item.timestamp.slice(11, 16)} · {item.summary}</p>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </ShellCard>
      </div>

      <div className="grid gap-5 xl:grid-cols-[0.95fr_1.05fr]">
        <ShellCard eyebrow="proof-of-work" title="Verificações">
          <div className="space-y-3">
            {(proof?.verifications ?? []).map((item) => (
              <div key={`${item.label}-${item.detail}`} className="rounded-[18px] border border-white/6 bg-white/[0.02] px-4 py-3 text-sm text-slate-300">
                <p className="text-white">{item.label}</p>
                <p className="mt-1">{item.detail}</p>
              </div>
            ))}
          </div>
        </ShellCard>

        <ShellCard eyebrow="commits" title="Últimos commits do NexusMind">
          <div className="space-y-3">
            {(proof?.commits ?? []).slice(0, 8).map((item) => (
              <div key={`${item.hash}-${item.msg}`} className="rounded-[18px] border border-white/6 bg-white/[0.02] px-4 py-3 text-sm text-slate-300">
                <p className="text-white">{item.hash} · {item.date}</p>
                <p className="mt-1">{item.msg}</p>
              </div>
            ))}
          </div>
        </ShellCard>
      </div>
    </section>
  );
}

function TelemetryView({
  logs,
  events,
  dashboard,
  runtimeStatus,
  onOpenUpdates,
  onRefresh,
}: {
  logs: string[];
  events: SessionEvent[];
  dashboard: DashboardPayload | null;
  runtimeStatus: RuntimeStatus | null;
  onOpenUpdates: () => void;
  onRefresh: () => void;
}) {
  const [logFilter, setLogFilter] = useState("");
  const [copyState, setCopyState] = useState<"idle" | "ok" | "error">("idle");
  const filteredLogs = useMemo(() => {
    const needle = logFilter.trim().toLowerCase();
    if (!needle) {
      return logs;
    }
    return logs.filter((line) => line.toLowerCase().includes(needle));
  }, [logFilter, logs]);

  return (
    <section className="space-y-6 px-4 py-8 lg:px-12">
      <div className="grid gap-4 md:grid-cols-4">
        <ShellCard eyebrow="runtime" title="Saude atual">
          <p className="text-5xl font-semibold text-[#54d8ff]">{dashboard?.health.score ?? "--"}</p>
          <p className="mt-2 text-sm text-slate-400">{dashboard?.health.status ?? "carregando"}</p>
        </ShellCard>
        <ShellCard eyebrow="fluxo" title="Eventos vivos">
          <p className="text-5xl font-semibold text-[#f0bb50]">{events.length}</p>
          <p className="mt-2 text-sm text-slate-400">ultimos eventos capturados pela shell</p>
        </ShellCard>
        <ShellCard eyebrow="observacoes" title="Avisos do projeto" right={<button type="button" className="shell-chip" onClick={onOpenUpdates}>novidades</button>}>
          <p className="text-sm leading-7 text-slate-300">{dashboard?.health.warnings[0] ?? "sem avisos fortes no momento"}</p>
        </ShellCard>
        <ShellCard eyebrow="servidor local" title="Monitor">
          <p className="text-sm leading-7 text-slate-300">CPU {runtimeStatus?.cpu ?? 0}% · RAM {runtimeStatus?.ram ?? 0}% · DISCO {runtimeStatus?.disk ?? 0}%</p>
          <button type="button" className="mt-4 shell-chip" onClick={onRefresh}>
            atualizar agora
          </button>
        </ShellCard>
      </div>

      <div className="grid gap-5 xl:grid-cols-[1fr_1fr]">
        <ShellCard eyebrow="timeline" title="Eventos recentes">
          <div className="space-y-3">
            {events.slice(0, 10).map((event) => (
              <div key={`${event.timestamp}-${event.message}`} className="rounded-[22px] border border-white/6 bg-white/[0.02] px-4 py-4">
                <div className="flex items-center justify-between gap-3">
                  <span className={`text-xs uppercase tracking-[0.24em] ${toneClass(event.kind)}`}>{event.kind}</span>
                  <span className="text-xs text-slate-500">{event.timestamp.slice(11, 19)}</span>
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-200">{event.message}</p>
              </div>
            ))}
          </div>
        </ShellCard>

        <ShellCard
          eyebrow="logs"
          title="Saida do sistema"
          right={
            <div className="flex gap-2">
              <button type="button" className="shell-chip" onClick={onRefresh}>
                atualizar
              </button>
              <button
                type="button"
                className="shell-chip"
                onClick={() => {
                  void copyText(filteredLogs.join("\n"))
                    .then(() => setCopyState("ok"))
                    .catch(() => setCopyState("error"));
                }}
              >
                {copyState === "ok" ? "copiado" : copyState === "error" ? "falhou" : "copiar"}
              </button>
            </div>
          }
        >
          <input
            value={logFilter}
            onChange={(event) => {
              setCopyState("idle");
              setLogFilter(event.target.value);
            }}
            placeholder="filtrar logs..."
            className="mb-4 w-full rounded-[18px] border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500"
          />
          <div className="rounded-[24px] border border-white/6 bg-[#080e18] p-4 font-mono text-xs leading-6 text-slate-300">
            {filteredLogs.slice(0, 40).map((line, index) => (
              <p key={`${index}-${line}`} className="border-b border-white/4 py-1 last:border-b-0">
                {line}
              </p>
            ))}
          </div>
        </ShellCard>
      </div>
    </section>
  );
}

function NexusSettingsHub({
  settings,
  setSettings,
  isSaving,
  onSave,
  profileContrast,
  setProfileContrast,
  fontScale,
  setFontScale,
  activeTab,
  setActiveTab,
  onOpenChatWithPrompt,
}: {
  settings: Record<string, unknown>;
  setSettings: (next: Record<string, unknown>) => void;
  isSaving: boolean;
  onSave: (next: Record<string, unknown>) => void;
  profileContrast: ProfileContrast;
  setProfileContrast: (next: ProfileContrast) => void;
  fontScale: FontScale;
  setFontScale: (next: FontScale) => void;
  activeTab: SettingsTab;
  setActiveTab: (next: SettingsTab) => void;
  onOpenChatWithPrompt: (prompt: string) => void;
}) {
  return (
    <section className="space-y-6 px-4 py-8 lg:px-12">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h2 className="text-4xl font-semibold text-white">Meu Perfil</h2>
          <p className="mt-2 text-sm text-slate-400">
            Se quiser aumentar o contraste ou o tamanho da fonte, e so acessar Meu Perfil nas configuracoes.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {[
            ["profile", "Perfil"],
            ["updates", "Novidades"],
            ["integrations", "Integracoes"],
            ["system", "Sistema"],
          ].map(([value, label]) => (
            <button key={value} type="button" className={`shell-pill-button ${activeTab === value ? "shell-pill-button-active" : ""}`} onClick={() => setActiveTab(value as SettingsTab)}>
              {label}
            </button>
          ))}
        </div>
      </div>

      {activeTab === "profile" ? (
        <div className="grid gap-5 xl:grid-cols-[0.9fr_1.1fr]">
          <ShellCard eyebrow="acessibilidade" title="Experiencia visual">
            <div className="space-y-5">
              <div>
                <p className="shell-eyebrow">contraste</p>
                <div className="mt-3 flex gap-2">
                  <button type="button" className={`shell-chip ${profileContrast === "normal" ? "shell-chip-active" : ""}`} onClick={() => setProfileContrast("normal")}>
                    Normal
                  </button>
                  <button type="button" className={`shell-chip ${profileContrast === "high" ? "shell-chip-active" : ""}`} onClick={() => setProfileContrast("high")}>
                    Alto contraste
                  </button>
                </div>
              </div>
              <div>
                <p className="shell-eyebrow">fonte</p>
                <div className="mt-3 flex gap-2">
                  <button type="button" className={`shell-chip ${fontScale === "normal" ? "shell-chip-active" : ""}`} onClick={() => setFontScale("normal")}>
                    Normal
                  </button>
                  <button type="button" className={`shell-chip ${fontScale === "large" ? "shell-chip-active" : ""}`} onClick={() => setFontScale("large")}>
                    Grande
                  </button>
                </div>
              </div>
              <div className="rounded-[22px] border border-white/8 bg-white/[0.03] p-4 text-sm text-slate-300">
                Nexus aplicado com {profileContrast === "high" ? "alto contraste" : "contraste padrao"} e fonte{" "}
                {fontScale === "large" ? "grande" : "normal"}.
              </div>
            </div>
          </ShellCard>

          <SettingsForm
            initialSettings={settings}
            isSaving={isSaving}
            onSave={(nextSettings) => {
              setSettings(nextSettings);
              onSave(nextSettings);
            }}
          />
        </div>
      ) : null}

      {activeTab === "updates" ? (
        <div className="grid gap-5 xl:grid-cols-[1.1fr_0.9fr]">
          <ShellCard eyebrow="central Nexus" title="Novidades e historico">
            <div className="space-y-4">
              {nexusUpdates.map((item) => (
                <article key={item.id} className="rounded-[22px] border border-white/8 bg-white/[0.03] p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="shell-eyebrow">{item.date}</p>
                      <h3 className="mt-2 text-lg font-semibold text-white">{item.title}</h3>
                    </div>
                    {item.actionUrl ? (
                      <button type="button" className="shell-chip" onClick={() => openExternal(item.actionUrl!)}>
                        {item.actionLabel}
                      </button>
                    ) : null}
                  </div>
                  <div className="mt-3 space-y-2 text-sm leading-6 text-slate-300">
                    {item.body.map((paragraph) => (
                      <p key={paragraph}>{paragraph}</p>
                    ))}
                  </div>
                </article>
              ))}
            </div>
          </ShellCard>

          <div className="grid gap-5">
            <ShellCard eyebrow="video" title="Mudancas recentes">
              <button type="button" className="shell-primary-button w-full" onClick={() => openExternal("https://youtu.be/_27xMh5UNaI")}>
                assistir video de novidades
              </button>
            </ShellCard>
            <ShellCard eyebrow="sugestoes" title="Como contribuir">
              <ul className="space-y-3 text-sm text-slate-300">
                <li>Relate bugs encontrados</li>
                <li>Sugira novas funcionalidades</li>
                <li>Compartilhe melhorias de UX</li>
                <li>Proponha integracoes</li>
              </ul>
              <div className="mt-4 flex flex-wrap gap-3">
                <button type="button" className="shell-chip" onClick={() => onOpenChatWithPrompt("quero relatar um bug no Nexus")}>
                  relatar bug no chat
                </button>
                <button type="button" className="shell-chip" onClick={() => onOpenChatWithPrompt("quero sugerir uma melhoria de UX para o Nexus")}>
                  sugerir melhoria
                </button>
              </div>
            </ShellCard>
          </div>
        </div>
      ) : null}

      {activeTab === "integrations" ? (
        <div className="grid gap-5 md:grid-cols-3">
          {[
            ["WhatsApp", "Mensagens e notificacoes com historico no chat."],
            ["Telegram", "Canal adicional para conversar com o Nexus."],
            ["Alexa", "Resposta unica e objetiva focada em voz."],
          ].map(([label, description]) => (
            <ShellCard key={label} eyebrow="integracao" title={label}>
              <p className="text-sm leading-7 text-slate-300">{description}</p>
              <button
                type="button"
                className="mt-4 shell-chip"
                onClick={() => onOpenChatWithPrompt(`quero configurar a integracao ${label.toLowerCase()} no Nexus`)}
              >
                continuar no chat
              </button>
            </ShellCard>
          ))}
        </div>
      ) : null}

      {activeTab === "system" ? (
        <div className="grid gap-5 md:grid-cols-3">
          <ShellCard eyebrow="dark mode" title="Tema do sistema">
            <p className="text-sm leading-7 text-slate-300">Modo escuro ativo e alinhado com o cockpit visual do Nexus.</p>
          </ShellCard>
          <ShellCard eyebrow="chat ia" title="Cards inteligentes">
            <p className="text-sm leading-7 text-slate-300">Cards visuais para recorrencia, parcelamentos, conhecimento e automacoes.</p>
          </ShellCard>
          <ShellCard eyebrow="performance" title="Evolucao interna">
            <p className="text-sm leading-7 text-slate-300">Melhorias de voz, imagem, PDF, atualizacao de interface e motor de contexto.</p>
          </ShellCard>
        </div>
      ) : null}
    </section>
  );
}

export default function App() {
  const [dashboard, setDashboard] = useState<DashboardPayload | null>(null);
  const [memoryGraph, setMemoryGraph] = useState<MemoryGraphPayload | null>(null);
  const [runtimeStatus, setRuntimeStatus] = useState<RuntimeStatus | null>(null);
  const [automationSections, setAutomationSections] = useState<AutomationSection[]>([]);
  const [visionStatus, setVisionStatus] = useState<VisionStatus | null>(null);
  const [visionScreenFrame, setVisionScreenFrame] = useState<VisionFrame | null>(null);
  const [visionCameraFrame, setVisionCameraFrame] = useState<VisionFrame | null>(null);
  const [visionLastResponse, setVisionLastResponse] = useState<VisionResponse | null>(null);
  const [visionCameraIndex, setVisionCameraIndex] = useState(0);
  const [visionBusyAction, setVisionBusyAction] = useState<string | null>(null);
  const [mindState, setMindState] = useState<MindState | null>(null);
  const [isSavingMind, setIsSavingMind] = useState(false);
  const [settings, setSettings] = useState<Record<string, unknown>>({});
  const [messages, setMessages] = useState<ChatMessage[]>([bootMessage]);
  const [command, setCommand] = useState("");
  const [attachments, setAttachments] = useState<AttachmentDraft[]>([]);
  const [isSending, setIsSending] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isConversationActive, setIsConversationActive] = useState(false);
  const [isDictating, setIsDictating] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [pendingConfirmation, setPendingConfirmation] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [activeView, setActiveView] = useState<ViewId>("chat");
  const [settingsTab, setSettingsTab] = useState<SettingsTab>("profile");
  const [profileContrast, setProfileContrast] = useState<ProfileContrast>("normal");
  const [fontScale, setFontScale] = useState<FontScale>("normal");
  const [isRefreshing, startTransition] = useTransition();
  const deferredLogs = useDeferredValue(dashboard?.logs ?? []);
  const recognitionRef = useRef<BrowserSpeechRecognitionInstance | null>(null);
  const activeVoiceModeRef = useRef<VoiceMode | null>(null);
  const latestTranscriptRef = useRef("");
  const conversationEnabledRef = useRef(false);
  const restartVoiceTimeoutRef = useRef<number | null>(null);
  const pendingConfirmationRef = useRef<string | null>(null);
  const isSendingRef = useRef(false);
  const isSpeakingRef = useRef(false);
  const speechRecognitionCtor = useMemo(() => resolveSpeechRecognitionConstructor(), []);
  const latestAssistantReply = useMemo(
    () => [...messages].reverse().find((message) => message.role === "assistant" && sanitizeChatText(message.content)) ?? null,
    [messages],
  );

  useEffect(() => {
    const storedContrast = window.localStorage.getItem("nexus-profile-contrast");
    const storedFont = window.localStorage.getItem("nexus-profile-font");
    if (storedContrast === "high") {
      setProfileContrast("high");
    }
    if (storedFont === "large") {
      setFontScale("large");
    }
  }, []);

  useEffect(() => {
    window.localStorage.setItem("nexus-profile-contrast", profileContrast);
    window.localStorage.setItem("nexus-profile-font", fontScale);
  }, [profileContrast, fontScale]);

  useEffect(() => {
    pendingConfirmationRef.current = pendingConfirmation;
  }, [pendingConfirmation]);

  useEffect(() => {
    isSendingRef.current = isSending;
  }, [isSending]);

  useEffect(() => {
    isSpeakingRef.current = isSpeaking;
  }, [isSpeaking]);

  useEffect(() => {
    return () => {
      if (restartVoiceTimeoutRef.current !== null) {
        window.clearTimeout(restartVoiceTimeoutRef.current);
      }
      recognitionRef.current?.abort();
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const shellStyle = useMemo(
    () => ({
      filter: profileContrast === "high" ? "contrast(1.1) saturate(1.05)" : "none",
      fontSize: fontScale === "large" ? "17px" : "16px",
    }),
    [profileContrast, fontScale],
  );

  function pushSystemMessage(content: string, meta = "web/system") {
    setMessages((current) => [
      ...current,
      {
        id: asMessageId(),
        role: "system",
        content,
        meta,
      },
    ]);
  }

  function clearScheduledVoiceRestart() {
    if (restartVoiceTimeoutRef.current !== null) {
      window.clearTimeout(restartVoiceTimeoutRef.current);
      restartVoiceTimeoutRef.current = null;
    }
  }

  function stopVoiceCapture(disableConversation = true) {
    clearScheduledVoiceRestart();
    recognitionRef.current?.abort();
    recognitionRef.current = null;
    activeVoiceModeRef.current = null;
    latestTranscriptRef.current = "";
    setIsDictating(false);

    if (disableConversation) {
      conversationEnabledRef.current = false;
      setIsConversationActive(false);
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
      }
      setIsSpeaking(false);
    }
  }

  function scheduleConversationRestart(delay = 220) {
    if (!conversationEnabledRef.current) {
      return;
    }
    clearScheduledVoiceRestart();
    restartVoiceTimeoutRef.current = window.setTimeout(() => {
      restartVoiceTimeoutRef.current = null;
      if (!conversationEnabledRef.current || recognitionRef.current || isSendingRef.current || isSpeakingRef.current) {
        return;
      }
      beginVoiceCapture("conversation");
    }, delay);
  }

  async function submitVoiceTranscript(transcript: string, mode: VoiceMode) {
    const trimmed = transcript.trim();
    if (!trimmed) {
      if (mode === "conversation") {
        scheduleConversationRestart();
      }
      return;
    }

    const confirmationCommand = pendingConfirmationRef.current;
    if (confirmationCommand) {
      const normalized = normalizeVoiceText(trimmed);
      if (["sim", "confirmar", "confirma", "pode", "ok", "pode executar"].includes(normalized)) {
        setPendingConfirmation(null);
        await executeCommand(confirmationCommand, true, false, mode === "conversation", mode);
        return;
      }
      if (["nao", "não", "cancelar", "cancela", "parar"].includes(normalized)) {
        setPendingConfirmation(null);
        pushSystemMessage("Confirmacao cancelada por voz.", "voice/cancel");
        if (mode === "conversation") {
          speakText("Comando cancelado.", { resumeConversation: true });
        }
        return;
      }
    }

    setCommand(trimmed);
    await executeCommand(trimmed, false, true, mode === "conversation", mode);
    setCommand("");
  }

  function speakText(text: string, options: { resumeConversation?: boolean } = {}) {
    if (typeof window === "undefined" || !("speechSynthesis" in window)) {
      pushSystemMessage("Seu navegador não oferece leitura por voz aqui.");
      if (options.resumeConversation) {
        scheduleConversationRestart();
      }
      return false;
    }

    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return true;
    }

    const sanitized = sanitizeChatText(text);
    if (!sanitized) {
      pushSystemMessage("Ainda não há resposta para eu ler em voz alta.");
      return false;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(sanitized);
    const voices = window.speechSynthesis.getVoices();
    const preferredVoice = voices.find((voice) => voice.lang.toLowerCase().startsWith("pt-br")) ?? voices.find((voice) => voice.lang.toLowerCase().startsWith("pt"));
    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }
    utterance.lang = "pt-BR";
    utterance.rate = 1;
    utterance.pitch = 1;
    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => {
      setIsSpeaking(false);
      if (options.resumeConversation) {
        scheduleConversationRestart();
      }
    };
    utterance.onerror = () => {
      setIsSpeaking(false);
      pushSystemMessage("Não consegui reproduzir essa resposta em voz alta.");
      if (options.resumeConversation) {
        scheduleConversationRestart(350);
      }
    };
    window.speechSynthesis.speak(utterance);
    return true;
  }

  function beginVoiceCapture(mode: VoiceMode) {
    if (!speechRecognitionCtor) {
      pushSystemMessage("Seu navegador não liberou reconhecimento de voz nesta interface.");
      if (mode === "conversation") {
        conversationEnabledRef.current = false;
        setIsConversationActive(false);
      }
      return;
    }

    if (recognitionRef.current || isSendingRef.current || isSpeakingRef.current) {
      return;
    }

    clearScheduledVoiceRestart();
    const recognition = new speechRecognitionCtor();
    recognition.lang = "pt-BR";
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    latestTranscriptRef.current = "";
    activeVoiceModeRef.current = mode;
    recognitionRef.current = recognition;

    recognition.onstart = () => {
      if (mode === "conversation") {
        setIsConversationActive(true);
      } else {
        setIsDictating(true);
      }
    };

    recognition.onresult = (event) => {
      const parts: string[] = [];
      for (let index = event.resultIndex; index < event.results.length; index += 1) {
        const result = event.results[index];
        const transcript = result?.[0]?.transcript ?? "";
        if (transcript.trim()) {
          parts.push(transcript.trim());
        }
      }
      const merged = parts.join(" ").trim();
      if (!merged) {
        return;
      }
      latestTranscriptRef.current = merged;
      if (mode === "dictation") {
        setCommand(merged);
      }
    };

    recognition.onerror = (event) => {
      recognitionRef.current = null;
      activeVoiceModeRef.current = null;
      latestTranscriptRef.current = "";
      setIsDictating(false);

      if (event.error === "aborted") {
        return;
      }

      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        pushSystemMessage("Permissão de microfone negada.");
        stopVoiceCapture();
        return;
      }

      if (event.error === "audio-capture") {
        pushSystemMessage("Nao encontrei um microfone disponivel neste navegador.");
        stopVoiceCapture();
        return;
      }

      if (mode === "conversation" && conversationEnabledRef.current) {
        scheduleConversationRestart(450);
        return;
      }

      pushSystemMessage("Não consegui captar sua voz agora.");
    };

    recognition.onend = () => {
      const transcript = latestTranscriptRef.current.trim();
      const activeMode = activeVoiceModeRef.current;
      recognitionRef.current = null;
      activeVoiceModeRef.current = null;
      setIsDictating(false);
      latestTranscriptRef.current = "";

      if (!activeMode) {
        return;
      }

      void submitVoiceTranscript(transcript, activeMode);
    };

    recognition.start();
  }

  function toggleConversationMode() {
    if (conversationEnabledRef.current) {
      stopVoiceCapture();
      return;
    }
    conversationEnabledRef.current = true;
    setIsConversationActive(true);
    beginVoiceCapture("conversation");
  }

  function triggerVoiceCommand() {
    if (recognitionRef.current && activeVoiceModeRef.current === "dictation") {
      stopVoiceCapture(false);
      return;
    }
    if (conversationEnabledRef.current) {
      stopVoiceCapture();
    }
    beginVoiceCapture("dictation");
  }

  function handleAttachFiles(fileList: FileList | null) {
    if (!fileList?.length) {
      return;
    }

    const nextItems = Array.from(fileList).map((file) => ({
      id: asMessageId(),
      file,
      kind: classifyAttachment(file),
      label: file.name,
      sizeLabel: formatFileSize(file.size),
    }));

    setAttachments((current) => [...current, ...nextItems]);
    if (!command.trim()) {
      setCommand("analise esta mídia");
    }
  }

  function removeAttachment(id: string) {
    setAttachments((current) => current.filter((attachment) => attachment.id !== id));
  }

  async function refreshDashboard() {
    const [payload, memoryPayload, runtimePayload, nextMindState] = await Promise.all([fetchDashboard(), fetchMemoryGraph(), fetchRuntimeStatus(), fetchMindState()]);
    startTransition(() => {
      setDashboard(payload);
      setMemoryGraph(memoryPayload);
      setRuntimeStatus(runtimePayload);
      setMindState(nextMindState);
    });
  }

  async function refreshVisionStatus() {
    try {
      const nextStatus = await fetchVisionStatus();
      setVisionStatus(nextStatus);
      setVisionCameraIndex((current) => {
        if (nextStatus.camera_indices.includes(current)) {
          return current;
        }
        if (nextStatus.camera_indices.includes(nextStatus.default_camera_index)) {
          return nextStatus.default_camera_index;
        }
        return nextStatus.camera_indices[0] ?? nextStatus.default_camera_index ?? 0;
      });
      setErrorMessage(null);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Falha ao ler status da visao.");
    }
  }

  useEffect(() => {
    let active = true;

    async function bootstrap() {
      try {
        const [dashboardPayload, memoryPayload, settingsPayload, runtimePayload, automationPayload, nextMindState, nextVisionStatus] = await Promise.all([
          fetchDashboard(),
          fetchMemoryGraph(),
          fetchSettings(),
          fetchRuntimeStatus(),
          fetchAutomationCatalog(),
          fetchMindState(),
          fetchVisionStatus(),
        ]);
        if (!active) {
          return;
        }
        startTransition(() => {
          setDashboard(dashboardPayload);
          setMemoryGraph(memoryPayload);
          setRuntimeStatus(runtimePayload);
          setMindState(nextMindState);
        });
        setAutomationSections(automationPayload);
        setSettings(settingsPayload);
        setVisionStatus(nextVisionStatus);
        setVisionCameraIndex(
          nextVisionStatus.camera_indices.includes(nextVisionStatus.default_camera_index)
            ? nextVisionStatus.default_camera_index
            : nextVisionStatus.camera_indices[0] ?? nextVisionStatus.default_camera_index ?? 0,
        );
        setErrorMessage(null);
      } catch (error) {
        if (!active) {
          return;
        }
        setErrorMessage(error instanceof Error ? error.message : "Sincronização instável. Verifique a conexão.");
      }
    }

    void bootstrap();
    const intervalId = window.setInterval(() => {
      void refreshDashboard().catch((error: unknown) => {
        setErrorMessage(error instanceof Error ? error.message : "Sincronização instável. Verifique a conexão.");
      });
    }, 15000);

    return () => {
      active = false;
      window.clearInterval(intervalId);
    };
  }, []);

  useEffect(() => {
    const source = new EventSource(`${apiBase}/api/events/stream`);
    source.onmessage = (event) => {
      const nextEvent = eventToSessionEvent(event);
      if (!nextEvent) {
        return;
      }
      setDashboard((current) => {
        if (!current) {
          return current;
        }
        return {
          ...current,
          events: [nextEvent, ...current.events].slice(0, 40),
        };
      });
    };
    source.onerror = () => {
      source.close();
    };

    return () => {
      source.close();
    };
  }, []);

  async function executeCommand(text: string, confirm = false, echoUser = true, speakResponse = false, voiceMode: VoiceMode | null = null) {
    const trimmed = text.trim();
    if (!trimmed) {
      if (voiceMode === "conversation") {
        scheduleConversationRestart();
      }
      return;
    }

    if (echoUser) {
      setMessages((current) => [
        ...current,
        {
          id: asMessageId(),
          role: "user",
          content: trimmed,
          meta: confirm ? "confirmed" : "draft",
        },
      ]);
    }

    setIsSending(true);
    try {
      const result = await sendChat(trimmed, confirm);
      setMessages((current) => [
        ...current,
        {
          id: asMessageId(),
          role: "assistant",
          content: result.response,
          meta: result.understood,
        },
      ]);
      setPendingConfirmation(result.confirmation_required ? trimmed : null);
      setErrorMessage(null);
      if (speakResponse && result.response) {
        window.setTimeout(() => {
          speakText(result.response, { resumeConversation: voiceMode === "conversation" });
        }, 120);
      } else if (voiceMode === "conversation") {
        scheduleConversationRestart();
      }
      await refreshDashboard();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Falha ao enviar comando.";
      setMessages((current) => [
        ...current,
        {
          id: asMessageId(),
          role: "system",
          content: message,
          meta: "web/error",
        },
      ]);
      setErrorMessage(message);
      if (voiceMode === "conversation") {
        scheduleConversationRestart(500);
      }
    } finally {
      setIsSending(false);
    }
  }

  async function handleSend() {
    const nextCommand = command.trim();
    if (!nextCommand && attachments.length === 0) {
      return;
    }

    if (attachments.length) {
      const prompt = nextCommand || "descreva esta mídia";
      const queuedAttachments = [...attachments];
      setCommand("");
      setAttachments([]);
      setMessages((current) => [
        ...current,
        {
          id: asMessageId(),
          role: "user",
          content: `${prompt} (${queuedAttachments.map((item) => item.label).join(", ")})`,
          meta: "media",
        },
      ]);
      setIsSending(true);
      try {
        const responses = await Promise.all(queuedAttachments.map((attachment) => analyzeMedia(attachment.file, prompt)));
        const responseText = responses
          .map((item) => `Arquivo: ${item.filename}\n${item.response}`)
          .join("\n\n");
        setMessages((current) => [
          ...current,
          {
            id: asMessageId(),
            role: "assistant",
            content: responseText,
            meta: "media/analyze",
          },
        ]);
        setErrorMessage(null);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Falha ao analisar a mídia anexada.";
        pushSystemMessage(message, "media/error");
        setErrorMessage(message);
      } finally {
        setIsSending(false);
      }
      return;
    }

    setCommand("");
    await executeCommand(nextCommand);
  }

  async function handleConfirmPending() {
    if (!pendingConfirmation) {
      return;
    }
    const nextCommand = pendingConfirmation;
    setPendingConfirmation(null);
    await executeCommand(nextCommand, true, false);
  }

  async function handleSaveSettings(nextSettings: Record<string, unknown>) {
    setIsSaving(true);
    try {
      const saved = await saveSettings(nextSettings);
      setSettings(saved);
      setMessages((current) => [
        ...current,
        {
          id: asMessageId(),
          role: "system",
          content: "Configuracoes atualizadas com sucesso.",
          meta: "settings/save",
        },
      ]);
      setErrorMessage(null);
      await refreshDashboard();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Falha ao salvar configuracoes.";
      setErrorMessage(message);
      setMessages((current) => [
        ...current,
        {
          id: asMessageId(),
          role: "system",
          content: message,
          meta: "settings/error",
        },
      ]);
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSaveMindSettings(nextSettings: Record<string, unknown>) {
    setIsSavingMind(true);
    try {
      const saved = await saveMindSettings(nextSettings);
      setMindState(saved);
      setErrorMessage(null);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Falha ao salvar NexusMind.";
      setErrorMessage(message);
    } finally {
      setIsSavingMind(false);
    }
  }

  async function runMindMutation(action: () => Promise<MindState>) {
    try {
      const nextState = await action();
      setMindState(nextState);
      setErrorMessage(null);
      await refreshDashboard();
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Falha ao executar ação do NexusMind.");
    }
  }

  async function runVisionMutation(
    busyLabel: string,
    action: () => Promise<VisionResponse>,
    target: "screen" | "camera" | "result" = "result",
  ) {
    setVisionBusyAction(busyLabel);
    try {
      const result = await action();
      if (result.image) {
        if (target === "screen") {
          setVisionScreenFrame(result.image);
        } else if (target === "camera") {
          setVisionCameraFrame(result.image);
        }
      }
      setVisionLastResponse(result);
      setErrorMessage(result.ok ? null : result.response);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Falha ao executar o modulo de visao.");
    } finally {
      setVisionBusyAction(null);
    }
  }

  return (
    <div className="shell-root" style={shellStyle}>
      <Sidebar
        activeView={activeView}
        onSelect={setActiveView}
        onHelp={() => {
          setActiveView("settings");
          setSettingsTab("updates");
        }}
      />

      <main className="shell-main">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_top_left,rgba(50,180,216,0.14),transparent_22%),radial-gradient(circle_at_bottom_right,rgba(55,68,180,0.14),transparent_28%)]" />
        {errorMessage ? (
          <div className="relative z-20 mx-4 mt-4 rounded-full border border-[#6d3244] bg-[#2a151c]/80 px-5 py-3 text-sm text-[#f3a5b3] lg:mx-12">
            {errorMessage}
          </div>
        ) : null}

        <AnimatePresence mode="wait">
          <motion.div
            key={`${activeView}-${settingsTab}`}
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.24 }}
            className="relative z-10"
          >
            {activeView === "chat" ? (
              <ChatLanding
                dashboard={dashboard}
                messages={messages}
                command={command}
                attachments={attachments}
                isSending={isSending}
                isConversationActive={isConversationActive}
                isDictating={isDictating}
                isSpeaking={isSpeaking}
                voiceSupported={Boolean(speechRecognitionCtor)}
                pendingConfirmation={pendingConfirmation}
                quickActionItems={quickActions}
                onChange={setCommand}
                onAttachFiles={handleAttachFiles}
                onToggleConversation={() => {
                  toggleConversationMode();
                }}
                onTranscribe={() => {
                  triggerVoiceCommand();
                }}
                onSpeakLastResponse={() => {
                  speakText(latestAssistantReply?.content ?? "");
                }}
                onRemoveAttachment={removeAttachment}
                onQuickAction={(value) => {
                  setCommand(value);
                  void executeCommand(value);
                }}
                onSend={() => {
                  void handleSend();
                }}
                onConfirmPending={() => {
                  void handleConfirmPending();
                }}
                onBriefing={() => {
                  setActiveView("telemetry");
                }}
                onOpenUpdates={() => {
                  setActiveView("settings");
                  setSettingsTab("updates");
                }}
                onOpenFinance={() => {
                  setActiveView("finance");
                }}
              />
            ) : null}

            {activeView === "automation" ? (
              <AutomationView
                sections={automationSections}
                runtimeStatus={runtimeStatus}
                onRefresh={() => {
                  void Promise.all([refreshDashboard(), fetchAutomationCatalog().then(setAutomationSections)]).catch((error: unknown) => {
                    setErrorMessage(error instanceof Error ? error.message : "Falha ao atualizar automacoes.");
                  });
                }}
                onRunAction={(value) => {
                  setActiveView("chat");
                  setCommand(value);
                  void executeCommand(value);
                }}
              />
            ) : null}

            {activeView === "brain" ? <BrainView memoryGraph={memoryGraph} /> : null}
            {activeView === "vision" ? (
              <VisionView
                status={visionStatus}
                screenFrame={visionScreenFrame}
                cameraFrame={visionCameraFrame}
                lastResponse={visionLastResponse}
                selectedCameraIndex={visionCameraIndex}
                busyAction={visionBusyAction}
                onSelectCamera={setVisionCameraIndex}
                onRefreshStatus={() => {
                  void refreshVisionStatus();
                }}
                onCaptureScreen={() => {
                  void runVisionMutation("captura de tela", captureVisionScreen, "screen");
                }}
                onCaptureCamera={() => {
                  void runVisionMutation("captura de camera", () => captureVisionCamera(visionCameraIndex), "camera");
                }}
                onRunScreenAction={(action, question) => {
                  void runVisionMutation(`visao de tela:${action}`, () => runVisionScreenAction(action, question ?? ""), "screen");
                }}
                onRunCameraAction={(action, question) => {
                  void runVisionMutation(`visao de camera:${action}`, () => runVisionCameraAction(action, question ?? "", visionCameraIndex), "camera");
                }}
              />
            ) : null}
            {activeView === "mind" ? (
              <MindView
                state={mindState}
                isSaving={isSavingMind}
                onSaveSettings={(nextSettings) => {
                  void handleSaveMindSettings(nextSettings);
                }}
                onStart={() => {
                  void runMindMutation(startMind);
                }}
                onStop={() => {
                  void runMindMutation(stopMind);
                }}
                onCycle={() => {
                  void runMindMutation(runMindCycle);
                }}
                onRollback={() => {
                  void runMindMutation(rollbackMind);
                }}
                onRefreshProof={() => {
                  void runMindMutation(refreshMindProof);
                }}
                onClearRestart={() => {
                  void runMindMutation(clearMindRestartFlag);
                }}
              />
            ) : null}
            {activeView === "tasks" ? <TasksView modules={dashboard?.modules ?? []} /> : null}
            {activeView === "reminders" ? <RemindersView onQuickReminder={() => void executeCommand("me lembre de revisar minhas anotacoes de viagem hoje as 14:00")} /> : null}
            {activeView === "finance" ? <FinanceView /> : null}
            {activeView === "telemetry" ? (
              <TelemetryView
                logs={deferredLogs}
                events={dashboard?.events ?? []}
                dashboard={dashboard}
                runtimeStatus={runtimeStatus}
                onOpenUpdates={() => {
                  setActiveView("settings");
                  setSettingsTab("updates");
                }}
                onRefresh={() => {
                  void refreshDashboard().catch((error: unknown) => {
                    setErrorMessage(error instanceof Error ? error.message : "Falha ao atualizar telemetria.");
                  });
                }}
              />
            ) : null}
            {activeView === "settings" ? (
              <NexusSettingsHub
                settings={settings}
                setSettings={setSettings}
                isSaving={isSaving}
                onSave={(nextSettings) => {
                  void handleSaveSettings(nextSettings);
                }}
                profileContrast={profileContrast}
                setProfileContrast={setProfileContrast}
                fontScale={fontScale}
                setFontScale={setFontScale}
                activeTab={settingsTab}
                setActiveTab={setSettingsTab}
                onOpenChatWithPrompt={(prompt) => {
                  setActiveView("chat");
                  setCommand(prompt);
                  void executeCommand(prompt);
                }}
              />
            ) : null}
          </motion.div>
        </AnimatePresence>
      </main>

      <div className="fixed bottom-6 right-6 z-30 flex items-center gap-2 rounded-full border border-white/10 bg-[#0c1422]/80 px-4 py-2 text-xs uppercase tracking-[0.24em] text-slate-400 backdrop-blur-md md:bottom-8 md:right-8">
        {isRefreshing ? <Activity className="h-4 w-4 text-[#54d8ff]" /> : <Eye className="h-4 w-4 text-[#54d8ff]" />}
        {isRefreshing ? "atualizando" : "NEXUS sincronizado"}
        <MicOff className="h-4 w-4 text-slate-500" />
      </div>
    </div>
  );
}
