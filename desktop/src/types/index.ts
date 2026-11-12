// ─── AURA Shared Types ────────────────────────────────────────────────────────

// ── Agent / Chat ──────────────────────────────────────────────────────────────

export type MessageRole = "user" | "assistant" | "system" | "tool";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  /** True if this message includes tool execution details */
  hasPlan?: boolean;
  plan?: AgentPlan;
  status?: MessageStatus;
}

export type MessageStatus =
  | "pending"
  | "thinking"
  | "planning"
  | "executing"
  | "waiting_confirmation"
  | "completed"
  | "error";

export interface AgentPlan {
  steps: PlanStep[];
  status: "pending" | "in_progress" | "completed" | "failed";
}

export interface PlanStep {
  id: string;
  description: string;
  tool?: string;
  status: "pending" | "in_progress" | "completed" | "failed" | "skipped";
  result?: string;
  error?: string;
}

// ── Tool System ───────────────────────────────────────────────────────────────

export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: Record<string, unknown>;
  risk_level: RiskLevel;
  requires_confirmation: boolean;
  category: ToolCategory;
}

export type ToolCategory =
  | "files"
  | "apps"
  | "system"
  | "network"
  | "bluetooth"
  | "audio"
  | "settings"
  | "processes"
  | "diagnostics"
  | "tasks";

export interface ToolResult {
  success: boolean;
  message: string;
  data?: unknown;
  error?: string | null;
  error_code?: string;
}

// ── Confirmation ──────────────────────────────────────────────────────────────

export interface ConfirmationRequest {
  id: string;
  action: string;
  target: string;
  description: string;
  risk_level: RiskLevel;
  consequences: string[];
  tool: string;
  arguments: Record<string, unknown>;
}

// ── Activity ──────────────────────────────────────────────────────────────────

export type ActivityType =
  | "command"
  | "tool_executed"
  | "file_changed"
  | "app_launched"
  | "setting_changed"
  | "error"
  | "info";

export interface ActivityEntry {
  id: string;
  type: ActivityType;
  summary: string;
  detail?: string;
  timestamp: Date;
  risk_level?: RiskLevel;
  success?: boolean;
}

// ── System Info ───────────────────────────────────────────────────────────────

export interface SystemInfo {
  cpu_percent: number;
  cpu_count: number;
  ram_total_gb: number;
  ram_used_gb: number;
  ram_percent: number;
  disk_total_gb: number;
  disk_used_gb: number;
  disk_free_gb: number;
  disk_percent: number;
  battery_percent: number | null;
  battery_plugged: boolean | null;
  platform: string;
  windows_version: string;
  hostname: string;
  uptime_seconds: number;
  architecture: string;
}

// ── Network ───────────────────────────────────────────────────────────────────

export interface NetworkStatus {
  connected: boolean;
  ssid: string | null;
  signal_strength: number | null;
  ip_address: string | null;
  gateway: string | null;
  dns_servers: string[];
  adapter_name: string | null;
  adapter_status: string;
}

// ── Tasks ─────────────────────────────────────────────────────────────────────

export type TaskPriority = "low" | "medium" | "high";
export type TaskStatus = "pending" | "in_progress" | "completed" | "cancelled";

export interface Task {
  id: string;
  title: string;
  description?: string;
  created_at: Date;
  due_at?: Date | null;
  priority: TaskPriority;
  status: TaskStatus;
}

// ── Settings ──────────────────────────────────────────────────────────────────

export type AIProvider = "openai" | "anthropic" | "gemini" | "ollama" | "groq";
export type PermissionMode = "safe" | "balanced" | "power_user";
export type STTProvider = "whisper_local" | "whisper_api" | "azure_stt";
export type TTSProvider = "windows_sapi" | "piper" | "azure_tts" | "elevenlabs";
export type Theme = "dark" | "light" | "system";

export interface AuraSettings {
  ai_provider: AIProvider;
  model: string;
  stt_provider: STTProvider;
  tts_provider: TTSProvider;
  permission_mode: PermissionMode;
  theme: Theme;
  enable_memory: boolean;
  enable_activity_log: boolean;
  enable_voice: boolean;
  dry_run_default: boolean;
  start_minimized: boolean;
  global_hotkey: string;
  first_run_complete: boolean;
}

// ── Voice ─────────────────────────────────────────────────────────────────────

export type VoiceState =
  | "idle"
  | "listening"
  | "processing"
  | "thinking"
  | "speaking"
  | "error";

// ── WebSocket Events ──────────────────────────────────────────────────────────

export type AgentEventType =
  | "LISTENING"
  | "THINKING"
  | "PLANNING"
  | "EXECUTING_TOOL"
  | "WAITING_CONFIRMATION"
  | "COMPLETED"
  | "ERROR"
  | "TOOL_RESULT"
  | "PLAN_UPDATE"
  | "STATUS";

export interface AgentEvent {
  type: AgentEventType;
  message?: string;
  data?: unknown;
  timestamp: string;
}

// ── API Request / Response ────────────────────────────────────────────────────

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  context?: Record<string, unknown>;
}

export interface ChatResponse {
  message: string;
  conversation_id: string;
  plan?: AgentPlan;
  confirmation_required?: ConfirmationRequest;
  success: boolean;
  error?: string | null;
}

export interface BackendHealth {
  status: "ok" | "degraded" | "error";
  version: string;
  ai_provider_connected: boolean;
  tools_loaded: number;
  uptime_seconds: number;
}
