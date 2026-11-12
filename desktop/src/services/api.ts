/**
 * AURA API Client
 *
 * Communicates with the local FastAPI backend on 127.0.0.1:8765.
 * All requests are local — never exposed to external networks.
 */

import type {
  ChatRequest,
  ChatResponse,
  BackendHealth,
  SystemInfo,
  ActivityEntry,
  Task,
  AuraSettings,
  ToolDefinition,
} from "@/types";

const BASE_URL = "http://127.0.0.1:8765";
const WS_URL   = "ws://127.0.0.1:8765";

// ─── HTTP helpers ─────────────────────────────────────────────────────────────

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  if (!response.ok) {
    const text = await response.text().catch(() => "Unknown error");
    throw new Error(`API ${response.status}: ${text}`);
  }
  return response.json() as Promise<T>;
}

const get  = <T>(path: string)              => request<T>(path, { method: "GET" });
const post = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });
const put  = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "PUT",  body: JSON.stringify(body) });

// ─── REST client ──────────────────────────────────────────────────────────────

class AuraApiClient {
  async health(): Promise<BackendHealth> {
    return get<BackendHealth>("/api/health");
  }
  async ping(): Promise<boolean> {
    try {
      const r = await get<{ status: string }>("/api/health");
      return r.status === "ok" || r.status === "degraded";
    } catch { return false; }
  }
  async sendMessage(req: ChatRequest): Promise<ChatResponse> {
    return post<ChatResponse>("/api/chat", req);
  }
  async getSystemInfo(): Promise<SystemInfo> {
    return get<SystemInfo>("/api/system");
  }
  async listTools(): Promise<ToolDefinition[]> {
    return get<ToolDefinition[]>("/api/tools");
  }
  async executeTool(toolName: string, args: Record<string, unknown>) {
    return post("/api/tools/execute", { tool: toolName, arguments: args });
  }
  async confirmAction(confirmationId: string, confirmed: boolean): Promise<void> {
    await post("/api/confirmations/respond", { confirmation_id: confirmationId, confirmed });
  }
  async getActivity(limit = 100): Promise<ActivityEntry[]> {
    return get<ActivityEntry[]>(`/api/activity?limit=${limit}`);
  }
  async getTasks(): Promise<Task[]>                         { return get<Task[]>("/api/tasks"); }
  async createTask(task: Partial<Task>): Promise<Task>      { return post<Task>("/api/tasks", task); }
  async updateTask(id: string, u: Partial<Task>): Promise<Task> { return put<Task>(`/api/tasks/${id}`, u); }
  async getSettings(): Promise<AuraSettings>                { return get<AuraSettings>("/api/settings"); }
  async updateSettings(u: Partial<AuraSettings>)            { return put("/api/settings", u); }
  async setApiKey(provider: string, apiKey: string): Promise<void> {
    await put("/api/settings/api-key", { provider, api_key: apiKey });
  }
}

// ─── WebSocket manager ────────────────────────────────────────────────────────

type EventHandler = (event: unknown) => void;

class AuraWebSocket {
  private ws: WebSocket | null = null;
  private handlers = new Map<string, EventHandler[]>();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = 2000;
  private active = false;   // set true only after connect(), false after disconnect()

  connect(): void {
    this.active = true;
    this._open();
  }

  private _open(): void {
    if (!this.active) return;
    if (this.ws && this.ws.readyState <= WebSocket.OPEN) return;

    try {
      this.ws = new WebSocket(`${WS_URL}/ws/agent`);

      this.ws.onopen = () => {
        this.reconnectDelay = 2000;  // reset on success
        this._emit("connected", null);
      };

      this.ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data as string);
          this._emit("message", data);
          if (data?.type) this._emit(data.type, data);
        } catch { /* non-JSON — ignore */ }
      };

      this.ws.onclose = () => {
        this.ws = null;
        this._emit("disconnected", null);
        // Only reconnect if still active — with capped exponential backoff
        if (this.active) this._scheduleReconnect();
      };

      this.ws.onerror = () => {
        this._emit("error", null);
        // onclose fires right after — reconnect handled there
      };
    } catch {
      if (this.active) this._scheduleReconnect();
    }
  }

  private _scheduleReconnect(): void {
    if (this.reconnectTimer) return;
    // Cap at 30 seconds so it doesn't spam the backend
    this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 30_000);
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this._open();
    }, this.reconnectDelay);
  }

  disconnect(): void {
    this.active = false;
    if (this.reconnectTimer) { clearTimeout(this.reconnectTimer); this.reconnectTimer = null; }
    if (this.ws) {
      this.ws.onclose = null;   // prevent reconnect loop on intentional close
      this.ws.close();
      this.ws = null;
    }
  }

  on(event: string, handler: EventHandler): () => void {
    const list = this.handlers.get(event) ?? [];
    list.push(handler);
    this.handlers.set(event, list);
    return () => this.off(event, handler);
  }

  off(event: string, handler: EventHandler): void {
    this.handlers.set(event, (this.handlers.get(event) ?? []).filter(h => h !== handler));
  }

  private _emit(event: string, data: unknown): void {
    (this.handlers.get(event) ?? []).forEach(h => h(data));
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// ─── Singletons ───────────────────────────────────────────────────────────────

export const apiClient = new AuraApiClient();
export const wsClient  = new AuraWebSocket();
