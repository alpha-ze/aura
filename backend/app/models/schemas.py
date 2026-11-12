"""
Pydantic v2 request/response schemas shared across the API layer.
All user input is validated here before reaching the agent or tools.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Enums ─────────────────────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW      = "low"
    MEDIUM   = "medium"
    HIGH     = "high"
    CRITICAL = "critical"


class MessageRole(str, Enum):
    USER      = "user"
    ASSISTANT = "assistant"
    SYSTEM    = "system"
    TOOL      = "tool"


class AgentStatusEvent(str, Enum):
    LISTENING            = "LISTENING"
    THINKING             = "THINKING"
    PLANNING             = "PLANNING"
    EXECUTING_TOOL       = "EXECUTING_TOOL"
    WAITING_CONFIRMATION = "WAITING_CONFIRMATION"
    COMPLETED            = "COMPLETED"
    ERROR                = "ERROR"
    TOOL_RESULT          = "TOOL_RESULT"
    PLAN_UPDATE          = "PLAN_UPDATE"
    STATUS               = "STATUS"


class TaskPriority(str, Enum):
    LOW    = "low"
    MEDIUM = "medium"
    HIGH   = "high"


class TaskStatus(str, Enum):
    PENDING     = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED   = "completed"
    CANCELLED   = "cancelled"


# ── Tool schemas ──────────────────────────────────────────────────────────────

class ToolCall(BaseModel):
    """A validated tool invocation from the AI agent."""
    tool: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-z_]+$")
    arguments: dict[str, Any] = Field(default_factory=dict)

    @field_validator("tool")
    @classmethod
    def tool_name_safe(cls, v: str) -> str:
        # Prevent any path-like or shell-like characters in tool names
        if any(c in v for c in (".", "/", "\\", ";", "&", "|", "`", "$")):
            raise ValueError(f"Invalid tool name: {v!r}")
        return v


class ToolResult(BaseModel):
    """Structured result returned by every tool."""
    success: bool
    message: str
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    execution_time_ms: Optional[float] = None

    @classmethod
    def ok(cls, message: str, data: Any = None, **kwargs: Any) -> "ToolResult":
        return cls(success=True, message=message, data=data, **kwargs)

    @classmethod
    def fail(cls, message: str, error: str | None = None, error_code: str | None = None) -> "ToolResult":
        return cls(success=False, message=message, error=error, error_code=error_code)


# ── Chat schemas ──────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4096)
    conversation_id: Optional[str] = None
    context: Optional[dict[str, Any]] = None

    @field_validator("message")
    @classmethod
    def message_not_only_whitespace(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Message must not be empty or whitespace only.")
        return v.strip()


class PlanStep(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    description: str
    tool: Optional[str] = None
    status: str = "pending"
    result: Optional[str] = None
    error: Optional[str] = None


class AgentPlan(BaseModel):
    steps: list[PlanStep] = Field(default_factory=list)
    status: str = "pending"


class ConfirmationRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    action: str
    target: str
    description: str
    risk_level: RiskLevel
    consequences: list[str] = Field(default_factory=list)
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    plan: Optional[AgentPlan] = None
    confirmation_required: Optional[ConfirmationRequest] = None
    success: bool = True
    error: Optional[str] = None


class ConfirmationResponse(BaseModel):
    confirmation_id: str
    confirmed: bool


# ── WebSocket events ──────────────────────────────────────────────────────────

class AgentEvent(BaseModel):
    type: AgentStatusEvent
    message: Optional[str] = None
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ── System info schemas ───────────────────────────────────────────────────────

class SystemInfo(BaseModel):
    cpu_percent: float
    cpu_count: int
    ram_total_gb: float
    ram_used_gb: float
    ram_percent: float
    disk_total_gb: float
    disk_used_gb: float
    disk_free_gb: float
    disk_percent: float
    battery_percent: Optional[float] = None
    battery_plugged: Optional[bool] = None
    platform: str
    windows_version: str
    hostname: str
    uptime_seconds: float
    architecture: str


class NetworkStatus(BaseModel):
    connected: bool
    ssid: Optional[str] = None
    signal_strength: Optional[int] = None
    ip_address: Optional[str] = None
    gateway: Optional[str] = None
    dns_servers: list[str] = Field(default_factory=list)
    adapter_name: Optional[str] = None
    adapter_status: str = "unknown"


# ── Activity schemas ──────────────────────────────────────────────────────────

class ActivityEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    type: str
    summary: str
    detail: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    risk_level: Optional[RiskLevel] = None
    success: Optional[bool] = None


# ── Task schemas ──────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=256)
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    priority: TaskPriority = TaskPriority.MEDIUM


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_at: Optional[datetime] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None


class Task(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    due_at: Optional[datetime] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING


# ── Settings schemas ──────────────────────────────────────────────────────────

class ApiKeyUpdate(BaseModel):
    provider: str = Field(..., pattern=r"^(openai|anthropic|gemini|groq|elevenlabs|azure)$")
    api_key: str = Field(..., min_length=1, max_length=512)

    @field_validator("api_key")
    @classmethod
    def no_whitespace(cls, v: str) -> str:
        if v != v.strip():
            raise ValueError("API key must not have leading/trailing whitespace.")
        return v


# ── Health schema ─────────────────────────────────────────────────────────────

class BackendHealth(BaseModel):
    status: str  # "ok" | "degraded" | "error"
    version: str
    ai_provider_connected: bool
    tools_loaded: int
    uptime_seconds: float
