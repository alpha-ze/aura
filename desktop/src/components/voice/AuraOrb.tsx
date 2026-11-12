import { motion } from "framer-motion";
import { useVoiceStore, useChatStore } from "@/store";
import { cn } from "@/utils/cn";
import type { VoiceState } from "@/types";

// SVG path for the AURA logo mark (stylized A)
function AuraLogoMark() {
  return (
    <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
      <path
        d="M16 4L28 26H4L16 4Z"
        stroke="rgba(255,255,255,0.9)"
        strokeWidth="2"
        strokeLinejoin="round"
        fill="none"
      />
      <path
        d="M10 20H22"
        stroke="rgba(255,255,255,0.6)"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

// Animated wave bars for listening/speaking state
function VoiceWave({ audioLevel }: { audioLevel: number }) {
  const heights = [0.4, 0.7, 1.0, 0.7, 0.4];
  return (
    <div className="flex items-center gap-[3px] h-6">
      {heights.map((base, i) => (
        <motion.span
          key={i}
          className="block w-[3px] rounded-full bg-white/80"
          animate={{
            scaleY: [base, base + audioLevel * 0.6, base],
            opacity: [0.6, 1, 0.6],
          }}
          transition={{
            duration: 0.8,
            delay: i * 0.1,
            repeat: Infinity,
            ease: "easeInOut",
          }}
          style={{ height: "20px", transformOrigin: "center" }}
        />
      ))}
    </div>
  );
}

// Pulsing ring for thinking
function ThinkingRing() {
  return (
    <>
      {[1, 2, 3].map((i) => (
        <motion.div
          key={i}
          className="absolute inset-0 rounded-full border border-aura-400/30"
          animate={{ scale: [1, 1.5 + i * 0.2], opacity: [0.5, 0] }}
          transition={{
            duration: 2,
            delay: i * 0.4,
            repeat: Infinity,
            ease: "easeOut",
          }}
        />
      ))}
    </>
  );
}

const STATE_LABELS: Record<VoiceState, string> = {
  idle: "How can I help you?",
  listening: "Listening...",
  processing: "Processing...",
  thinking: "Thinking...",
  speaking: "Speaking...",
  error: "Something went wrong",
};

export default function AuraOrb({ onClick }: { onClick?: () => void }) {
  const { voiceState, audioLevel } = useVoiceStore();
  const { agentStatus } = useChatStore();

  const isListening = voiceState === "listening";
  const isSpeaking = voiceState === "speaking";
  const isThinking = voiceState === "thinking" || agentStatus === "thinking" || agentStatus === "planning";
  const isExecuting = agentStatus === "executing";

  const orbClass = cn(
    "aura-orb cursor-pointer transition-all duration-300",
    isListening && "listening",
    isSpeaking && "speaking",
    (isThinking || isExecuting) && "thinking"
  );

  return (
    <div className="flex flex-col items-center gap-3">
      {/* Outer glow rings */}
      <div className="relative flex items-center justify-center">
        {isThinking && <ThinkingRing />}

        <motion.div
          className={orbClass}
          onClick={onClick}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          animate={
            isListening
              ? { scale: [1, 1.03, 1] }
              : isExecuting
              ? { rotate: [0, 360] }
              : { scale: 1 }
          }
          transition={
            isExecuting
              ? { duration: 3, repeat: Infinity, ease: "linear" }
              : isListening
              ? { duration: 1.5, repeat: Infinity, ease: "easeInOut" }
              : { duration: 0.3 }
          }
        >
          {isListening || isSpeaking ? (
            <VoiceWave audioLevel={audioLevel} />
          ) : (
            <AuraLogoMark />
          )}
        </motion.div>
      </div>

      {/* State label */}
      <motion.p
        key={voiceState}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-sm text-white/50 font-light"
      >
        {STATE_LABELS[voiceState]}
      </motion.p>
    </div>
  );
}
