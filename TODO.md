# AURA — Development TODO

Tracks implementation progress across all phases.
Updated as each feature is completed.

---

## ✅ PHASE 1 — Foundation (COMPLETE)

### Project Scaffolding
- [x] Root directory structure (AURA/, desktop/, backend/, installer/, docs/, scripts/)
- [x] .gitignore, .env.example, README.md, LICENSE

### Desktop Frontend (Tauri + React + TypeScript + Vite + Tailwind)
- [x] Tauri 2 Rust shell (lib.rs, main.rs, Cargo.toml, tauri.conf.json)
- [x] Vite + React 18 + TypeScript config
- [x] Tailwind CSS with custom AURA theme (dark glassmorphism)
- [x] Shared TypeScript types (types/index.ts)
- [x] Zustand state stores (chat, voice, activity, tasks, settings, confirmation)
- [x] UI components: TitleBar, StatusIndicator
- [x] Voice component: AuraOrb (idle/listening/thinking/speaking states)
- [x] Chat components: ChatMessage, ChatInput, ChatWindow
- [x] Activity panel
- [x] Confirmation dialog (risk-aware, with Cancel/Confirm)
- [x] Pages: Main, Settings, Activity, Onboarding (5-step wizard)
- [x] React Router navigation (hash-based for Tauri)
- [x] Tauri system tray with right-click menu
- [x] Window control buttons (minimize/maximize/close-to-tray)

### API Service Layer
- [x] AuraApiClient (health, chat, system, tools, activity, tasks, settings)
- [x] AuraWebSocket (reconnecting WebSocket for real-time agent events)
- [x] useBackendConnection hook (health polling + WS management)
- [x] useChat hook (send messages, status tracking)
- [x] useVoice hook (MediaRecorder → /api/voice → transcript → chat)

### FastAPI Backend
- [x] app/config.py — Pydantic settings with localhost enforcement
- [x] app/logging_config.py — structured logs (structlog), sensitive key scrubbing
- [x] app/models/schemas.py — all Pydantic v2 request/response models
- [x] app/security/credential_store.py — Windows Credential Manager / keyring
- [x] app/security/path_validator.py — path traversal prevention
- [x] app/security/input_sanitiser.py — prompt injection defence
- [x] app/storage/activity_log.py — JSON-lines activity log
- [x] app/storage/task_store.py — local JSON task persistence
- [x] app/storage/memory_store.py — user preference memory
- [x] app/agent/safety.py — risk levels, permission modes, confirmation builder, audit log
- [x] app/agent/memory.py — AgentMemory with typed helpers
- [x] app/agent/planner.py — tool call parser, plan builder
- [x] app/agent/providers.py — OpenAI, Anthropic, Gemini, Ollama, **Groq** providers
- [x] app/agent/router.py — ToolRegistry with timed execution + audit logging
- [x] app/agent/agent.py — full agent loop (multi-step, confirmation handling)
- [x] app/tools/files.py — search, open, rename, move, copy, delete, create_folder
- [x] app/tools/system.py — system info, processes, storage, battery, kill_process
- [x] app/tools/apps.py — list, open, close, uninstall applications
- [x] app/tools/network.py — Wi-Fi status, networks, diagnostics, flush_dns
- [x] app/tools/audio.py — get/set volume, mute/unmute, devices
- [x] app/tools/bluetooth.py — status, toggle, restart_service
- [x] app/api/chat.py — POST /api/chat
- [x] app/api/system.py — GET /api/system, /api/system/processes
- [x] app/api/tools.py — GET /api/tools, POST /api/tools/execute
- [x] app/api/activity.py — GET/DELETE /api/activity
- [x] app/api/tasks.py — CRUD /api/tasks
- [x] app/api/settings.py — GET/PUT /api/settings, PUT /api/settings/api-key
- [x] app/api/voice.py — POST /api/voice (Whisper STT)
- [x] app/main.py — FastAPI app, CORS, lifespan, WebSocket /ws/agent, health endpoint
- [x] requirements.txt, pyproject.toml

