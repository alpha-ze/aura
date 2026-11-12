"""
Agent memory — bridges the MemoryStore to the agent loop.
Provides read/write helpers and conversation context management.
"""
from __future__ import annotations

from typing import Any, Optional

import structlog

from app.storage.memory_store import MemoryStore

log = structlog.get_logger(__name__)

# Well-known memory keys
KEY_PREFERRED_APPS        = "preferred_apps"
KEY_COMMON_FOLDERS        = "common_folders"
KEY_PERMISSION_MODE       = "permission_mode"
KEY_LAST_OPENED_FILES     = "last_opened_files"
KEY_FREQUENT_COMMANDS     = "frequent_commands"
KEY_USER_NAME             = "user_name"
KEY_ASSISTANT_PERSONALITY = "assistant_personality"


class AgentMemory:
    """
    Thin wrapper around MemoryStore providing typed helpers
    used by the agent loop.
    """

    def __init__(self, store: MemoryStore) -> None:
        self._store = store

    # ── Generic ───────────────────────────────────────────────────────────────

    async def remember(self, key: str, value: Any) -> None:
        await self._store.set(key, value)

    async def recall(self, key: str, default: Any = None) -> Any:
        return await self._store.get(key, default)

    async def forget(self, key: str) -> None:
        await self._store.delete(key)

    async def forget_all(self) -> None:
        await self._store.clear()
        log.info("memory_cleared")

    async def dump(self) -> dict[str, Any]:
        return await self._store.get_all()

    # ── Typed helpers ─────────────────────────────────────────────────────────

    async def get_preferred_apps(self) -> list[str]:
        return await self.recall(KEY_PREFERRED_APPS, [])

    async def add_preferred_app(self, app_name: str) -> None:
        apps: list[str] = await self.get_preferred_apps()
        if app_name not in apps:
            apps.insert(0, app_name)
            await self.remember(KEY_PREFERRED_APPS, apps[:20])

    async def get_common_folders(self) -> list[str]:
        return await self.recall(KEY_COMMON_FOLDERS, [])

    async def record_opened_file(self, path: str) -> None:
        recent: list[str] = await self.recall(KEY_LAST_OPENED_FILES, [])
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        await self.remember(KEY_LAST_OPENED_FILES, recent[:50])

    async def record_command(self, command: str) -> None:
        freq: dict[str, int] = await self.recall(KEY_FREQUENT_COMMANDS, {})
        freq[command] = freq.get(command, 0) + 1
        await self.remember(KEY_FREQUENT_COMMANDS, freq)

    async def build_context_snippet(self) -> str:
        """
        Build a brief text snippet of memory facts to inject into the
        agent system prompt to personalise responses.
        """
        lines: list[str] = []

        user_name = await self.recall(KEY_USER_NAME)
        if user_name:
            lines.append(f"The user's name is {user_name}.")

        preferred_apps = await self.get_preferred_apps()
        if preferred_apps:
            lines.append(f"Frequently used apps: {', '.join(preferred_apps[:5])}.")

        if not lines:
            return ""

        return "User preferences:\n" + "\n".join(f"- {l}" for l in lines)
