import { useState, useRef, useCallback } from "react";
import { motion } from "framer-motion";
import { Send, Mic, MicOff, Loader2 } from "lucide-react";
import { cn } from "@/utils/cn";
import { useChatStore, useVoiceStore } from "@/store";

interface Props {
  onSend: (message: string) => void;
  onVoiceToggle?: () => void;
  disabled?: boolean;
}

export default function ChatInput({ onSend, onVoiceToggle, disabled }: Props) {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { agentStatus } = useChatStore();
  const { voiceState } = useVoiceStore();

  const isProcessing =
    agentStatus === "thinking" ||
    agentStatus === "planning" ||
    agentStatus === "executing";

  const isListening = voiceState === "listening";

  const handleSend = useCallback(() => {
    const trimmed = input.trim();
    if (!trimmed || isProcessing || disabled) return;
    onSend(trimmed);
    setInput("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [input, isProcessing, disabled, onSend]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    // Auto-resize textarea
    const ta = e.target;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 120)}px`;
  };

  return (
    <div className="relative flex items-end gap-2 p-3 border-t border-white/5">
      {/* Text area */}
      <div className="flex-1 relative">
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={
            isListening
              ? "Listening..."
              : isProcessing
              ? "AURA is working..."
              : "Ask AURA anything..."
          }
          disabled={disabled || isProcessing}
          rows={1}
          className={cn(
            "chat-input pr-10 selectable",
            "min-h-[44px] max-h-[120px]",
            (disabled || isProcessing) && "opacity-50 cursor-not-allowed"
          )}
        />

        {/* Send button inside input */}
        <motion.button
          onClick={handleSend}
          disabled={!input.trim() || isProcessing || disabled}
          whileTap={{ scale: 0.9 }}
          className={cn(
            "absolute right-3 bottom-3",
            "w-7 h-7 rounded-lg flex items-center justify-center",
            "transition-all duration-200",
            input.trim() && !isProcessing && !disabled
              ? "bg-aura-600 text-white hover:bg-aura-500"
              : "text-white/20 cursor-not-allowed"
          )}
        >
          {isProcessing ? (
            <Loader2 size={14} className="animate-spin" />
          ) : (
            <Send size={14} />
          )}
        </motion.button>
      </div>

      {/* Voice button */}
      <motion.button
        onClick={onVoiceToggle}
        whileTap={{ scale: 0.9 }}
        title={isListening ? "Stop listening" : "Start voice input"}
        className={cn(
          "w-11 h-11 rounded-2xl flex items-center justify-center flex-shrink-0",
          "transition-all duration-200 border",
          isListening
            ? "bg-aura-600/40 border-aura-500/60 text-aura-300 animate-pulse"
            : "bg-white/5 border-white/10 text-white/40 hover:bg-white/10 hover:text-white/70 hover:border-white/20"
        )}
      >
        {isListening ? <MicOff size={18} /> : <Mic size={18} />}
      </motion.button>
    </div>
  );
}
