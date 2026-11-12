"""
Safety and permission layer.
Every tool call passes through this layer before execution.

Risk levels:
  LOW      — execute automatically (open app, read system info, search files)
  MEDIUM   — execute in balanced/power_user mode; ask in safe mode
  HIGH     — always ask for confirmation
  CRITICAL — blocked by default; requires explicit implementation + user approval
"""
from __future__ import annotations

from typing import Optional

import structlog

from app.config import PermissionMode, settings
from app.models.schemas import ConfirmationRequest, RiskLevel, ToolCall

log = structlog.get_logger(__name__)

# ── Blocked operations — NEVER execute these regardless of mode ───────────────
_BLOCKED_TOOLS: frozenset[str] = frozenset({
    "format_disk",
    "delete_partition",
    "modify_registry_destructive",
    "disable_firewall",
    "disable_antivirus",
    "escalate_privileges_arbitrary",
    "execute_arbitrary_shell",   # use controlled_shell instead
})

# ── Risk classification for each registered tool ─────────────────────────────
_TOOL_RISK: dict[str, RiskLevel] = {
    # Files — read
    "search_files":         RiskLevel.LOW,
    "get_recent_files":     RiskLevel.LOW,
    "get_downloads":        RiskLevel.LOW,
    "list_directory":       RiskLevel.LOW,
    "open_file":            RiskLevel.LOW,
    "show_in_explorer":     RiskLevel.LOW,
    "get_file_info":        RiskLevel.LOW,
    # Files — write
    "create_folder":        RiskLevel.MEDIUM,
    "rename_file":          RiskLevel.MEDIUM,
    "copy_file":            RiskLevel.MEDIUM,
    "move_file":            RiskLevel.MEDIUM,
    "delete_file":          RiskLevel.HIGH,
    "compress_files":       RiskLevel.MEDIUM,
    "extract_archive":      RiskLevel.MEDIUM,
    # Apps
    "list_installed_apps":  RiskLevel.LOW,
    "open_application":     RiskLevel.LOW,
    "close_application":    RiskLevel.MEDIUM,
    "restart_application":  RiskLevel.MEDIUM,
    "uninstall_application": RiskLevel.HIGH,
    # System info
    "get_system_info":      RiskLevel.LOW,
    "get_running_processes": RiskLevel.LOW,
    "get_startup_apps":     RiskLevel.LOW,
    "get_storage_info":     RiskLevel.LOW,
    "get_battery_status":   RiskLevel.LOW,
    # Processes
    "kill_process":         RiskLevel.HIGH,
    "close_unnecessary_apps": RiskLevel.MEDIUM,
    # Network
    "get_wifi_status":      RiskLevel.LOW,
    "list_wifi_networks":   RiskLevel.LOW,
    "connect_wifi":         RiskLevel.MEDIUM,
    "disconnect_wifi":      RiskLevel.MEDIUM,
    "get_network_info":     RiskLevel.LOW,
    "network_diagnostics":  RiskLevel.LOW,
    "restart_network_adapter": RiskLevel.HIGH,
    "flush_dns":            RiskLevel.MEDIUM,
    "renew_ip":             RiskLevel.MEDIUM,
    # Bluetooth
    "get_bluetooth_status": RiskLevel.LOW,
    "toggle_bluetooth":     RiskLevel.MEDIUM,
    # Audio
    "get_volume":           RiskLevel.LOW,
    "set_volume":           RiskLevel.LOW,
    "mute_audio":           RiskLevel.LOW,
    "unmute_audio":         RiskLevel.LOW,
    "get_audio_devices":    RiskLevel.LOW,
    # Services
    "restart_service":      RiskLevel.HIGH,
    "get_service_status":   RiskLevel.LOW,
    # PowerShell (controlled)
    "controlled_shell":     RiskLevel.HIGH,
}

# Human-readable consequences for HIGH/CRITICAL tools
_TOOL_CONSEQUENCES: dict[str, list[str]] = {
    "delete_file":          ["This file will be permanently deleted and cannot be recovered easily."],
    "uninstall_application": ["The application will be removed from your computer.", "This action may be irreversible."],
    "kill_process":         ["The process will be forcefully terminated.", "Unsaved work in that application will be lost."],
    "restart_service":      ["The Windows service will be stopped and restarted.", "This may temporarily affect system functionality."],
    "restart_network_adapter": ["Your network connection will be briefly interrupted."],
    "controlled_shell":     ["A PowerShell command will be executed on your system.", "Review the command carefully before confirming."],
    "connect_wifi":         ["AURA will connect to the specified Wi-Fi network."],
    "disconnect_wifi":      ["Your current Wi-Fi connection will be disconnected."],
}


def get_tool_risk(tool_name: str) -> RiskLevel:
    """Return the risk level for a tool. Defaults to HIGH for unknown tools."""
    return _TOOL_RISK.get(tool_name, RiskLevel.HIGH)


def is_blocked(tool_name: str) -> bool:
    """Return True if the tool is unconditionally blocked."""
    return tool_name in _BLOCKED_TOOLS


def requires_confirmation(tool_name: str, mode: Optional[PermissionMode] = None) -> bool:
    """
    Determine whether a tool call requires user confirmation in the current permission mode.
    """
    if is_blocked(tool_name):
        return True  # Will be rejected, not just confirmed

    risk = get_tool_risk(tool_name)
    permission_mode = mode or settings.permission_mode

    if risk == RiskLevel.LOW:
        return False  # Never needs confirmation

    if risk == RiskLevel.MEDIUM:
        return permission_mode == PermissionMode.SAFE

    if risk == RiskLevel.HIGH:
        return permission_mode in (PermissionMode.SAFE, PermissionMode.BALANCED)

    if risk == RiskLevel.CRITICAL:
        return True  # Always confirm critical

    return True


def build_confirmation_request(
    tool_call: ToolCall,
    action_description: str,
    target: str,
) -> ConfirmationRequest:
    """Build a ConfirmationRequest for a tool call that needs user approval."""
    risk = get_tool_risk(tool_call.tool)
    consequences = _TOOL_CONSEQUENCES.get(tool_call.tool, [])

    return ConfirmationRequest(
        action=action_description,
        target=target,
        description=f"AURA wants to execute: {tool_call.tool}",
        risk_level=risk,
        consequences=consequences,
        tool=tool_call.tool,
        arguments=tool_call.arguments,
    )


def audit_tool_call(
    tool_name: str,
    arguments: dict,
    risk_level: RiskLevel,
    confirmed: bool,
    result_success: bool,
) -> None:
    """Write a structured audit log entry for every tool execution."""
    log.info(
        "tool_executed",
        tool=tool_name,
        risk_level=risk_level.value,
        confirmed=confirmed,
        success=result_success,
        # Do NOT log argument values for HIGH/CRITICAL risk (may contain paths, names)
        arguments_keys=list(arguments.keys()) if risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL) else arguments,
    )
