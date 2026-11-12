import { useEffect, useRef } from "react";
import { AnimatePresence } from "framer-motion";
import { useChatStore } from "@/store";
import ChatMessage from "./ChatMessage";
import { Sparkles } from "lucide-react";

interface Props {
  className?: string;
}

export default function ChatWindow({ className }: Props) {
  const { messages } = useChatStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className={`flex flex-col items-center justify-center gap-3 opacity-30 ${className}`}>
        <Sparkles size={20} className="text-aura-400" />
        <p className="text-xs text-white/40 text-center px-8">
          Type a command or tap the mic to get started
        </p>
      </div>
    );
  }

  return (
    <div
      className={`flex flex-col gap-3 overflow-y-auto px-4 py-3 ${className}`}
      style={{ scrollbarGutter: "stable" }}
    >
      <AnimatePresence initial={false}>
        {messages.map((msg, i) => (
          <ChatMessage
            key={msg.id}
            message={msg}
            isLast={i === messages.length - 1}
          />
        ))}
      </AnimatePresence>
      <div ref={bottomRef} />
    </div>
  );
}
