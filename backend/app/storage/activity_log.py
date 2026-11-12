"""
Local activity log — stores AURA actions as JSON-lines on disk.
In-memory ring buffer for fast reads; persists to disk asynchronously.
"""
from __future__ import annotations

import asyncio
import json
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

import structlog

from app.models.schemas import ActivityEntry, RiskLevel

log = structlog.get_logger(__name__)

_MAX_MEMORY_ENTRIES = 1000


class ActivityLogger:
    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._log_file = data_dir / "activity.jsonl"
        self._entries: deque[ActivityEntry] = deque(maxlen=_MAX_MEMORY_ENTRIES)
        self._lock = asyncio.Lock()
        self._loaded = False

    async def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if self._log_file.exists():
            try:
                lines = self._log_file.read_text(encoding="utf-8").splitlines()
                for line in lines[-_MAX_MEMORY_ENTRIES:]:
                    entry = ActivityEntry.model_validate_json(line)
                    self._entries.append(entry)
            except Exception as exc:
                log.warning("activity_log_load_failed", error=str(exc))

    async def log(
        self,
        *,
        type: str,
        summary: str,
        detail: Optional[str] = None,
        risk_level: Optional[RiskLevel] = None,
        success: Optional[bool] = None,
    ) -> ActivityEntry:
        entry = ActivityEntry(
            id=str(uuid4()),
            type=type,
            summary=summary,
            detail=detail,
            timestamp=datetime.now(tz=timezone.utc),
            risk_level=risk_level,
            success=success,
        )
        async with self._lock:
            await self._ensure_loaded()
            self._entries.appendleft(entry)
            # Append to file
            try:
                self._data_dir.mkdir(parents=True, exist_ok=True)
                with open(self._log_file, "a", encoding="utf-8") as f:
                    f.write(entry.model_dump_json() + "\n")
            except Exception as exc:
                log.warning("activity_log_write_failed", error=str(exc))

        return entry

    async def get_entries(self, limit: int = 100) -> list[ActivityEntry]:
        async with self._lock:
            await self._ensure_loaded()
            return list(self._entries)[:limit]

    async def clear(self) -> None:
        async with self._lock:
            self._entries.clear()
            try:
                self._log_file.unlink(missing_ok=True)
            except Exception as exc:
                log.warning("activity_log_clear_failed", error=str(exc))
