import { motion } from "framer-motion";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { CheckCircle, XCircle, Loader2, ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { cn } from "@/utils/cn";
import { formatTime } from "@/utils/format";
import type { ChatMessage as ChatMessageType, PlanStep } from "@/types";

// ── Plan step display ─────────────────────────────────────────────────────────
function PlanStepItem({ step }: { step: PlanStep }) {
  const icon = {
    pending: <span className="w-4 h-4 rounded-full border border-white/20 flex-shrink-0" />,
    in_progress: <Loader2 size={14} className="text-aura-400 animate-spin flex-shrink-0" />,
    completed: <CheckCircle size={14} className="text-emerald-400 flex-shrink-0" />,
    failed: <XCircle size={14} className="text-red-400 flex-shrink-0" />,
    skipped: <span className="w-4 h-4 rounded-full border border-white/10 flex-shrink-0 opacity-40" />,
  }[step.status];

  return (
    <div className="flex items-start gap-2 py-1">
      <div className="mt-0.5">{icon}</div>
      <div className="flex-1 min-w-0">
        <p
          className={cn(
            "text-xs",
            step.status === "completed" ? "text-white/50 line-through" : "text-white/70",
            step.status === "in_progress" && "text-white/90 font-medium",
            step.status === "failed" && "text-red-400/80"
          )}
        >
          {step.description}
        </p>
        {step.result && step.status === "completed" && (
          <p className="text-xs text-white/30 mt-0.5 truncate">{step.result}</p>
        )}
        {step.error && (
          <p className="text-xs text-red-400/60 mt-0.5">{step.error}</p>
        )}
      </div>
    </div>
  );
}

// ── Plan collapsible panel ────────────────────────────────────────────────────
function AgentPlanPanel({ msg }: { msg: ChatMessageType }) {
  const [expanded, setExpanded] = useState(false);
  if (!msg.plan) return null;

  const completedCount = msg.plan.steps.filter((s) => s.status === "completed").length;
  const totalCount = msg.plan.steps.length;

  return (
    <div className="mt-2 border border-white/10 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded((v) => !v)}
        className="w-full flex items-center justify-between px-3 py-2 bg-white/5 hover:bg-white/8 transition-colors"
      >
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-white/60">
            Agent Plan
          </span>
          <span className="text-xs text-white/30">
            {completedCount}/{totalCount} steps
          </span>
        </div>
        {expanded ? (
          <ChevronUp size={14} className="text-white/30" />
        ) : (
          <ChevronDown size={14} className="text-white/30" />
        )}
      </button>

      {expanded && (
        <div className="px-3 py-2 space-y-0.5">
          {msg.plan.steps.map((step) => (
            <PlanStepItem key={step.id} step={step} />
          ))}
        </div>
      )}
    </div>
  );
}

// ── Main message component ────────────────────────────────────────────────────
interface Props {
  message: ChatMessageType;
  isLast?: boolean;
}

export default function ChatMessage({ message, isLast }: Props) {
  const isUser = message.role === "user";
  const isAssistant = message.role === "assistant";

  if (!isUser && !isAssistant) return null;

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className={cn(
        "flex flex-col",
        isUser ? "items-end" : "items-start",
        isLast && "mb-2"
      )}
    >
      {isUser ? (
        <div className="message-user selectable">
          {message.content}
        </div>
      ) : (
        <div className="message-assistant selectable">
          {message.status === "thinking" && (
            <div className="flex items-center gap-2 text-white/40">
              <Loader2 size={14} className="animate-spin" />
              <span className="text-xs">Thinking...</span>
            </div>
          )}

          {message.status === "planning" && (
            <div className="flex items-center gap-2 text-white/40">
              <Loader2 size={14} className="animate-spin" />
              <span className="text-xs">Planning steps...</span>
            </div>
          )}

          {message.status === "executing" && (
            <div className="flex items-center gap-2 text-white/40">
              <Loader2 size={14} className="animate-spin" />
              <span className="text-xs">Executing...</span>
            </div>
          )}

          {message.content && (
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code: ({ children, ...props }) => (
                  <code
                    className="bg-white/10 rounded px-1 py-0.5 text-xs font-mono"
                    {...props}
                  >
                    {children}
                  </code>
                ),
                pre: ({ children }) => (
                  <pre className="bg-white/5 rounded-lg p-3 overflow-x-auto text-xs my-2">
                    {children}
                  </pre>
                ),
                ul: ({ children }) => (
                  <ul className="list-disc list-inside space-y-1 my-1">{children}</ul>
                ),
                ol: ({ children }) => (
                  <ol className="list-decimal list-inside space-y-1 my-1">{children}</ol>
                ),
                li: ({ children }) => (
                  <li className="text-white/80">{children}</li>
                ),
                p: ({ children }) => (
                  <p className="mb-1 last:mb-0">{children}</p>
                ),
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}

          {/* Agent plan steps */}
          {message.plan && <AgentPlanPanel msg={message} />}
        </div>
      )}

      <span className="text-[10px] text-white/20 mt-1 px-1">
        {formatTime(message.timestamp)}
      </span>
    </motion.div>
  );
}
