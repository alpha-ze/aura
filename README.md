# AURA — Autonomous Windows AI Personal Assistant

AURA is a production-quality Windows desktop AI assistant that lets you control your computer using natural language and voice.

## What AURA Can Do

- **File Management** — search, rename, move, copy, delete, create folders, find recent files
- **Application Control** — launch, close, uninstall applications
- **System Diagnostics** — CPU, RAM, GPU, disk, battery, uptime
- **Network** — Wi-Fi status, connect/disconnect, troubleshoot internet
- **Bluetooth** — status, enable/disable, device management
- **Audio** — get/set volume, mute, microphone test
- **Troubleshooting** — intelligent diagnosis of system issues
- **Voice Interaction** — push-to-talk, voice activity detection, TTS responses
- **Tasks & Reminders** — create and manage local tasks
- **Multi-step Planning** — AURA reasons about complex requests step-by-step

## Tech Stack

| Layer | Technology |
|---|---|
| Desktop | Tauri 2 + React 18 + TypeScript + Vite + Tailwind CSS |
| Backend | Python 3.12 + FastAPI + asyncio |
| AI | OpenAI / Anthropic / Gemini / Ollama (provider-independent) |
| Voice | Whisper (STT) + Windows SAPI / Piper (TTS) |
| OS Integration | psutil + pywin32 + subprocess + PowerShell |

## Quick Start (Development)

### Prerequisites

- Node.js 20+
- Rust (for Tauri)
- Python 3.12+
- Windows 10/11

### 1. Clone & Setup

```bash
git clone https://github.com/yourname/aura.git
cd aura
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp ../.env.example ../.env
# Edit .env with your API keys
```

### 3. Frontend Setup

```bash
cd desktop
npm install
```

### 4. Run Development

Open two terminals:

**Terminal 1 — Backend:**
```bash
cd backend
.venv\Scripts\activate
python -m uvicorn app.main:app --host 127.0.0.1 --port 8765 --reload
```

**Terminal 2 — Desktop:**
```bash
cd desktop
npm run tauri dev
```

Or use the convenience script:
```bash
.\scripts\dev.ps1
```

## Architecture

```
User
 │
 ├─ Voice / Text Input
 │
 ▼
Speech-to-Text (Whisper / Azure)
 │
 ▼
AI Agent Core (FastAPI + Python)
 │
 ├─ Intent Detection
 ├─ Planning
 ├─ Permission / Safety Layer
 │
 ▼
Tool Router
 │
 ▼
Tool Registry
 ├─ File Tools
 ├─ App Tools
 ├─ System Tools
 ├─ Network Tools
 ├─ Audio Tools
 └─ Process Tools
 │
 ▼
Windows OS (psutil / pywin32 / PowerShell / WinAPI)
 │
 ▼
Result → AI Response → Text-to-Speech
```

## Permission Modes

| Mode | Description |
|---|---|
| Safe | Asks confirmation for almost every modification |
| Balanced | Auto-executes low-risk, confirms medium/high |
| Power User | More automation, still confirms destructive actions |

## Security

- Backend binds to `127.0.0.1` only — never exposed publicly
- All file paths are validated and sandboxed
- Destructive operations require explicit confirmation
- Prompt injection from file contents is actively blocked
- API keys stored via OS secure storage
- Full audit log of all tool executions
- No telemetry, no data collection, local-first

## Project Structure

```
AURA/
├── desktop/          # Tauri + React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── main.tsx
│   └── src-tauri/    # Tauri Rust shell
│
├── backend/          # FastAPI Python backend
│   └── app/
│       ├── agent/    # AI agent loop
│       ├── tools/    # Windows tool implementations
│       ├── voice/    # STT / TTS / VAD
│       ├── diagnostics/
│       └── api/      # REST + WebSocket endpoints
│
├── installer/        # NSIS / WiX installer config
├── docs/             # Architecture & user docs
├── scripts/          # Dev & build convenience scripts
└── .env.example      # Configuration template
```

## Documentation

- [Architecture Guide](docs/ARCHITECTURE.md)
- [Developer Guide](docs/DEVELOPER_GUIDE.md)
- [Tool Development Guide](docs/TOOL_GUIDE.md)
- [Security Documentation](docs/SECURITY.md)
- [Privacy Documentation](docs/PRIVACY.md)
- [API Reference](docs/API.md)

## License

MIT License — see [LICENSE](LICENSE)
