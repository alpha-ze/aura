"""
Bluetooth tools.
Uses PowerShell on Windows since there is no stable pure-Python
Bluetooth management API for all Windows versions.
"""
from __future__ import annotations

import subprocess

import structlog

from app.agent.router import registry
from app.models.schemas import ToolResult

log = structlog.get_logger(__name__)


def _ps(cmd: str, timeout: int = 15) -> tuple[str, int]:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
        capture_output=True, text=True, timeout=timeout,
        creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
    )
    return (result.stdout + result.stderr).strip(), result.returncode


# ── Tool: get_bluetooth_status ────────────────────────────────────────────────

@registry.register(
    name="get_bluetooth_status",
    description="Check if Bluetooth is enabled and get adapter information.",
    parameters={},
)
async def get_bluetooth_status() -> ToolResult:
    try:
        # Check for Bluetooth radio via WMI
        out, rc = _ps(
            "Get-WmiObject -Query 'SELECT * FROM Win32_SystemDriver WHERE Name LIKE \"%bthport%\"'"
            " | Select-Object Name, State | ConvertTo-Json -Compress"
        )

        # Also check via device manager
        out2, _ = _ps(
            "Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue"
            " | Select-Object Name, Status | ConvertTo-Json -Compress"
        )

        if not out and not out2:
            return ToolResult.ok(
                "No Bluetooth adapter detected. This device may not have Bluetooth hardware.",
                data={"adapter_found": False},
            )

        data = {
            "adapter_found": True,
            "driver_info": out,
            "devices": out2,
        }

        # Try to determine enabled state
        out3, _ = _ps(
            "(Get-Service -Name 'bthserv' -ErrorAction SilentlyContinue).Status"
        )
        enabled = "running" in out3.lower() if out3 else None
        data["service_running"] = enabled

        status = "enabled" if enabled else ("disabled" if enabled is False else "unknown")
        return ToolResult.ok(f"Bluetooth adapter found — service: {status}", data=data)

    except Exception as exc:
        return ToolResult.fail(str(exc))


# ── Tool: toggle_bluetooth (MEDIUM risk) ─────────────────────────────────────

@registry.register(
    name="toggle_bluetooth",
    description="Enable or disable Bluetooth. May require admin rights on some systems.",
    parameters={"enable": "bool — True to enable, False to disable"},
)
async def toggle_bluetooth(enable: bool) -> ToolResult:
    action = "Start" if enable else "Stop"
    action_word = "enabled" if enable else "disabled"

    try:
        # Control the Bluetooth Support Service
        out, rc = _ps(
            f"{action}-Service -Name 'bthserv' -ErrorAction Stop"
        )
        if rc == 0:
            return ToolResult.ok(f"Bluetooth service {action_word}.", data={"enabled": enable})

        # Try device enable/disable via PnP
        method = "Enable" if enable else "Disable"
        out2, rc2 = _ps(
            f"Get-PnpDevice -Class Bluetooth -ErrorAction SilentlyContinue"
            f" | {method}-PnpDevice -Confirm:$false -ErrorAction Stop"
        )
        if rc2 == 0:
            return ToolResult.ok(f"Bluetooth {action_word}.", data={"enabled": enable})

        return ToolResult.fail(
            f"Could not {action.lower()} Bluetooth. "
            "This may require administrator privileges. "
            "Try toggling from Windows Settings → Bluetooth & devices.",
            error_code="PERMISSION_REQUIRED",
        )
    except subprocess.TimeoutExpired:
        return ToolResult.fail("Bluetooth operation timed out.")
    except Exception as exc:
        return ToolResult.fail(str(exc))


# ── Tool: restart_service (HIGH risk) ────────────────────────────────────────

@registry.register(
    name="restart_service",
    description="Restart a Windows service by name. Requires confirmation.",
    parameters={"name": "str — Windows service name (e.g. 'WlanSvc', 'AudioSrv')"},
)
async def restart_service(name: str) -> ToolResult:
    # Whitelist of safe-to-restart services
    _ALLOWED_SERVICES = {
        "wlansvc", "audiosrv", "audioendpointbuilder",
        "bthserv", "dhcp", "dnscache", "wscsvc",
        "netlogon", "spooler", "w32tm",
    }

    if name.lower() not in _ALLOWED_SERVICES:
        return ToolResult.fail(
            f"Service '{name}' is not in the allowed restart list. "
            f"Allowed: {', '.join(sorted(_ALLOWED_SERVICES))}",
            error_code="SERVICE_NOT_ALLOWED",
        )

    try:
        # Validate service name - no shell injection possible here
        # because we pass as PowerShell argument string, not via shell=True
        out, rc = _ps(
            f"Restart-Service -Name '{name}' -Force -ErrorAction Stop",
            timeout=30,
        )
        if rc == 0:
            return ToolResult.ok(f"Service '{name}' restarted successfully.")
        return ToolResult.fail(
            f"Failed to restart service '{name}': {out}",
            error_code="SERVICE_RESTART_FAILED",
        )
    except subprocess.TimeoutExpired:
        return ToolResult.fail(f"Service restart timed out for '{name}'.")
    except Exception as exc:
        return ToolResult.fail(str(exc))
