import { useEffect } from "react";
import { Routes, Route, useNavigate } from "react-router-dom";
import { useSettingsStore } from "@/store";
import MainPage from "@/pages/MainPage";
import SettingsPage from "@/pages/SettingsPage";
import ActivityPage from "@/pages/ActivityPage";
import OnboardingPage from "@/pages/OnboardingPage";
import { useBackendConnection } from "@/hooks/useBackendConnection";

export default function App() {
  const navigate = useNavigate();
  const { settings } = useSettingsStore();

  // Connect to FastAPI backend
  useBackendConnection();

  // Tauri tray-menu navigation — only attempt inside a real Tauri window.
  // Wrapped in try/catch because the Tauri IPC bridge may not be initialised
  // even when the package is bundled (e.g. plain browser dev mode).
  useEffect(() => {
    let unlisten: (() => void) | undefined;

    const setup = async () => {
      try {
        // This throws if Tauri IPC is not available
        const { listen } = await import("@tauri-apps/api/event");
        unlisten = await listen<string>("navigate", (event) => {
          navigate(event.payload);
        });
      } catch {
        // Not running inside Tauri — silently ignore
      }
    };

    setup();

    return () => {
      unlisten?.();
    };
  }, [navigate]);

  // First-run onboarding redirect
  useEffect(() => {
    if (!settings.first_run_complete) {
      navigate("/onboarding");
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="w-full h-screen flex flex-col overflow-hidden bg-[#0f0f1a]">
      <Routes>
        <Route path="/"           element={<MainPage />} />
        <Route path="/settings"   element={<SettingsPage />} />
        <Route path="/activity"   element={<ActivityPage />} />
        <Route path="/onboarding" element={<OnboardingPage />} />
      </Routes>
    </div>
  );
}
