import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, CheckCircle, Cpu, Mic, Shield, Eye } from "lucide-react";
import { useSettingsStore } from "@/store";
import { cn } from "@/utils/cn";
import type { AIProvider, PermissionMode } from "@/types";

// ── Step definitions ──────────────────────────────────────────────────────────
const TOTAL_STEPS = 5;

function ProgressBar({ step }: { step: number }) {
  return (
    <div className="flex gap-1.5 px-8">
      {Array.from({ length: TOTAL_STEPS }).map((_, i) => (
        <div
          key={i}
          className={cn(
            "h-1 flex-1 rounded-full transition-all duration-500",
            i < step ? "bg-aura-500" : i === step ? "bg-aura-500/50" : "bg-white/10"
          )}
        />
      ))}
    </div>
  );
}

// ── Step 0: Welcome ───────────────────────────────────────────────────────────
function WelcomeStep({ onNext }: { onNext: () => void }) {
  return (
    <div className="flex flex-col items-center gap-6 px-8">
      <div className="w-24 h-24 rounded-full flex items-center justify-center"
           style={{ background: "radial-gradient(circle at 40% 35%, #8097fc, #6272f8 40%, #4044d4)", boxShadow: "0 0 60px rgba(98,114,248,0.5)" }}>
        <svg width="40" height="40" viewBox="0 0 32 32" fill="none">
          <path d="M16 4L28 26H4L16 4Z" stroke="white" strokeWidth="2" strokeLinejoin="round" fill="none"/>
          <path d="M10 20H22" stroke="rgba(255,255,255,0.6)" strokeWidth="1.5" strokeLinecap="round"/>
        </svg>
      </div>
      <div className="text-center">
        <h1 className="text-2xl font-bold text-white mb-2">Welcome to AURA</h1>
        <p className="text-sm text-white/50 leading-relaxed">
          Your personal AI assistant for Windows.<br />
          Control your computer with natural language and voice.
        </p>
      </div>
      <button
        onClick={onNext}
        className="w-full py-3 rounded-2xl bg-aura-600 hover:bg-aura-500
                   text-white font-medium transition-all flex items-center justify-center gap-2"
      >
        Get Started <ChevronRight size={16} />
      </button>
    </div>
  );
}

// ── Step 1: AI Provider ───────────────────────────────────────────────────────
function ProviderStep({
  onNext,
  value,
  onChange,
}: {
  onNext: () => void;
  value: AIProvider;
  onChange: (v: AIProvider) => void;
}) {
  const providers: { id: AIProvider; name: string; desc: string }[] = [
    { id: "groq",      name: "Groq",      desc: "Qwen 3.8-27B, Llama 3 — ultra-fast cloud inference" },
    { id: "openai",    name: "OpenAI",    desc: "GPT-4o, GPT-4 Turbo — cloud" },
    { id: "anthropic", name: "Anthropic", desc: "Claude 3.5 Sonnet — cloud" },
    { id: "gemini",    name: "Google Gemini", desc: "Gemini 1.5 Pro — cloud" },
    { id: "ollama",    name: "Ollama",    desc: "Llama, Mistral — fully local" },
  ];

  return (
    <div className="flex flex-col gap-4 px-6">
      <div className="flex items-center gap-2">
        <Cpu size={18} className="text-aura-400" />
        <h2 className="text-base font-semibold text-white">Choose AI Provider</h2>
      </div>
      <p className="text-xs text-white/40">
        AURA works with multiple AI providers. You can change this later in Settings.
      </p>
      <div className="space-y-2">
        {providers.map((p) => (
          <button
            key={p.id}
            onClick={() => onChange(p.id)}
            className={cn(
              "w-full flex items-center justify-between px-4 py-3 rounded-xl border transition-all",
              value === p.id
                ? "bg-aura-600/20 border-aura-500/60 text-white"
                : "bg-white/5 border-white/10 text-white/60 hover:bg-white/8 hover:text-white/80"
            )}
          >
            <div className="text-left">
              <p className="text-sm font-medium">{p.name}</p>
              <p className="text-xs opacity-60 mt-0.5">{p.desc}</p>
            </div>
            {value === p.id && <CheckCircle size={16} className="text-aura-400" />}
          </button>
        ))}
      </div>
      <button
        onClick={onNext}
        className="w-full py-3 rounded-2xl bg-aura-600 hover:bg-aura-500
                   text-white font-medium transition-all flex items-center justify-center gap-2"
      >
        Continue <ChevronRight size={16} />
      </button>
    </div>
  );
}

// ── Step 2: Microphone ────────────────────────────────────────────────────────
function MicrophoneStep({ onNext }: { onNext: () => void }) {
  return (
    <div className="flex flex-col gap-4 px-6">
      <div className="flex items-center gap-2">
        <Mic size={18} className="text-aura-400" />
        <h2 className="text-base font-semibold text-white">Voice Setup</h2>
      </div>
      <p className="text-xs text-white/40 leading-relaxed">
        AURA can listen to your voice using your microphone. Voice input is optional — you can always type instead.
      </p>
      <div className="glass rounded-2xl p-4 space-y-2">
        <p className="text-xs text-white/60">Voice features:</p>
        {[
          "Push-to-talk with the microphone button",
          "Voice activity detection",
          "Speech-to-text via Whisper (local)",
          "Text-to-speech responses",
        ].map((f) => (
          <div key={f} className="flex items-center gap-2">
            <CheckCircle size={12} className="text-emerald-400 flex-shrink-0" />
            <p className="text-xs text-white/50">{f}</p>
          </div>
        ))}
      </div>
      <p className="text-[10px] text-white/30 px-1">
        Your microphone is only activated when you explicitly press the mic button. Audio is processed locally by default.
      </p>
      <button
        onClick={onNext}
        className="w-full py-3 rounded-2xl bg-aura-600 hover:bg-aura-500
                   text-white font-medium transition-all flex items-center justify-center gap-2"
      >
        Continue <ChevronRight size={16} />
      </button>
    </div>
  );
}

