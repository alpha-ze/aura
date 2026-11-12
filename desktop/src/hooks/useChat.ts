import { useCallback } from "react";
import { apiClient } from "@/services/api";
import {
  useChatStore,
  useActivityStore,
  useAgentEventStore,
} from "@/store";
import { generateId } from "@/utils/format";
import type { ChatMessage, AgentEvent } from "@/types";

/**
 * Manages chat message flow.
 * Sends messages to the agent, tracks status, and writes to stores.
 */
export function useChat() {
  const {
    messages,
    addMessage,
    updateMessage,
    setAgentStatus,
    setConversationId,
    conversationId,
  } = useChatStore();

  const { addEntry } = useActivityStore();
  const { pushEvent } = useAgentEventStore();

  const sendMessage = useCallback(
    async (text: string) => {
      if (!text.trim()) return;

      const userMsgId = generateId();
      const assistantMsgId = generateId();

      // Add user message immediately
      const userMsg: ChatMessage = {
        id: userMsgId,
        role: "user",
        content: text,
        timestamp: new Date(),
      };
      addMessage(userMsg);

      // Add placeholder assistant message
      const assistantMsg: ChatMessage = {
        id: assistantMsgId,
        role: "assistant",
        content: "",
        timestamp: new Date(),
        status: "thinking",
      };
      addMessage(assistantMsg);
      setAgentStatus("thinking");

      // Log activity
      addEntry({
        id: generateId(),
        type: "command",
        summary: text.length > 60 ? text.slice(0, 60) + "…" : text,
        timestamp: new Date(),
      });

      try {
        const response = await apiClient.sendMessage({
          message: text,
          conversation_id: conversationId ?? undefined,
        });

        // Store conversation ID for context
        if (response.conversation_id) {
          setConversationId(response.conversation_id);
        }

        // Update assistant message with response
        updateMessage(assistantMsgId, {
          content: response.message,
          plan: response.plan,
          status: response.success ? "completed" : "error",
        });

        setAgentStatus(response.success ? "completed" : "error");

        // Push synthetic event
        const event: AgentEvent = {
          type: response.success ? "COMPLETED" : "ERROR",
          message: response.message,
          timestamp: new Date().toISOString(),
        };
        pushEvent(event);
      } catch (error) {
        const errMsg =
          error instanceof Error ? error.message : "Failed to reach AURA backend.";

        updateMessage(assistantMsgId, {
          content: `⚠ ${errMsg}\n\nMake sure the AURA backend is running:\n\`\`\`\ncd backend && python -m uvicorn app.main:app --host 127.0.0.1 --port 8765\n\`\`\``,
          status: "error",
        });

        setAgentStatus("error");
      }
    },
    [
      addMessage,
      updateMessage,
      setAgentStatus,
      setConversationId,
      addEntry,
      pushEvent,
      conversationId,
    ]
  );

  return { messages, sendMessage };
}
