import { useEffect, useMemo, useRef, useState } from "react";
import {
  Background,
  Controls,
  MiniMap,
  ReactFlow,
  addEdge,
  Handle,
  MarkerType,
  Position,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import {
  AlertTriangle,
  Bot,
  CheckCircle2,
  CircleDashed,
  GitBranch,
  LoaderCircle,
  Pause,
  Play,
  RotateCcw,
  Save,
  ShieldAlert,
  Sparkles,
  TerminalSquare,
} from "lucide-react";

import "@xyflow/react/dist/style.css";

import type { RuntimeStatus } from "@/lib/api";

type FlowNodeStatus = "pending" | "running" | "success" | "error" | "confirmation";
type FlowNodeKind = "command" | "action" | "decision" | "confirmation" | "result";
type FlowExecutionState = "idle" | "running" | "paused" | "awaiting_confirmation" | "completed";

type FlowNodeData = {
  title: string;
  detail: string;
  step: string;
  kind: FlowNodeKind;
  status: FlowNodeStatus;
};

type FlowNodeType = Node<FlowNodeData, FlowNodeKind>;

type NexusFlowProps = {
  ownerName: string;
  runtimeStatus: RuntimeStatus | null;
  healthScore: number;
  onOpenChatWithCommand: (command: string) => void;
};

type FlowSnapshot = {
  nodes: FlowNodeType[];
  edges: Edge[];
};

const STORAGE_KEY = "nexus-flow-layout-v1";
const COMMAND_TEXT = "Nexus, preparar meu ambiente de programacao";
const FLOW_LABEL = "Preparar ambiente de programacao";
const STEP_ORDER = [
  "flow-command",
  "flow-intent",
  "flow-project",
  "flow-vscode",
  "flow-git",
  "flow-deps",
  "flow-confirm",
  "flow-result",
] as const;

const statusMeta: Record<
  FlowNodeStatus,
  {
    label: string;
    toneClass: string;
    badgeClass: string;
    glowClass: string;
    accent: string;
  }
> = {
  pending: {
    label: "aguardando",
    toneClass: "text-slate-300",
    badgeClass: "border-white/10 bg-white/[0.04] text-slate-300",
    glowClass: "shadow-none",
    accent: "#94A3B8",
  },
  running: {
    label: "executando",
    toneClass: "text-cyan-200",
    badgeClass: "border-cyan-400/30 bg-cyan-400/10 text-cyan-200",
    glowClass: "shadow-[0_0_35px_rgba(34,211,238,0.14)]",
    accent: "#22D3EE",
  },
  success: {
    label: "concluido",
    toneClass: "text-emerald-300",
    badgeClass: "border-emerald-400/25 bg-emerald-400/10 text-emerald-300",
    glowClass: "shadow-[0_0_35px_rgba(34,197,94,0.12)]",
    accent: "#22C55E",
  },
  error: {
    label: "erro",
    toneClass: "text-rose-300",
    badgeClass: "border-rose-400/25 bg-rose-400/10 text-rose-300",
    glowClass: "shadow-[0_0_35px_rgba(239,68,68,0.12)]",
    accent: "#EF4444",
  },
  confirmation: {
    label: "precisa aprovacao",
    toneClass: "text-amber-300",
    badgeClass: "border-amber-400/25 bg-amber-400/10 text-amber-300",
    glowClass: "shadow-[0_0_35px_rgba(245,158,11,0.12)]",
    accent: "#F59E0B",
  },
};

const kindMeta: Record<
  FlowNodeKind,
  {
    label: string;
    icon: typeof Bot;
    tintClass: string;
  }
> = {
  command: {
    label: "Comando recebido",
    icon: Bot,
    tintClass: "text-cyan-300",
  },
  action: {
    label: "Acao",
    icon: TerminalSquare,
    tintClass: "text-sky-300",
  },
  decision: {
    label: "Entender intencao",
    icon: GitBranch,
    tintClass: "text-violet-300",
  },
  confirmation: {
    label: "Confirmacao",
    icon: ShieldAlert,
    tintClass: "text-amber-300",
  },
  result: {
    label: "Resumo",
    icon: Sparkles,
    tintClass: "text-emerald-300",
  },
};

const executionMeta: Record<
  FlowExecutionState,
  {
    label: string;
    toneClass: string;
    badgeClass: string;
  }
> = {
  idle: {
    label: "pronto para montar o fluxo",
    toneClass: "text-slate-300",
    badgeClass: "border-white/10 bg-white/[0.04] text-slate-300",
  },
  running: {
    label: "executando fluxo visual",
    toneClass: "text-cyan-200",
    badgeClass: "border-cyan-400/30 bg-cyan-400/10 text-cyan-200",
  },
  paused: {
    label: "fluxo pausado",
    toneClass: "text-amber-300",
    badgeClass: "border-amber-400/25 bg-amber-400/10 text-amber-300",
  },
  awaiting_confirmation: {
    label: "aguardando aprovacao",
    toneClass: "text-amber-300",
    badgeClass: "border-amber-400/25 bg-amber-400/10 text-amber-300",
  },
  completed: {
    label: "fluxo concluido",
    toneClass: "text-emerald-300",
    badgeClass: "border-emerald-400/25 bg-emerald-400/10 text-emerald-300",
  },
};

function buildDefaultNodes(): FlowNodeType[] {
  return [
    {
      id: "flow-command",
      type: "command",
      position: { x: 40, y: 110 },
      data: {
        step: "01",
        title: "Receber comando",
        detail: "Capturar o pedido inicial e preparar o contexto da automacao.",
        kind: "command",
        status: "pending",
      },
    },
    {
      id: "flow-intent",
      type: "decision",
      position: { x: 330, y: 110 },
      data: {
        step: "02",
        title: "Entender intencao",
        detail: "Classificar dominio, objetivo e risco antes de agir.",
        kind: "decision",
        status: "pending",
      },
    },
    {
      id: "flow-project",
      type: "action",
      position: { x: 640, y: 40 },
      data: {
        step: "03",
        title: "Verificar projeto atual",
        detail: "Detectar workspace, contexto Git e stack do projeto em foco.",
        kind: "action",
        status: "pending",
      },
    },
    {
      id: "flow-vscode",
      type: "action",
      position: { x: 640, y: 235 },
      data: {
        step: "04",
        title: "Abrir VS Code",
        detail: "Preparar editor, janelas e arquivos principais do ambiente.",
        kind: "action",
        status: "pending",
      },
    },
    {
      id: "flow-git",
      type: "action",
      position: { x: 955, y: 235 },
      data: {
        step: "05",
        title: "Rodar git status",
        detail: "Conferir branch atual, arquivos alterados e risco de conflito.",
        kind: "action",
        status: "pending",
      },
    },
    {
      id: "flow-deps",
      type: "action",
      position: { x: 1270, y: 235 },
      data: {
        step: "06",
        title: "Verificar dependencias",
        detail: "Inspecionar instalacao local, scripts e saude do projeto.",
        kind: "action",
        status: "pending",
      },
    },
    {
      id: "flow-confirm",
      type: "confirmation",
      position: { x: 1270, y: 40 },
      data: {
        step: "07",
        title: "Rodar testes",
        detail: "Solicitar aprovacao antes de gastar tempo e tocar no ambiente real.",
        kind: "confirmation",
        status: "pending",
      },
    },
    {
      id: "flow-result",
      type: "result",
      position: { x: 1585, y: 110 },
      data: {
        step: "08",
        title: "Mostrar resumo",
        detail: "Entregar status final com proximos passos e resultado do fluxo.",
        kind: "result",
        status: "pending",
      },
    },
  ];
}

function buildDefaultEdges(): Edge[] {
  return [
    ["flow-command", "flow-intent"],
    ["flow-intent", "flow-project"],
    ["flow-project", "flow-vscode"],
    ["flow-vscode", "flow-git"],
    ["flow-git", "flow-deps"],
    ["flow-deps", "flow-confirm"],
    ["flow-confirm", "flow-result"],
  ].map(([source, target], index) => ({
    id: `edge-${index}-${source}-${target}`,
    source,
    target,
    animated: true,
    markerEnd: {
      type: MarkerType.ArrowClosed,
      color: "rgba(148, 163, 184, 0.7)",
    },
    style: {
      stroke: "rgba(148, 163, 184, 0.42)",
      strokeWidth: 1.3,
    },
  }));
}

function cloneNodes(nodes: FlowNodeType[]) {
  return nodes.map((node) => ({
    ...node,
    position: { ...node.position },
    data: { ...node.data },
  }));
}

function cloneEdges(edges: Edge[]) {
  return edges.map((edge) => ({
    ...edge,
    markerEnd: edge.markerEnd,
    style: edge.style ? { ...edge.style } : edge.style,
  }));
}

function loadSnapshot(): FlowSnapshot | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw) as FlowSnapshot;
    if (!Array.isArray(parsed.nodes) || !Array.isArray(parsed.edges)) {
      return null;
    }
    return {
      nodes: cloneNodes(parsed.nodes),
      edges: cloneEdges(parsed.edges),
    };
  } catch {
    return null;
  }
}

