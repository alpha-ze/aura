import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type {
  ChatMessage,
  ActivityEntry,
  Task,
  AuraSettings,
  SystemInfo,
  NetworkStatus,
  VoiceState,
  AgentEvent,
  ConfirmationRequest,
  MessageStatus,
} from "@/types";

// ─── Default Settings ─────────────────────────────────────────────────────────

const DEFAULT_SETTINGS: AuraSettings = {
  ai_provider: "groq",
  model: "qwen/qwen3.8-27b",
  stt_provider: "whisper_local",
  tts_provider: "windows_sapi",
  permission_mode: "balanced",
  theme: "dark",
  enable_memory: true,
  enable_activity_log: true,
  enable_voice: true,
  dry_run_default: false,
  start_minimized: false,
  global_hotkey: "Ctrl+Space",
  first_run_complete: false,
};

// ─── Chat Store ───────────────────────────────────────────────────────────────

interface ChatStore {
  messages: ChatMessage[];
  conversationId: string | null;
  agentStatus: MessageStatus;
  isStreaming: boolean;

  addMessage: (msg: ChatMessage) => void;
  updateMessage: (id: string, updates: Partial<ChatMessage>) => void;
  clearMessages: () => void;
  setConversationId: (id: string) => void;
  setAgentStatus: (status: MessageStatus) => void;
  setStreaming: (v: boolean) => void;
}

export const useChatStore = create<ChatStore>()((set) => ({
  messages: [],
  conversationId: null,
  agentStatus: "pending",
  isStreaming: false,

  addMessage: (msg) =>
    set((s) => ({ messages: [...s.messages, msg] })),

  updateMessage: (id, updates) =>
    set((s) => ({
      messages: s.messages.map((m) => (m.id === id ? { ...m, ...updates } : m)),
    })),

  clearMessages: () => set({ messages: [], conversationId: null }),

  setConversationId: (id) => set({ conversationId: id }),

  setAgentStatus: (status) => set({ agentStatus: status }),

  setStreaming: (v) => set({ isStreaming: v }),
}));

// ─── Voice Store ──────────────────────────────────────────────────────────────

interface VoiceStore {
  voiceState: VoiceState;
  transcript: string;
  audioLevel: number; // 0–1

  setVoiceState: (s: VoiceState) => void;
  setTranscript: (t: string) => void;
  setAudioLevel: (l: number) => void;
}

export const useVoiceStore = create<VoiceStore>()((set) => ({
  voiceState: "idle",
  transcript: "",
  audioLevel: 0,

  setVoiceState: (s) => set({ voiceState: s }),
  setTranscript: (t) => set({ transcript: t }),
  setAudioLevel: (l) => set({ audioLevel: l }),
}));

// ─── Activity Store ───────────────────────────────────────────────────────────

interface ActivityStore {
  entries: ActivityEntry[];
  addEntry: (entry: ActivityEntry) => void;
  clearEntries: () => void;
}

export const useActivityStore = create<ActivityStore>()(
  persist(
    (set) => ({
      entries: [],
      addEntry: (entry) =>
        set((s) => ({
          // Keep last 500 entries
          entries: [entry, ...s.entries].slice(0, 500),
        })),
      clearEntries: () => set({ entries: [] }),
    }),
    {
      name: "aura-activity",
      storage: createJSONStorage(() => localStorage),
    }
  )
);

// ─── Task Store ───────────────────────────────────────────────────────────────

interface TaskStore {
  tasks: Task[];
  addTask: (task: Task) => void;
  updateTask: (id: string, updates: Partial<Task>) => void;
  deleteTask: (id: string) => void;
}

export const useTaskStore = create<TaskStore>()(
  persist(
    (set) => ({
      tasks: [],
      addTask: (task) => set((s) => ({ tasks: [...s.tasks, task] })),
      updateTask: (id, updates) =>
        set((s) => ({
          tasks: s.tasks.map((t) => (t.id === id ? { ...t, ...updates } : t)),
        })),
      deleteTask: (id) =>
        set((s) => ({ tasks: s.tasks.filter((t) => t.id !== id) })),
    }),
    {
      name: "aura-tasks",
      storage: createJSONStorage(() => localStorage),
    }
  )
);

// ─── System Store ─────────────────────────────────────────────────────────────

interface SystemStore {
  systemInfo: SystemInfo | null;
  networkStatus: NetworkStatus | null;
  backendConnected: boolean;
  backendVersion: string | null;

  setSystemInfo: (info: SystemInfo) => void;
  setNetworkStatus: (status: NetworkStatus) => void;
  setBackendConnected: (v: boolean) => void;
  setBackendVersion: (v: string) => void;
}

export const useSystemStore = create<SystemStore>()((set) => ({
  systemInfo: null,
  networkStatus: null,
  backendConnected: false,
  backendVersion: null,

  setSystemInfo: (info) => set({ systemInfo: info }),
  setNetworkStatus: (status) => set({ networkStatus: status }),
  setBackendConnected: (v) => set({ backendConnected: v }),
  setBackendVersion: (v) => set({ backendVersion: v }),
}));

// ─── Settings Store ───────────────────────────────────────────────────────────

interface SettingsStore {
  settings: AuraSettings;
  updateSettings: (updates: Partial<AuraSettings>) => void;
  resetSettings: () => void;
}

export const useSettingsStore = create<SettingsStore>()(
  persist(
    (set) => ({
      settings: DEFAULT_SETTINGS,
      updateSettings: (updates) =>
        set((s) => ({ settings: { ...s.settings, ...updates } })),
      resetSettings: () => set({ settings: DEFAULT_SETTINGS }),
    }),
    {
      name: "aura-settings",
      storage: createJSONStorage(() => localStorage),
    }
  )
);

// ─── Confirmation Store ───────────────────────────────────────────────────────

interface ConfirmationStore {
  pending: ConfirmationRequest | null;
  setPending: (req: ConfirmationRequest | null) => void;
}

export const useConfirmationStore = create<ConfirmationStore>()((set) => ({
  pending: null,
  setPending: (req) => set({ pending: req }),
}));

// ─── WebSocket / Agent Event Store ───────────────────────────────────────────

interface AgentEventStore {
  lastEvent: AgentEvent | null;
  pushEvent: (event: AgentEvent) => void;
}

export const useAgentEventStore = create<AgentEventStore>()((set) => ({
  lastEvent: null,
  pushEvent: (event) => set({ lastEvent: event }),
}));
