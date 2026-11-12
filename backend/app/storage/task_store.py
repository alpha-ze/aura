"""
Local task/reminder storage.
Persists as a single JSON file in the data directory.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from uuid import uuid4

import structlog

from app.models.schemas import Task, TaskCreate, TaskUpdate, TaskStatus

log = structlog.get_logger(__name__)


class TaskStore:
    def __init__(self, data_dir: Path) -> None:
        self._file = data_dir / "tasks.json"
        self._tasks: dict[str, Task] = {}
        self._lock = asyncio.Lock()
        self._loaded = False

    async def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._loaded = True
        if self._file.exists():
            try:
                raw = json.loads(self._file.read_text(encoding="utf-8"))
                for item in raw:
                    task = Task.model_validate(item)
                    self._tasks[task.id] = task
            except Exception as exc:
                log.warning("task_store_load_failed", error=str(exc))

    async def _persist(self) -> None:
        try:
            self._file.parent.mkdir(parents=True, exist_ok=True)
            data = [t.model_dump(mode="json") for t in self._tasks.values()]
            self._file.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        except Exception as exc:
            log.warning("task_store_save_failed", error=str(exc))

    async def list_tasks(self) -> list[Task]:
        async with self._lock:
            await self._ensure_loaded()
            return sorted(self._tasks.values(), key=lambda t: t.created_at, reverse=True)

    async def create_task(self, payload: TaskCreate) -> Task:
        task = Task(
            id=str(uuid4()),
            title=payload.title,
            description=payload.description,
            due_at=payload.due_at,
            priority=payload.priority,
            created_at=datetime.now(tz=timezone.utc),
        )
        async with self._lock:
            await self._ensure_loaded()
            self._tasks[task.id] = task
            await self._persist()
        return task

    async def update_task(self, task_id: str, payload: TaskUpdate) -> Optional[Task]:
        async with self._lock:
            await self._ensure_loaded()
            task = self._tasks.get(task_id)
            if not task:
                return None
            updated = task.model_copy(
                update={k: v for k, v in payload.model_dump().items() if v is not None}
            )
            self._tasks[task_id] = updated
            await self._persist()
            return updated

    async def delete_task(self, task_id: str) -> bool:
        async with self._lock:
            await self._ensure_loaded()
            if task_id not in self._tasks:
                return False
            del self._tasks[task_id]
            await self._persist()
            return True
