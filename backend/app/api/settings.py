"""
Settings API.
GET /api/settings           — current settings.
PUT /api/settings           — update settings.
PUT /api/settings/api-key   — store an API key securely.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import settings as app_settings
from app.models.schemas import ApiKeyUpdate
from app.security.credential_store import store_api_key, delete_api_key, has_api_key

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
async def get_settings():
    """Return safe (non-secret) settings."""
    return {
        "ai_provider": app_settings.ai_provider.value,
        "model": app_settings.active_model,
        "stt_provider": app_settings.stt_provider.value,
        "tts_provider": app_settings.tts_provider.value,
        "permission_mode": app_settings.permission_mode.value,
        "enable_memory": app_settings.enable_memory,
        "enable_activity_log": app_settings.enable_activity_log,
        "enable_voice": app_settings.enable_voice,
        "dry_run_default": app_settings.dry_run_default,
        # Indicate which providers have API keys configured (without revealing keys)
        "api_keys_configured": {
            "openai":    has_api_key("openai"),
            "anthropic": has_api_key("anthropic"),
            "gemini":    has_api_key("gemini"),
            "groq":      has_api_key("groq"),
        },
    }


@router.put("/api-key")
async def set_api_key(payload: ApiKeyUpdate):
    """
    Store an API key securely in Windows Credential Manager.
    The key is NEVER echoed back or stored in app state.
    """
    success = store_api_key(payload.provider, payload.api_key)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to store API key securely.")
    return {"message": f"API key for {payload.provider} stored securely."}


@router.delete("/api-key/{provider}")
async def remove_api_key(provider: str):
    """Remove a stored API key."""
    delete_api_key(provider)
    return {"message": f"API key for {provider} removed."}


@router.post("/api/confirmations/respond")
async def respond_to_confirmation():
    """Placeholder — handled by main.py WebSocket state."""
    raise HTTPException(status_code=501, detail="Use WebSocket for confirmation responses.")
