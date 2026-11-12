import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import { Trash2, Activity } from "lucide-react";
import TitleBar from "@/components/ui/TitleBar";
import { useActivityStore } from "@/store";
import { formatTime, timeAgo } from "@/utils/format";
import type { ActivityEntry } from "@/types";

function EntryRow({ entry }: { entry: ActivityEntry }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-start gap-3 py-3 border-b border-white/5 last:border-0"
    >
      {/* Status dot */}
      <span
        className={`w-2 h-2 mt-1.5 rounded-full flex-shrink-0 ${
          entry.success === false
            ? "bg-red-400"
            : entry.type === "error"
            ? "bg-red-400"
            : "bg-aura-500"
        }`}
      />

      <div className="flex-1 min-w-0">
        <p className="text-sm text-white/80">{entry.summary}</p>
        {entry.detail && (
          <p className="text-xs text-white/30 mt-0.5 font-mono truncate">
            {entry.detail}
          </p>
        )}
        <p className="text-[10px] text-white/20 mt-1">
          {timeAgo(entry.timestamp)} · {formatTime(entry.timestamp)}
        </p>
      </div>

      {entry.risk_level && (
        <span
          className={`text-[10px] px-2 py-0.5 rounded-full border flex-shrink-0 ${
            entry.risk_level === "low"
              ? "risk-low"
              : entry.risk_level === "medium"
              ? "risk-medium"
              : "risk-high"
          }`}
        >
          {entry.risk_level}
        </span>
      )}
    </motion.div>
  );
}

export default function ActivityPage() {
  const navigate = useNavigate();
  const { entries, clearEntries } = useActivityStore();

  return (
    <div className="flex flex-col h-full bg-[#0f0f1a]">
      <TitleBar />

      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/5">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-aura-400" />
          <h1 className="text-sm font-semibold text-white/80">Activity Log</h1>
          <span className="text-xs text-white/20">({entries.length})</span>
        </div>
        {entries.length > 0 && (
          <button
            onClick={clearEntries}
            className="flex items-center gap-1.5 text-xs text-red-400/60 hover:text-red-400
                       transition-colors px-2 py-1 rounded-lg hover:bg-red-500/10"
          >
            <Trash2 size={12} />
            Clear
          </button>
        )}
      </div>

      {/* Entries */}
      <div className="flex-1 overflow-y-auto px-4">
        {entries.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full gap-2 opacity-30">
            <Activity size={24} className="text-white/30" />
            <p className="text-xs text-white/30">No activity yet</p>
          </div>
        ) : (
          <div className="divide-y divide-white/5">
            {entries.map((entry) => (
              <EntryRow key={entry.id} entry={entry} />
            ))}
          </div>
        )}
      </div>

      {/* Back */}
      <div className="px-4 py-3 border-t border-white/5">
        <button
          onClick={() => navigate("/")}
          className="w-full py-2.5 rounded-xl bg-white/5 hover:bg-white/10
                     text-sm text-white/50 hover:text-white/80 transition-all border border-white/8"
        >
          ← Back to AURA
        </button>
      </div>
    </div>
  );
}
