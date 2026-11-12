import { useEffect, useRef } from "react";
import { apiClient, wsClient } from "@/services/api";
import { useSystemStore, useAgentEventStore, useConfirmationStore } from "@/store";
import type { AgentEvent, ConfirmationRequest } from "@/types";

const HEALTH_INTERVAL_MS = 10_000;

/**
 * Manages the connection to the FastAPI backend.
 * Safe under React StrictMode — cleanup fully cancels reconnect attempts.
 */
export function useBackendConnection() {
  const { setBackendConnected, setBackendVersion, setSystemInfo } = useSystemStore();
  const { pushEvent }   = useAgentEventStore();
  const { setPending }  = useConfirmationStore();
  const intervalRef     = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    let cancelled = false;

    const checkHealth = async () => {
      if (cancelled) return;
      try {
        const h = await apiClient.health();
        if (cancelled) return;
        setBackendConnected(true);
        setBackendVersion(h.version);
      } catch {
        if (!cancelled) setBackendConnected(false);
      }
    };

    const fetchSystem = async () => {
      if (cancelled) return;
      try {
        const info = await apiClient.getSystemInfo();
        if (!cancelled) setSystemInfo(info);
      } catch { /* non-critical */ }
    };

    // Initial checks
    checkHealth();
    fetchSystem();

    // Periodic health poll
    intervalRef.current = setInterval(checkHealth, HEALTH_INTERVAL_MS);

    // WebSocket
    wsClient.connect();

    const offConnected    = wsClient.on("connected",    () => { if (!cancelled) { setBackendConnected(true); fetchSystem(); } });
    const offDisconnected = wsClient.on("disconnected", () => { if (!cancelled) setBackendConnected(false); });
    const offMessage      = wsClient.on("message",      (data) => {
      if (cancelled) return;
      const event = data as AgentEvent;
      pushEvent(event);
      if (event.type === "WAITING_CONFIRMATION" && event.data) {
        setPending(event.data as ConfirmationRequest);
      }
    });

    return () => {
      cancelled = true;
      if (intervalRef.current) clearInterval(intervalRef.current);
      offConnected();
      offDisconnected();
      offMessage();
      wsClient.disconnect();
    };
  }, []); // eslint-disable-line react-hooks/exhaustive-deps
}
