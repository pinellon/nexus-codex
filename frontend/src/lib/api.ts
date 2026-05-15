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
  detail: string;
  permission: string;
  action_label: string;
  configured: boolean;
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
  node_type: "vault" | "area" | "note" | "tag" | "finance" | "account" | "category" | "transaction" | "bill" | "goal";
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
    finance?: number;
  };
};

export type FinanceTransaction = {
  id: string;
  title: string;
  amount: number;
  type: "income" | "expense";
  category: string;
  account: string;
  date: string;
  notes: string;
  finance_type: "variable" | "recurring" | "installments";
  created_at: string;
};

export type FinanceBill = {
  id: string;
  title: string;
  amount: number;
  due_date: string;
  paid: boolean;
  recurrence: "none" | "monthly" | "weekly" | "yearly";
  account: string;
  category: string;
  notes: string;
  created_at: string;
  paid_at?: string | null;
};

export type FinanceGoal = {
  id: string;
  title: string;
  target_amount: number;
  current_amount: number;
  deadline: string;
  notes: string;
  created_at: string;
  progress_ratio: number;
  remaining_amount: number;
};

export type FinanceSummary = {
  month_label: string;
  current_balance: number;
  month_income: number;
  month_expense: number;
  available_until_month_end: number;
  upcoming_bills_count: number;
  upcoming_bills_amount: number;
  overdue_bills_count: number;
  overdue_bills_amount: number;
  active_installments_count: number;
  active_installments_amount: number;
  upcoming_bills: FinanceBill[];
  overdue_bills: FinanceBill[];
  goals: FinanceGoal[];
};

export type FinanceChartPoint = {
  date: string;
  label: string;
  balance: number;
  income: number;
  expense: number;
  is_future: boolean;
};

export type FinanceMonthlyChart = {
  start_date: string;
  end_date: string;
  points: FinanceChartPoint[];
  opening_balance: number;
};

export type FinanceCategoryBreakdown = {
  categories: Array<{ category: string; amount: number }>;
  accounts: Array<{ account: string; amount: number }>;
};

export type ChatResponse = {
  command: unknown;
  understood: string;
  response: string;
  should_exit: boolean;
  confirmation_required: boolean;
  confirmation_message?: string | null;
};

export type ConversationState =
  | "idle"
  | "listening"
  | "thinking"
  | "generating_audio"
  | "speaking"
  | "ready"
  | "interrupted"
  | "error"
  | "paused";

export type ConversationSession = {
  session_id: string;
  current_topic: string;
  current_goal: string;
  last_user_messages: string[];
  last_assistant_messages: string[];
  study_mode_enabled: boolean;
  last_summary: string;
  related_notes: string[];
  created_at: string;
  updated_at: string;
};

export type ConversationMessageResponse = {
  ok: boolean;
  session_id: string;
  state: ConversationState;
  intent: string;
  topic: string;
  response: string;
  should_speak: boolean;
  saved_note_path: string | null;
  session: ConversationSession;
};

export type ConversationStateResponse = {
  ok: boolean;
  state: ConversationState;
  session: ConversationSession | null;
};

export type VoiceDeviceRow = {
  index: number;
  name: string;
  max_input_channels: number;
  max_output_channels: number;
  default_samplerate: number;
};

export type VoiceDevicesResponse = {
  ok: boolean;
  error?: string;
  default_input_index: number | null;
  default_output_index: number | null;
  inputs: VoiceDeviceRow[];
  outputs: VoiceDeviceRow[];
};

export type VoiceListenOnceResponse = {
  ok: boolean;
  text: string;
  backend: string;
  confidence: number | null;
  device_index: string | number | null;
  error?: string;
};

export type VoiceProfile = {
  id: string;
  label: string;
  provider: string;
  voice: string;
  speed: number;
  pitch: string;
  instructions: string;
};

export type VoiceProfilesResponse = {
  ok: boolean;
  profiles: VoiceProfile[];
  providers: string[];
};

export type VoiceChunk = {
  id: string;
  text: string;
  audio_url: string;
  content_type: string;
  order: string;
};

export type VoiceChunksResponse = {
  ok: boolean;
  chunks: VoiceChunk[];
};

export type MediaAnalysisResponse = {
  filename: string;
  media_type: string;
  response: string;
  supported: boolean;
};

const rawBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8001";
export const apiBase = rawBaseUrl.replace(/\/$/, "");
let localApiToken = (import.meta.env.VITE_NEXUS_API_TOKEN as string | undefined)?.trim() ?? "";

export function setApiToken(token: string | null | undefined) {
  localApiToken = token?.trim() ?? "";
}

function buildHeaders(initHeaders?: HeadersInit, includeJson = true) {
  const headers = new Headers(initHeaders);
  if (includeJson && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (localApiToken) {
    headers.set("X-NEXUS-TOKEN", localApiToken);
  }
  return headers;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    ...init,
    headers: buildHeaders(init?.headers),
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

export function fetchFinanceSummary() {
  return fetchJson<FinanceSummary>("/api/finance/summary");
}

export async function fetchFinanceTransactions() {
  const payload = await fetchJson<{ items: FinanceTransaction[] }>("/api/finance/transactions");
  return payload.items;
}

export async function fetchFinanceBills() {
  const payload = await fetchJson<{ items: FinanceBill[] }>("/api/finance/bills");
  return payload.items;
}

export async function fetchFinanceGoals() {
  const payload = await fetchJson<{ items: FinanceGoal[] }>("/api/finance/goals");
  return payload.items;
}

export function fetchFinanceMonthlyChart() {
  return fetchJson<FinanceMonthlyChart>("/api/finance/chart/monthly");
}

export function fetchFinanceCategories() {
  return fetchJson<FinanceCategoryBreakdown>("/api/finance/categories");
}

export async function createFinanceTransaction(payload: Partial<FinanceTransaction> & { title: string; amount: number; type: "income" | "expense" }) {
  const response = await fetchJson<{ item: FinanceTransaction }>("/api/finance/transactions", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return response.item;
}

export async function createFinanceBill(payload: Partial<FinanceBill> & { title: string; amount: number }) {
  const response = await fetchJson<{ item: FinanceBill }>("/api/finance/bills", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return response.item;
}

export async function markFinanceBillPaid(billId: string) {
  const response = await fetchJson<{ item: FinanceBill }>(`/api/finance/bills/${encodeURIComponent(billId)}/pay`, {
    method: "PUT",
  });
  return response.item;
}

export async function createFinanceGoal(payload: Partial<FinanceGoal> & { title: string; target_amount: number }) {
  const response = await fetchJson<{ item: FinanceGoal }>("/api/finance/goals", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  return response.item;
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

export function sendConversationMessage(payload: {
  text: string;
  session_id?: string;
  study_mode?: boolean;
  save_to_obsidian?: boolean;
}) {
  return fetchJson<ConversationMessageResponse>("/api/conversation/message", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function resetConversationSession(sessionId: string) {
  return fetchJson<{ ok: boolean }>("/api/conversation/reset", {
    method: "POST",
    body: JSON.stringify({ session_id: sessionId }),
  });
}

export function saveConversationNote(payload: {
  session_id: string;
  title: string;
  content: string;
}) {
  return fetchJson<{ ok: boolean; path: string | null }>("/api/conversation/save-note", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function fetchConversationState() {
  return fetchJson<ConversationStateResponse>("/api/conversation/state");
}

export function fetchVoiceDevices() {
  return fetchJson<VoiceDevicesResponse>("/api/voice/devices");
}

export function listenVoiceOnce(payload?: { timeout?: number; phrase_time_limit?: number }) {
  return fetchJson<VoiceListenOnceResponse>("/api/voice/listen-once", {
    method: "POST",
    body: JSON.stringify(payload ?? {}),
  });
}

export function fetchVoiceProfiles() {
  return fetchJson<VoiceProfilesResponse>("/api/voice/profiles");
}

export function fetchVoiceChunks(payload: { text: string; provider?: string; profile?: string }) {
  return fetchJson<VoiceChunksResponse>("/api/voice/chunks", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function fetchVoiceTestAudio(payload: { provider?: string; profile?: string }) {
  const response = await fetch(`${apiBase}/api/voice/test`, {
    method: "POST",
    headers: buildHeaders(),
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `HTTP ${response.status}`);
  }
  return response.blob();
}

export function stopProfessionalVoice() {
  return fetchJson<{ ok: boolean; state: string; token: string }>("/api/voice/stop", {
    method: "POST",
    body: JSON.stringify({}),
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
    headers: buildHeaders(),
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
