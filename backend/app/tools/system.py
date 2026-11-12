"""
System information and process management tools.
Uses psutil for cross-version compatibility.
"""
from __future__ import annotations

import platform
import socket
from datetime import datetime, timezone
from typing import Optional

import psutil
import structlog

from app.agent.router import registry
from app.models.schemas import ToolResult

log = structlog.get_logger(__name__)


# ── Tool: get_system_info ─────────────────────────────────────────────────────

@registry.register(
    name="get_system_info",
    description="Get comprehensive system information: CPU, RAM, disk, battery, OS details.",
    parameters={},
)
async def get_system_info() -> ToolResult:
    try:
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_count = psutil.cpu_count(logical=True) or 1

        ram = psutil.virtual_memory()
        ram_total_gb = round(ram.total / 1e9, 1)
        ram_used_gb  = round(ram.used / 1e9, 1)
        ram_percent  = ram.percent

        disk = psutil.disk_usage("/")
        disk_total_gb = round(disk.total / 1e9, 1)
        disk_used_gb  = round(disk.used / 1e9, 1)
        disk_free_gb  = round(disk.free / 1e9, 1)
        disk_percent  = disk.percent

        battery = psutil.sensors_battery()
        battery_percent = round(battery.percent, 1) if battery else None
        battery_plugged = battery.power_plugged if battery else None

        uptime_seconds = psutil.boot_time()
        boot_dt = datetime.fromtimestamp(uptime_seconds, tz=timezone.utc)
        uptime_secs = (datetime.now(tz=timezone.utc) - boot_dt).total_seconds()

        uname = platform.uname()
        win_ver = platform.version()

        data = {
            "cpu_percent": cpu_percent,
            "cpu_count": cpu_count,
            "ram_total_gb": ram_total_gb,
            "ram_used_gb": ram_used_gb,
            "ram_percent": ram_percent,
            "disk_total_gb": disk_total_gb,
            "disk_used_gb": disk_used_gb,
            "disk_free_gb": disk_free_gb,
            "disk_percent": disk_percent,
            "battery_percent": battery_percent,
            "battery_plugged": battery_plugged,
            "platform": uname.system,
            "windows_version": win_ver,
            "hostname": socket.gethostname(),
            "uptime_seconds": round(uptime_secs),
            "architecture": uname.machine,
        }

        summary = (
            f"CPU: {cpu_percent}% | RAM: {ram_used_gb}/{ram_total_gb} GB ({ram_percent}%) | "
            f"Disk: {disk_free_gb} GB free | "
            + (f"Battery: {battery_percent}%{'⚡' if battery_plugged else '🔋'}" if battery else "No battery")
        )

        return ToolResult.ok(summary, data=data)
    except Exception as exc:
        log.exception("get_system_info_error")
        return ToolResult.fail(str(exc))


# ── Tool: get_storage_info ────────────────────────────────────────────────────

@registry.register(
    name="get_storage_info",
    description="Get detailed storage information for all drives.",
    parameters={},
)
async def get_storage_info() -> ToolResult:
    try:
        partitions = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                partitions.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "fstype": part.fstype,
                    "total_gb": round(usage.total / 1e9, 1),
                    "used_gb": round(usage.used / 1e9, 1),
                    "free_gb": round(usage.free / 1e9, 1),
                    "percent": usage.percent,
                })
            except PermissionError:
                continue

        msg = " | ".join(
            f"{p['device']} {p['free_gb']}GB free ({p['percent']}% used)"
            for p in partitions
        )
        return ToolResult.ok(msg or "No storage information available.", data=partitions)
    except Exception as exc:
        return ToolResult.fail(str(exc))


# ── Tool: get_running_processes ───────────────────────────────────────────────