// ── Step 3: Permission Mode ───────────────────────────────────────────────────
function PermissionStep({
  onNext,
  value,
  onChange,
}: {
  onNext: () => void;
  value: PermissionMode;
  onChange: (v: PermissionMode) => void;
}) {
  const modes: { id: PermissionMode; name: string; desc: string; recommended?: boolean }[] = [
    { id: "safe", name: "Safe", desc: "Ask before almost every action. Best for new users." },
    { id: "balanced", name: "Balanced", desc: "Auto-execute safe actions, confirm risky ones.", recommended: true },
    { id: "power_user", name: "Power User", desc: "Maximum automation. Still confirms destructive actions." },
  ];

  return (
    <div className="flex flex-col gap-4 px-6">
      <div className="flex items-center gap-2">
        <Shield size={18} className="text-aura-400" />
        <h2 className="text-base font-semibold text-white">Permission Mode</h2>
      </div>
      <p className="text-xs text-white/40">
        How should AURA handle actions on your computer?
      </p>
      <div className="space-y-2">
        {modes.map((m) => (
          <button
            key={m.id}
            onClick={() => onChange(m.id)}
            className={cn(
              "w-full text-left px-4 py-3 rounded-xl border transition-all",
              value === m.id
                ? "bg-aura-600/20 border-aura-500/60"
                : "bg-white/5 border-white/10 hover:bg-white/8"
            )}
          >
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-white">
                {m.name}
                {m.recommended && (
                  <span className="ml-2 text-[10px] bg-aura-500/30 text-aura-300 px-2 py-0.5 rounded-full">
                    Recommended
                  </span>
                )}
              </p>
              {value === m.id && <CheckCircle size={14} className="text-aura-400" />}
            </div>
            <p className="text-xs text-white/40 mt-0.5">{m.desc}</p>
          </button>
        ))}
      </div>
      <button
        onClick={onNext}
        className="w-full py-3 rounded-2xl bg-aura-600 hover:bg-aura-500
                   text-white font-medium transition-all flex items-center justify-center gap-2"
      >
        Continue <ChevronRight size={16} />
      </button>
    </div>
  );
}

// ── Step 4: Privacy ───────────────────────────────────────────────────────────
function PrivacyStep({ onFinish }: { onFinish: () => void }) {
  return (
    <div className="flex flex-col gap-4 px-6">
      <div className="flex items-center gap-2">
        <Eye size={18} className="text-aura-400" />
        <h2 className="text-base font-semibold text-white">Privacy First</h2>
      </div>
      <div className="space-y-3">
        {[
          { title: "Local-first", desc: "All file operations run locally. Nothing leaves your machine unless you use a cloud AI." },
          { title: "No telemetry", desc: "AURA collects no usage data, analytics, or crash reports." },
          { title: "Secure storage", desc: "API keys are stored using Windows Credential Manager, never in plain text." },
          { title: "You're in control", desc: "AURA always tells you what it's doing and asks before risky actions." },
        ].map((item) => (
          <div key={item.title} className="glass rounded-xl p-3">
            <p className="text-xs font-semibold text-white/80 mb-0.5">{item.title}</p>
            <p className="text-xs text-white/40 leading-relaxed">{item.desc}</p>
          </div>
        ))}
      </div>
      <button
        onClick={onFinish}
        className="w-full py-3 rounded-2xl bg-aura-600 hover:bg-aura-500
                   text-white font-semibold transition-all flex items-center justify-center gap-2"
      >
        <CheckCircle size={16} />
        Start using AURA
      </button>
    </div>
  );
}

// ── Main Onboarding Page ──────────────────────────────────────────────────────
export default function OnboardingPage() {
  const navigate = useNavigate();
  const { settings, updateSettings } = useSettingsStore();
  const [step, setStep] = useState(0);

  const next = () => setStep((s) => Math.min(s + 1, TOTAL_STEPS - 1));

  const finish = () => {
    updateSettings({ first_run_complete: true });
    navigate("/");
  };

  const steps = [
    <WelcomeStep onNext={next} />,
    <ProviderStep onNext={next} value={settings.ai_provider} onChange={(v) => updateSettings({ ai_provider: v })} />,
    <MicrophoneStep onNext={next} />,
    <PermissionStep onNext={next} value={settings.permission_mode} onChange={(v) => updateSettings({ permission_mode: v })} />,
    <PrivacyStep onFinish={finish} />,
  ];

  return (
    <div className="flex flex-col h-full bg-[#0f0f1a] pt-8">
      {/* Progress */}
      <ProgressBar step={step} />

      {/* Step content */}
      <div className="flex-1 flex flex-col justify-center py-8 overflow-y-auto">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.25 }}
          >
            {steps[step]}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Step counter */}
      <p className="text-center text-[10px] text-white/20 pb-4">
        {step + 1} of {TOTAL_STEPS}
      </p>
    </div>
  );
}
