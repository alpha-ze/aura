import { motion } from "framer-motion";
import {
  FolderOpen, Settings, AppWindow,
  AlertCircle, Info, CheckCircle, FileText,
} from "lucide-react";
import { useActivityStore } from "@/store";
import { timeAgo } from "@/utils/format";
import type { ActivityEntry, ActivityType } from "@/types";

const ACTIVITY_ICONS: Record<ActivityType, React.ReactNode> = {
  command:       <FileText size={12} />,
  tool_executed: <CheckCircle size={12} />,
  file_changed:  <FolderOpen size={12} />,
  app_launched:  <AppWindow size={12} />,
  setting_changed: <Settings size={12} />,
  error:         <AlertCircle size={12} />,
  info:          <Info size={12} />,
};

const ACTIVITY_COLORS: Record<ActivityType, string> = {
  command:       "text-aura-400",
  tool_executed: "text-emerald-400",
  file_changed:  "text-blue-400",
  app_launched:  "text-violet-400",
  setting_changed: "text-amber-400",
  error:         "text-red-400",
  info:          "text-white/40",
};

function ActivityItem({ entry }: { entry: ActivityEntry }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -6 }}
      animate={{ opacity: 1, x: 0 }}
      className="flex items-start gap-2.5 py-2 border-b border-white/5 last:border-0"
    >
      <span
        className={`mt-0.5 flex-shrink-0 ${ACTIVITY_COLORS[entry.type]}`}
      >
        {ACTIVITY_ICONS[entry.type]}
      </span>

      <div className="flex-1 min-w-0">
        <p className="text-xs text-white/70 truncate">{entry.summary}</p>
        {entry.detail && (
          <p className="text-[10px] text-white/30 truncate mt-0.5">{entry.detail}</p>
        )}
      </div>

      <span className="text-[10px] text-white/20 flex-shrink-0 mt-0.5">
        {timeAgo(entry.timestamp)}
      </span>
    </motion.div>
  );
}

interface Props {
  maxItems?: number;
  className?: string;
}

export default function ActivityPanel({ maxItems = 5, className }: Props) {
  const { entries } = useActivityStore();
  const recent = entries.slice(0, maxItems);

  if (recent.length === 0) return null;

  return (
    <div className={`px-4 pb-2 ${className}`}>
      <p className="text-[10px] font-semibold text-white/20 uppercase tracking-widest mb-1">
        Recent
      </p>
      <div className="glass rounded-xl px-3 py-1 divide-y divide-white/5">
        {recent.map((entry) => (
          <ActivityItem key={entry.id} entry={entry} />
        ))}
      </div>
    </div>
  );
}
