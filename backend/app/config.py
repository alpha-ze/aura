"""
AURA Backend Configuration
Loaded once at startup from environment variables + .env file.
Never stores raw secrets in memory beyond what's needed.
"""
from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


# ── Enumerations ──────────────────────────────────────────────────────────────

class AIProvider(str, Enum):
    OPENAI    = "openai"
    ANTHROPIC = "anthropic"
    GEMINI    = "gemini"
    OLLAMA    = "ollama"
    GROQ      = "groq"


class STTProvider(str, Enum):
    WHISPER_LOCAL = "whisper_local"
    WHISPER_API   = "whisper_api"
    AZURE_STT     = "azure_stt"


class TTSProvider(str, Enum):
    WINDOWS_SAPI = "windows_sapi"
    PIPER        = "piper"
    AZURE_TTS    = "azure_tts"
    ELEVENLABS   = "elevenlabs"


class PermissionMode(str, Enum):
    SAFE        = "safe"
    BALANCED    = "balanced"
    POWER_USER  = "power_user"


class LogLevel(str, Enum):
    DEBUG    = "DEBUG"
    INFO     = "INFO"
    WARNING  = "WARNING"
    ERROR    = "ERROR"
    CRITICAL = "CRITICAL"


# ── Settings ──────────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Server — MUST bind to localhost only
    backend_host: str = Field(default="127.0.0.1")
    backend_port: int = Field(default=8765)

    # AI provider (API keys are fetched from secure storage at runtime, not here)
    ai_provider: AIProvider = Field(default=AIProvider.GROQ)
    openai_model: str = Field(default="gpt-4o")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022")
    gemini_model: str = Field(default="gemini-1.5-pro")
    ollama_model: str = Field(default="llama3.2")
    ollama_base_url: str = Field(default="http://localhost:11434")
    groq_model: str = Field(default="qwen/qwen3.8-27b")
    groq_base_url: str = Field(default="https://api.groq.com/openai/v1")
    groq_api_key: str = Field(default="")

    # Voice
    stt_provider: STTProvider = Field(default=STTProvider.WHISPER_LOCAL)
    whisper_model: str = Field(default="base.en")
    tts_provider: TTSProvider = Field(default=TTSProvider.WINDOWS_SAPI)

    # Permissions
    permission_mode: PermissionMode = Field(default=PermissionMode.BALANCED)

    # Security — used for session token signing
    secret_key: str = Field(default="change-me-to-a-random-64-char-string")

    # Logging
    log_level: LogLevel = Field(default=LogLevel.INFO)
    log_dir: Path = Field(default=Path("./logs"))

    # Feature flags
    enable_memory: bool = Field(default=True)
    enable_activity_log: bool = Field(default=True)
    enable_voice: bool = Field(default=True)
    dry_run_default: bool = Field(default=False)

    # Paths
    data_dir: Path = Field(default=Path(__file__).parent.parent / "data")

    @field_validator("backend_host")
    @classmethod
    def must_be_localhost(cls, v: str) -> str:
        """Enforce localhost-only binding for security."""
        allowed = {"127.0.0.1", "localhost", "::1"}
        if v not in allowed:
            raise ValueError(
                f"backend_host must be a loopback address. Got: {v!r}. "
                "AURA must never be exposed to external networks."
            )
        return v

    @property
    def active_model(self) -> str:
        models = {
            AIProvider.OPENAI:    self.openai_model,
            AIProvider.ANTHROPIC: self.anthropic_model,
            AIProvider.GEMINI:    self.gemini_model,
            AIProvider.OLLAMA:    self.ollama_model,
            AIProvider.GROQ:      self.groq_model,
        }
        return models[self.ai_provider]

    def ensure_dirs(self) -> None:
        """Create required data/log directories if they don't exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)


# Module-level singleton — import this everywhere
settings = Settings()
