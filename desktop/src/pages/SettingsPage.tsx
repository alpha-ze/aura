import { useNavigate } from "react-router-dom";
import { useState } from "react";
import { Eye, EyeOff, Settings, Save } from "lucide-react";
import TitleBar from "@/components/ui/TitleBar";
import { useSettingsStore } from "@/store";
import { cn } from "@/utils/cn";
import type { AIProvider, PermissionMode, Theme } from "@/types";
import toast from "react-hot-toast";

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mb-5">
      <p className="text-[10px] font-semibold text-white/20 uppercase tracking-widest mb-2 px-1">
        {title}
      </p>
      <div className="glass rounded-2xl divide-y divide-white/5">{children}</div>
    </div>
  );
}

function Row({
  label,
  description,
  children,
}: {
  label: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-center justify-between px-4 py-3 gap-3">
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white/80">{label}</p>
        {description && (
          <p className="text-xs text-white/30 mt-0.5">{description}</p>
        )}
      </div>
      <div className="flex-shrink-0">{children}</div>
    </div>
  );
}

function Toggle({
  value,
  onChange,
}: {
  value: boolean;
  onChange: (v: boolean) => void;
}) {
  return (
    <button
      onClick={() => onChange(!value)}
      className={cn(
        "w-10 h-6 rounded-full transition-all duration-200 relative",
        value ? "bg-aura-600" : "bg-white/10"
      )}
    >
      <span
        className={cn(
          "absolute top-1 w-4 h-4 rounded-full bg-white transition-all duration-200",
          value ? "left-5" : "left-1"
        )}
      />
    </button>
  );
}

function Select<T extends string>({
  value,
  options,
  onChange,
}: {
  value: T;
  options: { value: T; label: string }[];
  onChange: (v: T) => void;
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as T)}
      className="bg-white/5 border border-white/10 text-white text-xs rounded-xl px-3 py-2
                 focus:outline-none focus:border-aura-500/50 transition-colors"
    >
      {options.map((opt) => (
        <option key={opt.value} value={opt.value} className="bg-[#1a1a2e]">
          {opt.label}
        </option>
      ))}
    </select>
  );
}

function ApiKeyInput({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [show, setShow] = useState(false);
  return (
    <div className="flex items-center gap-1">
      <input
        type={show ? "text" : "password"}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="sk-..."
        className="bg-white/5 border border-white/10 text-white text-xs rounded-xl px-3 py-2
                   w-40 focus:outline-none focus:border-aura-500/50 placeholder-white/20 transition-colors"
      />
      <button
        onClick={() => setShow((v) => !v)}
        className="p-2 text-white/30 hover:text-white/60 transition-colors"
      >
        {show ? <EyeOff size={13} /> : <Eye size={13} />}
      </button>
    </div>
  );
}

export default function SettingsPage() {
  const navigate = useNavigate();
  const { settings, updateSettings } = useSettingsStore();
  const [apiKey, setApiKey] = useState("");

  const handleSave = () => {
    if (apiKey) {
      // API key is sent to the backend to be stored securely — never stored in localStorage
      fetch("http://127.0.0.1:8765/api/settings/api-key", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider: settings.ai_provider, api_key: apiKey }),
      })
        .then(() => {
          setApiKey("");
          toast.success("API key saved securely");
        })
        .catch(() => toast.error("Failed to save API key"));
    } else {
      toast.success("Settings saved");
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0f0f1a]">
      <TitleBar />

      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
        <Settings size={16} className="text-aura-400" />
        <h1 className="text-sm font-semibold text-white/80">Settings</h1>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-4 py-4">
        {/* AI */}
        <Section title="AI Provider">
          <Row label="Provider">
            <Select<AIProvider>
              value={settings.ai_provider}
              onChange={(v) => updateSettings({ ai_provider: v })}
              options={[
                { value: "groq",      label: "Groq (Fast Inference)" },
                { value: "openai",    label: "OpenAI" },
                { value: "anthropic", label: "Anthropic" },
                { value: "gemini",    label: "Google Gemini" },
                { value: "ollama",    label: "Ollama (Local)" },
              ]}
            />
          </Row>
          <Row label="API Key" description="Stored securely, never logged">
            <ApiKeyInput value={apiKey} onChange={setApiKey} />
          </Row>
          <Row label="Model">
            <input
              value={settings.model}
              onChange={(e) => updateSettings({ model: e.target.value })}
              placeholder="gpt-4o"
              className="bg-white/5 border border-white/10 text-white text-xs rounded-xl px-3 py-2
                         w-32 focus:outline-none focus:border-aura-500/50 placeholder-white/20 transition-colors"
            />
          </Row>
        </Section>

        {/* Permissions */}
        <Section title="Permissions">
          <Row
            label="Permission Mode"
            description="Controls when AURA asks for confirmation"
          >
            <Select<PermissionMode>
              value={settings.permission_mode}
              onChange={(v) => updateSettings({ permission_mode: v })}
              options={[
                { value: "safe", label: "Safe — Ask always" },
                { value: "balanced", label: "Balanced (Recommended)" },
                { value: "power_user", label: "Power User" },
              ]}
            />
          </Row>
          <Row label="Dry Run Default" description="Preview actions before executing">
            <Toggle
              value={settings.dry_run_default}
              onChange={(v) => updateSettings({ dry_run_default: v })}
            />
          </Row>
        </Section>

        {/* Voice */}
        <Section title="Voice">
          <Row label="Enable Voice">
            <Toggle
              value={settings.enable_voice}
              onChange={(v) => updateSettings({ enable_voice: v })}
            />
          </Row>
        </Section>

        {/* Privacy */}
        <Section title="Privacy & Data">
          <Row label="Enable Memory" description="Remember preferences and habits">
            <Toggle
              value={settings.enable_memory}
              onChange={(v) => updateSettings({ enable_memory: v })}
            />
          </Row>
          <Row label="Activity Log" description="Track AURA's actions locally">
            <Toggle
              value={settings.enable_activity_log}
              onChange={(v) => updateSettings({ enable_activity_log: v })}
            />
          </Row>
        </Section>

        {/* Appearance */}
        <Section title="Appearance">
          <Row label="Theme">
            <Select<Theme>
              value={settings.theme}
              onChange={(v) => updateSettings({ theme: v })}
              options={[
                { value: "dark", label: "Dark" },
                { value: "light", label: "Light" },
                { value: "system", label: "System" },
              ]}
            />
          </Row>
        </Section>

        {/* Startup */}
        <Section title="Startup">
          <Row label="Start Minimized" description="Open to system tray on startup">
            <Toggle
              value={settings.start_minimized}
              onChange={(v) => updateSettings({ start_minimized: v })}
            />
          </Row>
        </Section>
      </div>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-white/5 flex gap-2">
        <button
          onClick={() => navigate("/")}
          className="flex-1 py-2.5 rounded-xl bg-white/5 hover:bg-white/10
                     text-sm text-white/50 hover:text-white/80 transition-all border border-white/8"
        >
          ← Back
        </button>
        <button
          onClick={handleSave}
          className="flex-1 py-2.5 rounded-xl bg-aura-600 hover:bg-aura-500
                     text-sm text-white font-medium transition-all flex items-center justify-center gap-2"
        >
          <Save size={14} />
          Save
        </button>
      </div>
    </div>
  );
}
