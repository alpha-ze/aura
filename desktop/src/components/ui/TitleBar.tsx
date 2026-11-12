import { Minus, Square, X } from "lucide-react";
import { cn } from "@/utils/cn";

/** True when running inside a real Tauri window (not a plain browser). */
const IS_TAURI = typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;

async function tauriMinimize() {
  if (!IS_TAURI) return;
  const { getCurrentWindow } = await import("@tauri-apps/api/window");
  getCurrentWindow().minimize();
}

async function tauriMaximize() {
  if (!IS_TAURI) return;
  const { getCurrentWindow } = await import("@tauri-apps/api/window");
  getCurrentWindow().toggleMaximize();
}

async function tauriHide() {
  if (!IS_TAURI) return;
  const { getCurrentWindow } = await import("@tauri-apps/api/window");
  getCurrentWindow().hide();
}

interface TitleBarProps {
  title?: string;
  onBack?: () => void;
  showBack?: boolean;
}

export default function TitleBar({ title = "AURA", showBack, onBack }: TitleBarProps) {
  return (
    <div
      className={cn(
        "flex items-center justify-between px-4 h-10 flex-shrink-0",
        "bg-[#0a0a14] border-b border-white/5 select-none",
        IS_TAURI && "drag-region"
      )}
    >
      {/* Left */}
      <div className={cn("flex items-center gap-2 w-24", IS_TAURI && "no-drag")}>
        {showBack ? (
          <button
            onClick={onBack}
            className="text-white/40 hover:text-white/80 transition-colors text-sm"
          >
            ← Back
          </button>
        ) : (
          <span className="text-xs font-semibold tracking-widest text-aura-400 uppercase">
            {title}
          </span>
        )}
      </div>

      {/* Centre: pulse dot */}
      <div className="flex items-center gap-1.5">
        <span className="w-1.5 h-1.5 rounded-full bg-aura-500 animate-pulse" />
      </div>

      {/* Right: window controls — only shown inside Tauri */}
      <div className={cn("flex items-center gap-1 w-24 justify-end", IS_TAURI && "no-drag")}>
        {IS_TAURI ? (
          <>
            <WindowBtn onClick={tauriMinimize} title="Minimize"><Minus size={12} /></WindowBtn>
            <WindowBtn onClick={tauriMaximize} title="Maximize"><Square size={11} /></WindowBtn>
            <WindowBtn onClick={tauriHide}     title="Close to tray" danger><X size={12} /></WindowBtn>
          </>
        ) : (
          /* Browser mode: show a subtle "browser mode" badge instead */
          <span className="text-[9px] text-white/15 tracking-wider uppercase">browser</span>
        )}
      </div>
    </div>
  );
}

function WindowBtn({
  children, onClick, title, danger,
}: {
  children: React.ReactNode;
  onClick: () => void;
  title: string;
  danger?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className={cn(
        "w-7 h-7 rounded-lg flex items-center justify-center",
        "text-white/30 transition-all duration-150",
        danger
          ? "hover:bg-red-500/20 hover:text-red-400"
          : "hover:bg-white/10 hover:text-white/80"
      )}
    >
      {children}
    </button>
  );
}
