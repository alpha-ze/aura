"""
AURA FastAPI Application Entry Point.

Security: The server MUST only be started bound to 127.0.0.1.
          Never expose this server to external networks.
"""
from __future__ import annotations

import asyncio
import time
from contextlib import asynccontextmanager
from uuid import uuid4

import structlog
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.logging_config import setup_logging
from app.models.schemas import (
    AgentEvent,
    AgentStatusEvent,
    BackendHealth,
    ConfirmationResponse,
)

# ── Logging ───────────────────────────────────────────────────────────────────
setup_logging(log_level=settings.log_level.value, log_dir=settings.log_dir)
log = structlog.get_logger(__name__)

_START_TIME = time.monotonic()
_VERSION = "0.1.0"


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    """
    Set up all application singletons on startup and tear down on shutdown.
    NOTE: parameter is named fastapi_app (not 'app') to avoid shadowing
          the 'app' Python package when doing local imports.
    """
    log.info("aura_backend_starting", version=_VERSION)
    settings.ensure_dirs()

    # ── Storage ───────────────────────────────────────────────────────────────
    from app.storage.activity_log import ActivityLogger
    from app.storage.task_store import TaskStore
    from app.storage.memory_store import MemoryStore

    activity_log = ActivityLogger(settings.data_dir)
    task_store   = TaskStore(settings.data_dir)
    memory_store = MemoryStore(settings.data_dir)

    # ── Tool registry — import modules to trigger @registry.register ──────────
    from app.agent.router import registry as tool_registry
    import app.tools.files      # noqa: F401
    import app.tools.system     # noqa: F401
    import app.tools.apps       # noqa: F401
    import app.tools.network    # noqa: F401
    import app.tools.audio      # noqa: F401
    import app.tools.bluetooth  # noqa: F401
    log.info("tools_loaded", count=tool_registry.tool_count)

    # ── AI Provider ───────────────────────────────────────────────────────────
    from app.agent.providers import create_provider
    from app.agent.memory import AgentMemory
    from app.agent.agent import AuraAgent

    ai_provider  = create_provider()
    agent_memory = AgentMemory(memory_store)
    agent = AuraAgent(
        provider=ai_provider,
        registry=tool_registry,
        memory=agent_memory,
        activity_log=activity_log,
    )

    # ── Attach everything to FastAPI app state ────────────────────────────────
    fastapi_app.state.agent              = agent
    fastapi_app.state.registry           = tool_registry
    fastapi_app.state.activity_log       = activity_log
    fastapi_app.state.task_store         = task_store
    fastapi_app.state.memory_store       = memory_store
    fastapi_app.state.conversation_store = {}   # conversation_id -> [messages]
    fastapi_app.state.ws_connections     = {}   # ws_id -> WebSocket

    log.info("aura_backend_ready", host=settings.backend_host, port=settings.backend_port)

    yield  # ← server runs here

    log.info("aura_backend_shutting_down")


# ── App factory ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="AURA Backend",
    description="Local-only AI personal assistant backend for Windows.",
    version=_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — only allow the Tauri / Vite dev origins (both local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:1420",
        "http://127.0.0.1:1420",
        "tauri://localhost",
        "https://tauri.localhost",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
from app.api.chat     import router as chat_router
from app.api.system   import router as system_router
from app.api.tools    import router as tools_router
from app.api.activity import router as activity_router
from app.api.tasks    import router as tasks_router
from app.api.settings import router as settings_router
from app.api.voice    import router as voice_router

app.include_router(chat_router)
app.include_router(system_router)
app.include_router(tools_router)
app.include_router(activity_router)
app.include_router(tasks_router)
app.include_router(settings_router)
app.include_router(voice_router)


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health", response_model=BackendHealth, tags=["health"])
async def health() -> BackendHealth:
    uptime   = time.monotonic() - _START_TIME
    provider = app.state.agent._provider

    try:
        provider_ok = await asyncio.wait_for(provider.is_available(), timeout=3.0)
    except Exception:
        provider_ok = False

    return BackendHealth(
        status="ok" if provider_ok else "degraded",
        version=_VERSION,
        ai_provider_connected=provider_ok,
        tools_loaded=app.state.registry.tool_count,
        uptime_seconds=round(uptime, 1),
    )


# ── Confirmation ──────────────────────────────────────────────────────────────

@app.post("/api/confirmations/respond", tags=["agent"])
async def respond_confirmation(payload: ConfirmationResponse):
    from app.agent.agent import AuraAgent
    agent: AuraAgent = app.state.agent
    return await agent.handle_confirmation(payload.confirmation_id, payload.confirmed)


# ── WebSocket ─────────────────────────────────────────────────────────────────

@app.websocket("/ws/agent")
async def ws_agent(websocket: WebSocket, conversation_id: str | None = None):
    """Real-time agent status stream."""
    await websocket.accept()
    ws_id = str(uuid4())
    app.state.ws_connections[ws_id] = websocket
    log.info("ws_connected", ws_id=ws_id)

    try:
        while True:
            try:
                await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                event = AgentEvent(type=AgentStatusEvent.STATUS, message="connected")
                await websocket.send_text(event.model_dump_json())
            except asyncio.TimeoutError:
                event = AgentEvent(type=AgentStatusEvent.STATUS, message="heartbeat")
                await websocket.send_text(event.model_dump_json())
    except WebSocketDisconnect:
        log.info("ws_disconnected", ws_id=ws_id)
    except Exception as exc:
        log.warning("ws_error", ws_id=ws_id, error=str(exc))
    finally:
        app.state.ws_connections.pop(ws_id, None)


async def broadcast_event(event: AgentEvent) -> None:
    """Broadcast an agent event to all connected WebSocket clients."""
    if not hasattr(app.state, "ws_connections"):
        return
    dead: list[str] = []
    payload = event.model_dump_json()
    for ws_id, ws in app.state.ws_connections.items():
        try:
            await ws.send_text(payload)
        except Exception:
            dead.append(ws_id)
    for ws_id in dead:
        app.state.ws_connections.pop(ws_id, None)


# ── Root ──────────────────────────────────────────────────────────────────────

@app.get("/", tags=["health"])
async def root():
    return {
        "name": "AURA Backend",
        "version": _VERSION,
        "status": "running",
        "docs": "/docs",
        "note": "This server runs locally only. Never expose it externally.",
    }