function flowStatusIcon(status: FlowNodeStatus) {
  if (status === "running") {
    return <LoaderCircle className="h-4 w-4 animate-spin" />;
  }
  if (status === "success") {
    return <CheckCircle2 className="h-4 w-4" />;
  }
  if (status === "error") {
    return <AlertTriangle className="h-4 w-4" />;
  }
  if (status === "confirmation") {
    return <ShieldAlert className="h-4 w-4" />;
  }
  return <CircleDashed className="h-4 w-4" />;
}

function FlowNodeCard({ data }: NodeProps<FlowNodeType>) {
  const kind = kindMeta[data.kind];
  const status = statusMeta[data.status];
  const KindIcon = kind.icon;

  return (
    <div className={`nexus-flow-node-card ${status.glowClass}`}>
      <Handle type="target" position={Position.Left} style={{ background: status.accent, borderColor: status.accent }} />
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          <span className="inline-flex h-11 w-11 items-center justify-center rounded-2xl border border-white/10 bg-white/[0.05]">
            <KindIcon className={`h-5 w-5 ${kind.tintClass}`} />
          </span>
          <div>
            <p className="text-[11px] uppercase tracking-[0.24em] text-slate-500">{data.step} / {kind.label}</p>
            <h3 className="mt-2 text-sm font-semibold text-slate-100">{data.title}</h3>
          </div>
        </div>
        <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] uppercase tracking-[0.18em] ${status.badgeClass}`}>
          {flowStatusIcon(data.status)}
          {status.label}
        </span>
      </div>
      <p className="mt-4 text-sm leading-6 text-slate-400">{data.detail}</p>
      <Handle type="source" position={Position.Right} style={{ background: status.accent, borderColor: status.accent }} />
    </div>
  );
}

const nodeTypes = {
  command: FlowNodeCard,
  action: FlowNodeCard,
  decision: FlowNodeCard,
  confirmation: FlowNodeCard,
  result: FlowNodeCard,
};

export function NexusFlow({
  ownerName,
  runtimeStatus,
  healthScore,
  onOpenChatWithCommand,
}: NexusFlowProps) {
  const initialSnapshot = useMemo(() => loadSnapshot() ?? { nodes: buildDefaultNodes(), edges: buildDefaultEdges() }, []);
  const [nodes, setNodes, onNodesChange] = useNodesState<FlowNodeType>(initialSnapshot.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialSnapshot.edges);
  const [executionState, setExecutionState] = useState<FlowExecutionState>("idle");
  const [feedback, setFeedback] = useState("Fluxo pronto para ser executado ou editado.");
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);
  const timerRef = useRef<number | null>(null);
  const currentStepIndexRef = useRef(0);

  useEffect(() => {
    return () => {
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current);
      }
    };
  }, []);

  function clearTimer() {
    if (timerRef.current !== null) {
      window.clearTimeout(timerRef.current);
      timerRef.current = null;
    }
  }

  function setStatusesForStep(stepIndex: number, currentStatus: FlowNodeStatus) {
    setNodes((current) =>
      current.map((node) => {
        const index = STEP_ORDER.indexOf(node.id as (typeof STEP_ORDER)[number]);
        let nextStatus: FlowNodeStatus = "pending";
        if (index < stepIndex) {
          nextStatus = "success";
        } else if (index === stepIndex) {
          nextStatus = currentStatus;
        }

        return {
          ...node,
          data: {
            ...node.data,
            status: nextStatus,
          },
        };
      }),
    );
  }

  function runStep(stepIndex: number) {
    clearTimer();
    const stepId = STEP_ORDER[stepIndex];
    if (!stepId) {
      setExecutionState("completed");
      setActiveNodeId("flow-result");
      setFeedback("Fluxo concluido. O Nexus entregou o resumo final do ambiente.");
      return;
    }

    currentStepIndexRef.current = stepIndex;
    const currentNode = nodes.find((node) => node.id === stepId);
    const nextStatus: FlowNodeStatus = stepId === "flow-confirm" ? "confirmation" : "running";
    setStatusesForStep(stepIndex, nextStatus);
    setActiveNodeId(stepId);
    setFeedback(currentNode ? `${currentNode.data.title} em execucao.` : "Executando fluxo visual.");

    if (stepId === "flow-confirm") {
      setExecutionState("awaiting_confirmation");
      setFeedback("Fluxo pausado aguardando sua aprovacao para rodar os testes.");
      return;
    }

    setExecutionState("running");
    timerRef.current = window.setTimeout(() => {
      setNodes((current) =>
        current.map((node) =>
          node.id === stepId
            ? {
                ...node,
                data: {
                  ...node.data,
                  status: "success",
                },
              }
            : node,
        ),
      );

      if (stepId === "flow-result") {
        setExecutionState("completed");
        setFeedback("Fluxo concluido. Workspace, Git, dependencias e resumo finalizados.");
        return;
      }

      runStep(stepIndex + 1);
    }, stepId === "flow-command" ? 620 : 960);
  }

  function resetStatuses() {
    clearTimer();
    currentStepIndexRef.current = 0;
    setActiveNodeId(null);
    setExecutionState("idle");
    setFeedback("Fluxo limpo. Arraste, conecte ou execute novamente.");
    setNodes((current) =>
      current.map((node) => ({
        ...node,
        data: {
          ...node.data,
          status: "pending",
        },
      })),
    );
  }

  function saveSnapshot() {
    if (typeof window === "undefined") {
      return;
    }
    const snapshot: FlowSnapshot = {
      nodes: nodes.map((node) => ({
        ...node,
        position: { ...node.position },
        data: { ...node.data },
      })),
      edges: edges.map((edge) => ({
        ...edge,
        markerEnd: edge.markerEnd,
        style: edge.style ? { ...edge.style } : edge.style,
      })),
    };
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(snapshot));
    setFeedback("Fluxo salvo localmente. O Nexus vai reabrir este layout na proxima vez.");
  }

  function handleRun() {
    if (executionState === "awaiting_confirmation") {
      setNodes((current) =>
        current.map((node) =>
          node.id === "flow-confirm"
            ? {
                ...node,
                data: {
                  ...node.data,
                  status: "success",
                },
              }
            : node,
        ),
      );
      runStep(currentStepIndexRef.current + 1);
      return;
    }

    if (executionState === "paused") {
      runStep(currentStepIndexRef.current);
      return;
    }

    resetStatuses();
    window.setTimeout(() => runStep(0), 60);
  }

  function handlePause() {
    if (executionState !== "running") {
      return;
    }
    clearTimer();
    setExecutionState("paused");
    setFeedback("Fluxo pausado. Voce pode continuar do ponto atual a qualquer momento.");
  }

  const completionCount = nodes.filter((node) => node.data.status === "success").length;
  const progress = Math.round((completionCount / STEP_ORDER.length) * 100);
  const sortedNodes = [...nodes].sort(
    (left, right) =>
      STEP_ORDER.indexOf(left.id as (typeof STEP_ORDER)[number]) - STEP_ORDER.indexOf(right.id as (typeof STEP_ORDER)[number]),
  );
  const activeNode = sortedNodes.find((node) => node.id === activeNodeId) ?? null;

  return (
    <section className="space-y-6 px-4 py-8 lg:px-12">
      <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_360px]">
        <div className="nexus-flow-shell">
          <div className="nexus-flow-toolbar">
            <div>
              <p className="shell-eyebrow text-[#78d8ff]">Nexus Flow</p>
              <h2 className="shell-display mt-2 text-3xl font-semibold text-white">{FLOW_LABEL}</h2>
              <p className="mt-2 text-sm leading-7 text-slate-400">
                Visualize o plano do Nexus, acompanhe execucao por etapa e ajuste o fluxo no canvas com arrastar e conectar.
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              <button type="button" className="nexus-flow-toolbar-button nexus-flow-toolbar-button-primary" onClick={handleRun}>
                <Play className="h-4 w-4" />
                {executionState === "awaiting_confirmation" ? "Aprovar etapa" : executionState === "paused" ? "Continuar" : "Executar"}
              </button>
              <button type="button" className="nexus-flow-toolbar-button" onClick={handlePause}>
                <Pause className="h-4 w-4" />
                Pausar
              </button>
              <button type="button" className="nexus-flow-toolbar-button" onClick={resetStatuses}>
                <RotateCcw className="h-4 w-4" />
                Limpar
              </button>
              <button type="button" className="nexus-flow-toolbar-button" onClick={saveSnapshot}>
                <Save className="h-4 w-4" />
                Salvar fluxo
              </button>
            </div>
          </div>

          <div className="nexus-flow-feedback-bar">
            <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs uppercase tracking-[0.2em] ${executionMeta[executionState].badgeClass}`}>
              {executionMeta[executionState].label}
            </span>
            <p className={`text-sm leading-6 ${executionMeta[executionState].toneClass}`}>{feedback}</p>
          </div>

          <div className="nexus-flow-canvas">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={(connection: Connection) => {
                setEdges((current) =>
                  addEdge(
                    {
                      ...connection,
                      animated: true,
                      markerEnd: {
                        type: MarkerType.ArrowClosed,
                        color: "rgba(148, 163, 184, 0.7)",
                      },
                      style: {
                        stroke: "rgba(148, 163, 184, 0.42)",
                        strokeWidth: 1.3,
                      },
                    },
                    current,
                  ),
                );
              }}
              fitView
              fitViewOptions={{ padding: 0.18 }}
              minZoom={0.45}
              maxZoom={1.4}
              className="nexus-flow-react"
            >
              <MiniMap
                pannable
                zoomable
                className="!rounded-2xl !border !border-white/10 !bg-[#0b111d]/90"
                nodeColor={(node) => statusMeta[(node.data as FlowNodeData).status].accent}
                maskColor="rgba(7, 10, 18, 0.52)"
              />
              <Controls className="!rounded-2xl !border !border-white/10 !bg-[#0b111d]/90" />
              <Background color="rgba(148, 163, 184, 0.12)" gap={22} size={1} />
            </ReactFlow>
          </div>
        </div>

        <div className="grid gap-5">
          <div className="nexus-flow-panel">
            <p className="shell-eyebrow">Resumo operacional</p>
            <h3 className="mt-3 text-xl font-semibold text-white">{FLOW_LABEL}</h3>
            <p className="mt-2 text-sm leading-7 text-slate-400">
              Nexus Flow mostra exatamente o que o Nexus entendeu, o que vai executar, onde precisa de voce e o que ja foi concluido.
            </p>
            <div className="mt-5 space-y-3">
              <div className="flex items-center justify-between gap-3 text-sm text-slate-400">
                <span>Progresso total</span>
                <span className="font-semibold text-slate-100">{progress}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-white/6">
                <div
                  className="h-full rounded-full bg-[linear-gradient(90deg,rgba(34,211,238,0.9),rgba(139,92,246,0.78))] transition-[width] duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
            <div className="mt-5 grid grid-cols-2 gap-3">
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="shell-eyebrow">Comando</p>
                <p className="mt-2 text-sm leading-6 text-slate-200">{COMMAND_TEXT}</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="shell-eyebrow">Status atual</p>
                <p className={`mt-2 text-sm font-semibold ${executionMeta[executionState].toneClass}`}>{executionMeta[executionState].label}</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="shell-eyebrow">Saude Nexus</p>
                <p className="mt-2 text-2xl font-semibold text-cyan-200">{healthScore || 0}%</p>
                <p className="mt-2 text-xs text-slate-500">base do sistema ativa</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                <p className="shell-eyebrow">Runtime</p>
                <p className="mt-2 text-2xl font-semibold text-emerald-200">{runtimeStatus?.cpu ?? 0}%</p>
                <p className="mt-2 text-xs text-slate-500">CPU / RAM {runtimeStatus?.ram ?? 0}%</p>
              </div>
            </div>
            <div className="mt-5 flex flex-wrap gap-3">
              <button type="button" className="shell-chip" onClick={() => onOpenChatWithCommand("preparar meu ambiente de programacao")}>
                executar no chat
              </button>
              <button type="button" className="shell-chip" onClick={() => onOpenChatWithCommand("modo faculdade")}>
                testar fluxo faculdade
              </button>
            </div>
          </div>

          <div className="nexus-flow-panel">
            <p className="shell-eyebrow">Etapas do fluxo</p>
            <div className="mt-4 space-y-3">
              {sortedNodes.map((node) => {
                const status = statusMeta[node.data.status];
                const isActive = node.id === activeNode?.id;
                return (
                  <div key={node.id} className={`nexus-flow-step-row ${isActive ? "nexus-flow-step-row-active" : ""}`}>
                    <div className={`nexus-flow-step-dot ${status.toneClass}`}>{flowStatusIcon(node.data.status)}</div>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-sm font-semibold text-white">{node.data.title}</span>
                        <span className={`inline-flex rounded-full border px-2 py-0.5 text-[10px] uppercase tracking-[0.18em] ${status.badgeClass}`}>
                          {status.label}
                        </span>
                      </div>
                      <p className="mt-1 text-sm leading-6 text-slate-400">{node.data.detail}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="nexus-flow-panel">
            <p className="shell-eyebrow">Bloco em foco</p>
            {activeNode ? (
              <>
                <h3 className="mt-3 text-lg font-semibold text-white">{activeNode.data.title}</h3>
                <p className="mt-2 text-sm leading-7 text-slate-400">{activeNode.data.detail}</p>
                <div className="mt-4 rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                  <p className="shell-eyebrow">Nexus thinking</p>
                  <p className="mt-2 text-sm leading-7 text-slate-200">
                    {executionState === "awaiting_confirmation"
                      ? "Etapa sensivel detectada. O Nexus esta esperando sua aprovacao para continuar com os testes automatizados."
                      : executionState === "running"
                        ? "O Nexus esta resolvendo esta etapa agora e vai avancar sozinho para a proxima assim que concluir."
                        : "Este bloco esta selecionado como referencia atual do fluxo."}
                  </p>
                </div>
              </>
            ) : (
              <>
                <h3 className="mt-3 text-lg font-semibold text-white">Fluxo pronto para interacao</h3>
                <p className="mt-2 text-sm leading-7 text-slate-400">
                  Arraste os blocos, ligue novas arestas e depois use a toolbar para executar ou salvar seu layout visual.
                </p>
              </>
            )}
            <p className="mt-5 text-xs uppercase tracking-[0.22em] text-slate-500">Owner context / {ownerName}</p>
          </div>
        </div>
      </div>
    </section>
  );
}
