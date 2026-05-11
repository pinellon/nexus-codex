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
};

export type ChatResponse = {
  command: unknown;
  understood: string;
  response: string;
  should_exit: boolean;
  confirmation_required: boolean;
  confirmation_message?: string | null;
};

const rawBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";
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
