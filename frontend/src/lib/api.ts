export type HealthReport = {
  score: number;
  status: string;
  found: string[];
  missing: string[];
  warnings: string[];
};

export type DashboardModule = {
  id: string;
  title: string;
  description: string;
  status: string;
  tone: "cyan" | "amber" | "lime" | "orange" | "rose" | "sky";
  sector: string;
  icon: string;
  examples: string[];
};

export type SessionEvent = {
  timestamp: string;
  kind: string;
  message: string;
  data: Record<string, unknown>;
};

export type DashboardPayload = {
  project_root: string;
  health: HealthReport;
  modules: DashboardModule[];
  logs: string[];
  events: SessionEvent[];
  settings: Record<string, unknown>;
  runtime: RuntimeStatus;
};

export type RuntimeStatus = {
  cpu: number;
  ram: number;
  disk: number;
  updated_at: string;
};

export type AutomationAction = {
  label: string;
  command: string;
};

export type AutomationSection = {
  title: string;
  tone: "secondary" | "success" | "ghost" | "danger";
  actions: AutomationAction[];
};

export type MindChangedFile = {
  path: string;
  action: "edit" | "create" | "delete";
};

export type MindHistoryItem = {
  timestamp: string;
  summary: string;
  files: MindChangedFile[];
};

export type MindProofVerification = {
  status: string;
  label: string;
  detail: string;
};

export type MindProofCommit = {
  hash: string;
  full_hash?: string;
  msg: string;
  date: string;
  author?: string;
  is_nexus?: boolean;
};

export type MindProof = {
  generated_at: string;
  commits: MindProofCommit[];
  verifications: MindProofVerification[];
};

export type MindState = {
  settings: {
    directive?: string;
    auto_restart?: boolean;
    active?: boolean;
    mode?: string;
    interval?: number;
  };
  running: boolean;
  cycle_active: boolean;
  last_error: string | null;
  last_modified_path: string | null;
  logs: string[];
  changed_files: MindChangedFile[];
  history: MindHistoryItem[];
  score: Record<string, number>;
  proof: MindProof | null;
  restart: {
    pending_reason: string | null;
    requested_at: string | null;
  };
};

export type VisionFrame = {
  base64_data: string;
  media_type: string;
  width: number;
  height: number;
  source: string;
};

export type VisionResponse = {
  ok: boolean;
  action: string;
  image: VisionFrame | null;
  response: string;
};

export type VisionStatus = {
  ok: boolean;
  camera_indices: number[];
  default_camera_index: number;
};

export type MemoryGraphNode = {
  id: string;
  label: string;
  node_type: "vault" | "area" | "note" | "tag";
  group: string;
  size: number;
  path: string;
};

export type MemoryGraphEdge = {
  source: string;
  target: string;
  relation: "contains" | "links" | "tagged";
};

export type MemoryGraphPayload = {
  enabled: boolean;
  vault_name: string;
  vault_path: string;
  nodes: MemoryGraphNode[];
  edges: MemoryGraphEdge[];
  stats: {
    areas: number;
    notes: number;
    tags: number;
    links: number;
  };
};

export type ChatResponse = {
  command: unknown;
  understood: string;
  response: string;
  should_exit: boolean;
  confirmation_required: boolean;
  confirmation_message?: string | null;
};

export type MediaAnalysisResponse = {
  filename: string;
  media_type: string;
  response: string;
  supported: boolean;
};

const rawBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8001";
export const apiBase = rawBaseUrl.replace(/\/$/, "");

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
    ...init,
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }

  return (await response.json()) as T;
}

export function fetchDashboard() {
  return fetchJson<DashboardPayload>("/api/dashboard");
}

export function fetchRuntimeStatus() {
  return fetchJson<RuntimeStatus>("/api/runtime/status");
}

export async function fetchAutomationCatalog(query = "") {
  const suffix = query.trim() ? `?query=${encodeURIComponent(query.trim())}` : "";
  const payload = await fetchJson<{ sections: AutomationSection[] }>(`/api/automation/catalog${suffix}`);
  return payload.sections;
}

export function fetchMindState() {
  return fetchJson<MindState>("/api/mind/state");
}

export function saveMindSettings(settings: Record<string, unknown>) {
  return fetchJson<MindState>("/api/mind/settings", {
    method: "PUT",
    body: JSON.stringify({ settings }),
  });
}

async function postMindAction(path: string) {
  return fetchJson<MindState>(path, { method: "POST" });
}

export function startMind() {
  return postMindAction("/api/mind/start");
}

export function stopMind() {
  return postMindAction("/api/mind/stop");
}

export function runMindCycle() {
  return postMindAction("/api/mind/cycle");
}

export function rollbackMind() {
  return postMindAction("/api/mind/rollback");
}

export function refreshMindProof() {
  return postMindAction("/api/mind/proof");
}

export function clearMindRestartFlag() {
  return postMindAction("/api/mind/restart/clear");
}

export function fetchVisionStatus() {
  return fetchJson<VisionStatus>("/api/vision/status");
}

async function postVisionAction(path: string, payload?: Record<string, unknown>) {
  return fetchJson<VisionResponse>(path, {
    method: "POST",
    body: JSON.stringify(payload ?? {}),
  });
}

export function captureVisionScreen() {
  return postVisionAction("/api/vision/screen/capture");
}

export function captureVisionCamera(cameraIndex = 0) {
  return postVisionAction("/api/vision/camera/capture", { camera_index: cameraIndex });
}

export function runVisionScreenAction(action: "describe" | "read-text" | "analyze-code" | "find-objects" | "ask", question = "") {
  return postVisionAction(`/api/vision/screen/${action}`, { question });
}

export function runVisionCameraAction(action: "describe" | "find-objects" | "ask", question = "", cameraIndex = 0) {
  return postVisionAction(`/api/vision/camera/${action}`, { question, camera_index: cameraIndex });
}

export function fetchMemoryGraph() {
  return fetchJson<MemoryGraphPayload>("/api/memory/graph");
}

export async function fetchSettings() {
  const payload = await fetchJson<{ settings: Record<string, unknown> }>("/api/settings");
  return payload.settings;
}

export async function saveSettings(settings: Record<string, unknown>) {
  const payload = await fetchJson<{ settings: Record<string, unknown> }>("/api/settings", {
    method: "PUT",
    body: JSON.stringify({ settings }),
  });
  return payload.settings;
}

export function sendChat(text: string, confirm = false) {
  return fetchJson<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({ text, confirm }),
  });
}

export async function analyzeMedia(file: File, question = "") {
  const buffer = await file.arrayBuffer();
  const bytes = new Uint8Array(buffer);
  let binary = "";
  const chunkSize = 0x8000;
  for (let index = 0; index < bytes.length; index += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(index, index + chunkSize));
  }
  const contentBase64 = btoa(binary);

  const response = await fetch(`${apiBase}/api/media/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      filename: file.name,
      media_type: file.type,
      question,
      content_base64: contentBase64,
    }),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }

  return (await response.json()) as MediaAnalysisResponse;
}
