import { useNavigate } from "react-router-dom";
import { Settings, Activity } from "lucide-react";
import TitleBar from "@/components/ui/TitleBar";
import StatusIndicator from "@/components/ui/StatusIndicator";
import AuraOrb from "@/components/voice/AuraOrb";
import ChatWindow from "@/components/chat/ChatWindow";
import ChatInput from "@/components/chat/ChatInput";
import ActivityPanel from "@/components/activity/ActivityPanel";
import ConfirmationDialog from "@/components/confirmation/ConfirmationDialog";
import { useChat } from "@/hooks/useChat";
import { useVoice } from "@/hooks/useVoice";
import { useConfirmationStore, useChatStore } from "@/store";
import { apiClient } from "@/services/api";

export default function MainPage() {
  const navigate = useNavigate();
  const { sendMessage } = useChat();
  const { toggleVoice } = useVoice();
  const { setPending } = useConfirmationStore();

  const handleConfirm = async (confirmationId: string) => {
    setPending(null);
    await apiClient.confirmAction(confirmationId, true);
  };

  const handleCancel = async (confirmationId: string) => {
    setPending(null);
    await apiClient.confirmAction(confirmationId, false);
  };

  return (
    <div className="flex flex-col h-full bg-[#0f0f1a] relative overflow-hidden">
      {/* Custom title bar */}
      <TitleBar />

      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-2.5 flex-shrink-0">
        <StatusIndicator />
        <div className="flex items-center gap-1">
          <HeaderButton onClick={() => navigate("/activity")} title="Activity">
            <Activity size={16} />
          </HeaderButton>
          <HeaderButton onClick={() => navigate("/settings")} title="Settings">
            <Settings size={16} />
          </HeaderButton>
        </div>
      </div>

      {/* Orb hero — shown when chat is empty */}
      <OrbSection />

      {/* Chat messages */}
      <ChatWindow className="flex-1 min-h-0" />

      {/* Activity summary (bottom of empty state) */}
      <ActivityPanel maxItems={3} />

      {/* Text input */}
      <ChatInput onSend={sendMessage} onVoiceToggle={toggleVoice} />

      {/* Confirmation overlay */}
      <ConfirmationDialog onConfirm={handleConfirm} onCancel={handleCancel} />
    </div>
  );
}

function OrbSection() {
  const { toggleVoice } = useVoice();
  const { messages } = useChatStore();

  if (messages.length > 0) return null;

  return (
    <div className="flex flex-col items-center justify-center pt-6 pb-2 flex-shrink-0">
      <AuraOrb onClick={toggleVoice} />
    </div>
  );
}

function HeaderButton({
  onClick,
  title,
  children,
}: {
  onClick: () => void;
  title: string;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      title={title}
      className="w-8 h-8 rounded-xl flex items-center justify-center
                 text-white/30 hover:text-white/70 hover:bg-white/8
                 transition-all duration-150"
    >
      {children}
    </button>
  );
}
