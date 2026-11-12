"""
Tool router — resolves tool names to their implementations
and executes them safely.
"""
from __future__ import annotations

import time
from typing import Any, Callable, Awaitable

import structlog

from app.models.schemas import ToolCall, ToolResult, RiskLevel
from app.agent.safety import (
    get_tool_risk,
    is_blocked,
    audit_tool_call,
)

log = structlog.get_logger(__name__)

# Type alias for async tool implementations
ToolImpl = Callable[..., Awaitable[ToolResult]]


class ToolRegistry:
    """
    Central registry of all available tools.
    Tools register themselves via @registry.register().
    """

    def __init__(self) -> None:
        self._tools: dict[str, ToolImpl] = {}
        self._descriptions: dict[str, str] = {}
        self._parameters: dict[str, dict[str, Any]] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict[str, Any] | None = None,
    ):
        """Decorator for registering a tool implementation."""
        def decorator(fn: ToolImpl) -> ToolImpl:
            self._tools[name] = fn
            self._descriptions[name] = description
            self._parameters[name] = parameters or {}
            log.debug("tool_registered", name=name)
            return fn
        return decorator

    def get(self, name: str) -> ToolImpl | None:
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, Any]]:
        from app.agent.safety import get_tool_risk, requires_confirmation
        return [
            {
                "name": name,
                "description": self._descriptions[name],
                "parameters": self._parameters[name],
                "risk_level": get_tool_risk(name).value,
                "requires_confirmation": requires_confirmation(name),
            }
            for name in sorted(self._tools.keys())
        ]

    @property
    def tool_count(self) -> int:
        return len(self._tools)

    async def execute(
        self,
        tool_call: ToolCall,
        *,
        confirmed: bool = False,
    ) -> ToolResult:
        """
        Execute a validated, approved tool call.
        Handles:
          - blocked tool rejection
          - implementation lookup
          - timed execution
          - structured audit logging
          - error wrapping
        """
        tool_name = tool_call.tool

        # Reject blocked tools unconditionally
        if is_blocked(tool_name):
            log.warning("blocked_tool_call", tool=tool_name)
            return ToolResult.fail(
                f"Tool '{tool_name}' is not permitted.",
                error_code="TOOL_BLOCKED",
            )

        impl = self.get(tool_name)
        if impl is None:
            log.warning("unknown_tool", tool=tool_name)
            return ToolResult.fail(
                f"Unknown tool: '{tool_name}'.",
                error_code="TOOL_NOT_FOUND",
            )

        risk = get_tool_risk(tool_name)
        start_ms = time.monotonic() * 1000

        try:
            result = await impl(**tool_call.arguments)
            elapsed = time.monotonic() * 1000 - start_ms
            result.execution_time_ms = round(elapsed, 2)

            audit_tool_call(
                tool_name=tool_name,
                arguments=tool_call.arguments,
                risk_level=risk,
                confirmed=confirmed,
                result_success=result.success,
            )
            return result

        except TypeError as exc:
            # Wrong arguments passed by the AI
            log.warning("tool_argument_error", tool=tool_name, error=str(exc))
            return ToolResult.fail(
                f"Invalid arguments for tool '{tool_name}': {exc}",
                error_code="INVALID_ARGUMENTS",
            )
        except Exception as exc:
            elapsed = time.monotonic() * 1000 - start_ms
            log.exception("tool_execution_error", tool=tool_name)
            audit_tool_call(
                tool_name=tool_name,
                arguments=tool_call.arguments,
                risk_level=risk,
                confirmed=confirmed,
                result_success=False,
            )
            result = ToolResult.fail(
                f"Tool '{tool_name}' raised an unexpected error: {type(exc).__name__}: {exc}",
                error_code="TOOL_ERROR",
            )
            result.execution_time_ms = round(elapsed, 2)
            return result


# Module-level singleton — imported by all tool modules to register themselves
registry = ToolRegistry()