@registry.register(
    name="get_running_processes",
    description="List currently running processes with CPU and memory usage.",
    parameters={"top_n": "int — number of top processes by memory to return (default 15)"},
)
async def get_running_processes(top_n: int = 15) -> ToolResult:
    try:
        procs = []
        for proc in psutil.process_iter(["pid", "name", "cpu_percent", "memory_info", "status"]):
            try:
                info = proc.info
                mem_mb = round((info["memory_info"].rss if info["memory_info"] else 0) / 1e6, 1)
                procs.append({
                    "pid": info["pid"],
                    "name": info["name"],
                    "cpu_percent": info["cpu_percent"],
                    "memory_mb": mem_mb,
                    "status": info["status"],
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by memory descending
        procs.sort(key=lambda p: p["memory_mb"], reverse=True)
        top = procs[:top_n]

        total_processes = len(procs)
        top_ram = top[0] if top else None
        msg = f"{total_processes} processes running."
        if top_ram:
            msg += f" Highest RAM: {top_ram['name']} ({top_ram['memory_mb']} MB)."

        return ToolResult.ok(msg, data={"processes": top, "total_count": total_processes})
    except Exception as exc:
        return ToolResult.fail(str(exc))


# ── Tool: get_battery_status ──────────────────────────────────────────────────

@registry.register(
    name="get_battery_status",
    description="Get battery percentage and charging status.",
    parameters={},
)
async def get_battery_status() -> ToolResult:
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return ToolResult.ok("No battery detected — this appears to be a desktop PC.", data=None)
        data = {
            "percent": round(battery.percent, 1),
            "plugged": battery.power_plugged,
            "seconds_left": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None,
        }
        status = "charging ⚡" if battery.power_plugged else "on battery 🔋"
        msg = f"Battery: {data['percent']}% — {status}"
        if data["seconds_left"]:
            mins = data["seconds_left"] // 60
            msg += f" (~{mins // 60}h {mins % 60}m remaining)"
        return ToolResult.ok(msg, data=data)
    except Exception as exc:
        return ToolResult.fail(str(exc))


# ── Tool: kill_process (HIGH risk) ────────────────────────────────────────────

@registry.register(
    name="kill_process",
    description="Forcefully terminate a running process. Requires confirmation.",
    parameters={
        "name": "str — process name (e.g. 'chrome.exe') OR",
        "pid": "int — process ID",
    },
)
async def kill_process(
    name: Optional[str] = None,
    pid: Optional[int] = None,
) -> ToolResult:
    if not name and not pid:
        return ToolResult.fail("Provide either a process name or PID.", error_code="INVALID_ARGUMENTS")

    killed = []
    errors = []

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            info = proc.info
            match = (pid and info["pid"] == pid) or (
                name and info["name"].lower() == name.lower()
            )
            if match:
                proc.terminate()
                killed.append(f"{info['name']} (PID {info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied) as exc:
            errors.append(str(exc))

    if killed:
        return ToolResult.ok(f"Terminated: {', '.join(killed)}", data={"killed": killed})
    elif errors:
        return ToolResult.fail(f"Could not terminate process: {'; '.join(errors)}", error_code="ACCESS_DENIED")
    else:
        return ToolResult.fail(f"No matching process found.", error_code="NOT_FOUND")


# ── Tool: close_unnecessary_apps (MEDIUM risk) ───────────────────────────────

@registry.register(
    name="close_unnecessary_apps",
    description="Close background applications that are not commonly needed during presentations or focused work.",
    parameters={
        "keep": "list[str] — process names to keep open (e.g. ['chrome.exe', 'code.exe'])",
    },
)
async def close_unnecessary_apps(keep: Optional[list[str]] = None) -> ToolResult:
    # Known background processes that are safe to close when asked
    _CLOSEABLE = {
        "discord.exe", "spotify.exe", "slack.exe", "teams.exe",
        "zoom.exe", "skype.exe", "onedrive.exe",
    }
    keep_lower = {k.lower() for k in (keep or [])}
    targets = _CLOSEABLE - keep_lower

    closed = []
    skipped = []

    for proc in psutil.process_iter(["pid", "name"]):
        try:
            pname = proc.info["name"].lower()
            if pname in targets:
                proc.terminate()
                closed.append(proc.info["name"])
            elif pname in keep_lower:
                skipped.append(proc.info["name"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    msg = f"Closed {len(closed)} background app(s)."
    if skipped:
        msg += f" Kept open: {', '.join(set(skipped))}."
    if not closed:
        msg = "No closeable background applications were running."

    return ToolResult.ok(msg, data={"closed": closed, "kept": list(set(skipped))})
