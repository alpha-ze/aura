"""
Agent planner — converts an AI response containing tool calls into
an ordered execution plan, validates each step, and tracks progress.
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional
from uuid import uuid4

import structlog

from app.models.schemas import AgentPlan, PlanStep, ToolCall

log = structlog.get_logger(__name__)

# Pattern to extract JSON tool calls from model output
# Supports both bare JSON and markdown code blocks
_JSON_BLOCK_RE = re.compile(
    r"```(?:json)?\s*(\{.*?\})\s*```|(\{[^{}]*\"tool\"\s*:[^{}]*\})",
    re.DOTALL | re.IGNORECASE,
)


def extract_tool_calls(text: str) -> list[ToolCall]:
    """
    Parse tool call JSON objects from model output text.
    Extracts all JSON objects that contain a "tool" key.
    Returns validated ToolCall objects; skips malformed entries with a warning.
    """
    tool_calls: list[ToolCall] = []

    for match in _JSON_BLOCK_RE.finditer(text):
        raw = match.group(1) or match.group(2)
        if not raw:
            continue
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and "tool" in data:
                tc = ToolCall.model_validate(data)
                tool_calls.append(tc)
        except (json.JSONDecodeError, ValueError) as exc:
            log.warning("tool_call_parse_failed", raw=raw[:200], error=str(exc))

    return tool_calls


def build_plan(tool_calls: list[ToolCall]) -> AgentPlan:
    """Create an AgentPlan from a list of ToolCall objects."""
    steps = [
        PlanStep(
            id=str(uuid4()),
            description=_describe_tool_call(tc),
            tool=tc.tool,
            status="pending",
        )
        for tc in tool_calls
    ]
    return AgentPlan(steps=steps, status="pending" if steps else "completed")


def _describe_tool_call(tc: ToolCall) -> str:
    """Generate a human-readable description for a tool call."""
    descriptions: dict[str, str] = {
        "search_files":         "Search for files",
        "open_file":            f"Open file: {tc.arguments.get('path', '')}",
        "rename_file":          f"Rename file to: {tc.arguments.get('new_name', '')}",
        "move_file":            f"Move file to: {tc.arguments.get('destination', '')}",
        "copy_file":            f"Copy file",
        "delete_file":          f"Delete: {tc.arguments.get('path', '')}",
        "create_folder":        f"Create folder: {tc.arguments.get('name', '')}",
        "open_application":     f"Open application: {tc.arguments.get('name', '')}",
        "close_application":    f"Close application: {tc.arguments.get('name', '')}",
        "uninstall_application": f"Uninstall: {tc.arguments.get('name', '')}",
        "get_system_info":      "Get system information",
        "get_running_processes": "Get running processes",
        "get_wifi_status":      "Check Wi-Fi status",
        "list_wifi_networks":   "List available Wi-Fi networks",
        "connect_wifi":         f"Connect to Wi-Fi: {tc.arguments.get('ssid', '')}",
        "set_volume":           f"Set volume to {tc.arguments.get('level', '')}%",
        "get_volume":           "Get current volume",
        "get_bluetooth_status": "Check Bluetooth status",
        "toggle_bluetooth":     "Toggle Bluetooth",
        "network_diagnostics":  "Run network diagnostics",
        "restart_service":      f"Restart service: {tc.arguments.get('name', '')}",
        "kill_process":         f"Terminate process: {tc.arguments.get('name', '')}",
    }
    return descriptions.get(tc.tool, f"Execute: {tc.tool}")
