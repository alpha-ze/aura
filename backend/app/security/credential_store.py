"""
Secure credential storage using Windows Credential Manager (keyring).
API keys are never written to disk in plain text.
Falls back to an in-memory store for dev/testing when keyring is unavailable.
"""
from __future__ import annotations

import logging
from typing import Optional

import structlog

log = structlog.get_logger(__name__)

# Service name prefix in Windows Credential Manager
_SERVICE_PREFIX = "AURA"


def _get_keyring():
    """Import keyring lazily — it may not be installed in all environments."""
    try:
        import keyring
        return keyring
    except ImportError:
        return None


# In-memory fallback (used when keyring is not available — dev mode only)
_memory_store: dict[str, str] = {}


def store_api_key(provider: str, api_key: str) -> bool:
    """
    Store an API key securely.
    Uses Windows Credential Manager when available, memory fallback otherwise.
    Returns True on success.
    """
    service = f"{_SERVICE_PREFIX}_{provider.upper()}"
    kr = _get_keyring()
    if kr:
        try:
            kr.set_password(service, provider, api_key)
            log.info("api_key_stored", provider=provider, backend="windows_credential_manager")
            return True
        except Exception as exc:
            log.warning("keyring_store_failed", provider=provider, error=str(exc))

    # Fallback — in-memory only (dev/test)
    _memory_store[provider] = api_key
    log.warning("api_key_stored_in_memory", provider=provider,
                note="keyring unavailable — key will not persist after restart")
    return True


def get_api_key(provider: str) -> Optional[str]:
    """
    Retrieve an API key for the given provider.
    Priority: keyring → environment variable → pydantic settings → memory fallback
    """
    service = f"{_SERVICE_PREFIX}_{provider.upper()}"
    kr = _get_keyring()
    if kr:
        try:
            key = kr.get_password(service, provider)
            if key:
                return key
        except Exception as exc:
            log.warning("keyring_get_failed", provider=provider, error=str(exc))

    # Check os.environ directly (works when env vars are set in the shell)
    import os
    env_key = os.environ.get(f"{provider.upper()}_API_KEY")
    if env_key:
        return env_key

    # Check pydantic settings (loads from .env file)
    try:
        from app.config import settings as app_settings
        settings_key = getattr(app_settings, f"{provider.lower()}_api_key", None)
        if settings_key:
            return settings_key
    except Exception:
        pass

    # Memory fallback
    return _memory_store.get(provider)


def delete_api_key(provider: str) -> bool:
    """Remove a stored API key."""
    service = f"{_SERVICE_PREFIX}_{provider.upper()}"
    kr = _get_keyring()
    if kr:
        try:
            kr.delete_password(service, provider)
            log.info("api_key_deleted", provider=provider)
            return True
        except Exception as exc:
            log.warning("keyring_delete_failed", provider=provider, error=str(exc))

    _memory_store.pop(provider, None)
    return True


def has_api_key(provider: str) -> bool:
    """Return True if a key is stored for the given provider."""
    return get_api_key(provider) is not None
