import { motion, AnimatePresence } from "framer-motion";
import { useSystemStore, useChatStore } from "@/store";
import { cn } from "@/utils/cn";
import type { MessageStatus } from "@/types";

const STATUS_LABELS: Record<MessageStatus, string> = {
  pending: "",
  thinking: "Thinking...",
  planning: "Planning...",
  executing: "Executing...",
  waiting_confirmation: "Waiting for confirmation",
  completed: "Done",
  error: "Error",
};

const STATUS_COLORS: Record<MessageStatus, string> = {
  pending: "bg-white/10",
  thinking: "bg-aura-500",
  planning: "bg-violet-500",
  executing: "bg-amber-500",
  waiting_confirmation: "bg-orange-500",
  completed: "bg-emerald-500",
  error: "bg-red-500",
};

export default function StatusIndicator() {
  const { backendConnected } = useSystemStore();
  const { agentStatus } = useChatStore();

  const label = STATUS_LABELS[agentStatus];
  const isActive = agentStatus !== "pending" && agentStatus !== "completed";

  return (
    <div className="flex items-center gap-2">
      {/* Backend connection dot */}
      <div
        title={backendConnected ? "Backend connected" : "Backend disconnected"}
        className={cn(
          "w-2 h-2 rounded-full transition-colors duration-500",
          backendConnected ? "bg-emerald-500" : "bg-red-500/70"
        )}
      />

      {/* Agent status */}
      <AnimatePresence mode="wait">
        {label && (
          <motion.div
            key={agentStatus}
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
            transition={{ duration: 0.15 }}
            className="flex items-center gap-1.5"
          >
            <span
              className={cn(
                "w-1.5 h-1.5 rounded-full",
                STATUS_COLORS[agentStatus],
                isActive && "animate-pulse"
              )}
            />
            <span className="text-xs text-white/40">{label}</span>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
