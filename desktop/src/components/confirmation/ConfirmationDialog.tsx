import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Shield, ShieldAlert, Skull } from "lucide-react";
import { useConfirmationStore } from "@/store";
import { cn } from "@/utils/cn";
import type { RiskLevel } from "@/types";

const RISK_CONFIG: Record<
  RiskLevel,
  { icon: React.ReactNode; color: string; bgColor: string; label: string }
> = {
  low: {
    icon: <Shield size={18} />,
    color: "text-emerald-400",
    bgColor: "bg-emerald-500/10 border-emerald-500/20",
    label: "Low Risk",
  },
  medium: {
    icon: <AlertTriangle size={18} />,
    color: "text-amber-400",
    bgColor: "bg-amber-500/10 border-amber-500/20",
    label: "Medium Risk",
  },
  high: {
    icon: <ShieldAlert size={18} />,
    color: "text-red-400",
    bgColor: "bg-red-500/10 border-red-500/20",
    label: "High Risk",
  },
  critical: {
    icon: <Skull size={18} />,
    color: "text-red-300",
    bgColor: "bg-red-800/20 border-red-700/30",
    label: "Critical",
  },
};

interface Props {
  onConfirm: (confirmationId: string) => void;
  onCancel: (confirmationId: string) => void;
}

export default function ConfirmationDialog({ onConfirm, onCancel }: Props) {
  const { pending } = useConfirmationStore();

  return (
    <AnimatePresence>
      {pending && (
        <>
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0 bg-black/60 backdrop-blur-sm z-40"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />

          {/* Dialog */}
          <motion.div
            className="absolute inset-x-4 bottom-20 z-50"
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 10, scale: 0.95 }}
            transition={{ type: "spring", stiffness: 400, damping: 30 }}
          >
            <div className="glass-card p-4 rounded-2xl">
              {/* Header */}
              <div className="flex items-center gap-2 mb-3">
                {(() => {
                  const cfg = RISK_CONFIG[pending.risk_level];
                  return (
                    <>
                      <span className={cn("flex-shrink-0", cfg.color)}>
                        {cfg.icon}
                      </span>
                      <div>
                        <p className="text-sm font-semibold text-white">
                          Confirm Action
                        </p>
                        <span
                          className={cn(
                            "text-[10px] font-medium px-2 py-0.5 rounded-full border",
                            cfg.bgColor,
                            cfg.color
                          )}
                        >
                          {cfg.label}
                        </span>
                      </div>
                    </>
                  );
                })()}
              </div>

              {/* Action details */}
              <div className="space-y-2 mb-4">
                <div className="bg-white/5 rounded-xl p-3 space-y-1.5">
                  <Row label="Action" value={pending.action} />
                  <Row label="Target" value={pending.target} mono />
                </div>

                <p className="text-xs text-white/50 px-1">
                  {pending.description}
                </p>

                {pending.consequences.length > 0 && (
                  <ul className="space-y-0.5 px-1">
                    {pending.consequences.map((c, i) => (
                      <li key={i} className="text-xs text-white/40 flex items-start gap-1.5">
                        <span className="text-white/20 mt-0.5">•</span>
                        {c}
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Buttons */}
              <div className="flex gap-2">
                <button
                  onClick={() => onCancel(pending.id)}
                  className="flex-1 py-2.5 rounded-xl bg-white/5 hover:bg-white/10
                             text-white/60 hover:text-white text-sm font-medium
                             transition-all duration-150 border border-white/10"
                >
                  Cancel
                </button>
                <button
                  onClick={() => onConfirm(pending.id)}
                  className={cn(
                    "flex-1 py-2.5 rounded-xl text-sm font-medium transition-all duration-150",
                    pending.risk_level === "critical"
                      ? "bg-red-600 hover:bg-red-500 text-white"
                      : pending.risk_level === "high"
                      ? "bg-red-500/80 hover:bg-red-500 text-white"
                      : "bg-aura-600 hover:bg-aura-500 text-white"
                  )}
                >
                  {pending.risk_level === "critical" ? "⚠ Confirm" : "Confirm"}
                </button>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

function Row({ label, value, mono }: { label: string; value: string; mono?: boolean }) {
  return (
    <div className="flex items-start gap-2">
      <span className="text-[10px] text-white/30 w-12 flex-shrink-0 pt-0.5 uppercase">
        {label}
      </span>
      <span
        className={cn(
          "text-xs text-white/80 break-all",
          mono && "font-mono text-[11px] text-aura-300"
        )}
      >
        {value}
      </span>
    </div>
  );
}
