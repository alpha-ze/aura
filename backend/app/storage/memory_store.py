"""
Local memory store for AURA.
Stores user preferences and learned habits as a simple JSON file.
Never stores API keys, passwords, or sensitive file contents.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Optional

import structlog

log = structlog.get_logger(__name__)

_FORBIDDEN_MEMORY_KEYS = frozenset({
    "api_key", "password", "token", "secret", "credential",
    "private_key", "auth",
})


class MemoryStore:
    def __init__(self, data_dir: Path) -> None:
        self._file = data_dir / "memory.json"
        self._data: dict[str, Any] = {}
        self._lock = asyncio.Lock()
        self._loaded = False

    async def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if self._file.exists():
            try:
                self._data = json.loads(self._file.read_text(encoding="utf-8"))
            except Exception as exc:
                log.warning("memory_load_failed", error=str(exc))

    async def _persist(self) -> None:
        try:
            self._file.parent.mkdir(parents=True, exist_ok=True)
            self._file.write_text(json.dumps(self._data, indent=2, default=str), encoding="utf-8")
        except Exception as exc:
            log.warning("memory_save_failed", error=str(exc))

    def _check_key(self, key: str) -> None:
        if any(s in key.lower() for s in _FORBIDDEN_MEMORY_KEYS):
            raise ValueError(f"Memory key {key!r} is not allowed — sensitive data must not be stored in memory.")

    async def set(self, key: str, value: Any) -> None:
        self._check_key(key)
        async with self._lock:
            await self._ensure_loaded()
            self._data[key] = value
            await self._persist()

    async def get(self, key: str, default: Any = None) -> Any:
        async with self._lock:
            await self._ensure_loaded()
            return self._data.get(key, default)

    async def get_all(self) -> dict[str, Any]:
        async with self._lock:
            await self._ensure_loaded()
            return dict(self._data)

    async def delete(self, key: str) -> bool:
        async with self._lock:
            await self._ensure_loaded()
            existed = key in self._data
            self._data.pop(key, None)
            await self._persist()
            return existed

    async def clear(self) -> None:
        async with self._lock:
            self._data = {}
            await self._persist()