### Dev Scripts
- [x] scripts/setup.ps1 — first-time environment setup
- [x] scripts/dev.ps1 — concurrent backend + frontend startup

---

## ⬜ PHASE 2 — AI + Core Tools (NEXT)

- [ ] Test agent loop end-to-end with a real AI provider
- [ ] Improve tool call extraction from model output (robustness)
- [ ] Add get_recent_files improvements (Windows Search index integration)
- [ ] Add processes/startup_apps tools
- [ ] Add show_in_explorer, get_file_info tools
- [ ] Improve application launcher (search PATH, registry, Start Menu)
- [ ] Add compress_files, extract_archive tools
- [ ] Refine agent system prompt for better tool call formatting
- [ ] Add dry-run mode for file operations

---

## ⬜ PHASE 3 — System + Network + Audio

- [ ] GPU information (using subprocess + wmic or WMI)
- [ ] Display/brightness control (WMI or windows-sdk)
- [ ] get_startup_apps tool
- [ ] network_diagnostics improvements (traceroute, MTU)
- [ ] renew_ip tool
- [ ] restart_network_adapter (HIGH risk, netsh wlan/interface)
- [ ] Bluetooth device discovery
- [ ] Microphone test tool

---

## ⬜ PHASE 4 — Voice

- [ ] VAD (Voice Activity Detection) — silero-vad or webrtcvad
- [ ] Wake word detection (openWakeWord or custom)
- [ ] Improve STT accuracy (faster-whisper large model option)
- [ ] Windows SAPI TTS integration
- [ ] Piper TTS (local, high-quality)
- [ ] Voice playback in frontend (audio element, streaming)
- [ ] Voice waveform visualisation improvements

---

## ⬜ PHASE 5 — Safety + Permissions

- [ ] Rate limiting for tools (prevent rapid-fire destructive calls)
- [ ] Per-session permission override store
- [ ] Dry-run report UI
- [ ] Rollback for reversible operations (rename, move)
- [ ] Confirmation dialog improvements (show full path diff)

---

## ⬜ PHASE 6 — Troubleshooting Engine

- [ ] Dedicated TroubleshootingAgent class
- [ ] Internet troubleshooter (automated 7-step diagnosis + fix)
- [ ] High RAM troubleshooter
- [ ] High CPU troubleshooter
- [ ] Audio/microphone troubleshooter
- [ ] Application not responding diagnosis
- [ ] Storage cleanup suggestions

---

## ⬜ PHASE 7 — Memory + Tasks + UX

- [ ] Memory dashboard UI (view, edit, clear)
- [ ] Task UI in frontend (list, create, complete, delete)
- [ ] Tasks natural language support ("remind me tomorrow")
- [ ] Global hotkey (Ctrl+Space) via Tauri plugin
- [ ] Improved onboarding API key validation
- [ ] First-run microphone test
- [ ] Light theme implementation

---

## ⬜ PHASE 8 — Testing + Packaging

- [ ] Unit tests: path_validator, safety, planner, tool results
- [ ] Integration tests: agent loop, file tools, system tools
- [ ] Security tests: path traversal, command injection, prompt injection
- [ ] Mock Windows APIs for CI testing
- [ ] GitHub Actions CI pipeline
- [ ] Tauri bundler configuration (NSIS installer)
- [ ] Bundle Python backend (PyInstaller → no Python required)
- [ ] Auto-start backend with Tauri
- [ ] AURA-Setup.exe production installer
- [ ] Code signing (optional)
- [ ] Uninstaller tested

---

## Notes

- Rust must be installed from https://rustup.rs to build the Tauri desktop app
- The backend binds to 127.0.0.1 ONLY — this is a security requirement
- Never commit .env files (they contain API keys)
- Run `scripts/setup.ps1` for first-time environment setup
