"""
Network and Wi-Fi tools.
Uses subprocess + netsh on Windows for Wi-Fi operations.
"""
from __future__ import annotations

import ipaddress
import re
import socket
import subprocess
from typing import Optional

import psutil
import structlog

from app.agent.router import registry
from app.models.schemas import ToolResult

log = structlog.get_logger(__name__)


def _run_netsh(*args: str, timeout: int = 10) -> tuple[str, str]:
    """Run a netsh command and return (stdout, stderr)."""
    result = subprocess.run(
        ["netsh", *args],
        capture_output=True, text=True, timeout=timeout,
        creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
    )
    return result.stdout, result.stderr


# ── Tool: get_wifi_status ─────────────────────────────────────────────────────

@registry.register(
    name="get_wifi_status",
    description="Get current Wi-Fi connection status, SSID, IP address, and signal.",
    parameters={},
)
async def get_wifi_status() -> ToolResult:
    try:
        stdout, _ = _run_netsh("wlan", "show", "interfaces")
        data: dict = {"connected": False}

        if "State" in stdout:
            state_match = re.search(r"State\s*:\s*(.+)", stdout)
            ssid_match  = re.search(r"SSID\s*:\s*(.+)", stdout)
            signal_match = re.search(r"Signal\s*:\s*(\d+)%", stdout)
            bssid_match = re.search(r"BSSID\s*:\s*(.+)", stdout)

            if state_match:
                state = state_match.group(1).strip()
                data["adapter_status"] = state
                data["connected"] = state.lower() == "connected"
            if ssid_match:
                data["ssid"] = ssid_match.group(1).strip()
            if signal_match:
                data["signal_strength"] = int(signal_match.group(1))
            if bssid_match:
                data["bssid"] = bssid_match.group(1).strip()

        # Get IP info from psutil
        for iface_name, addrs in psutil.net_if_addrs().items():
            if "wi-fi" in iface_name.lower() or "wireless" in iface_name.lower() or "wlan" in iface_name.lower():
                for addr in addrs:
                    if addr.family == socket.AF_INET:
                        data["ip_address"] = addr.address
                        data["netmask"] = addr.netmask
                        data["adapter_name"] = iface_name

        # Check internet connectivity
        try:
            socket.setdefaulttimeout(3)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            data["internet_accessible"] = True
        except OSError:
            data["internet_accessible"] = False

        if data["connected"]:
            ssid = data.get("ssid", "unknown network")
            signal = data.get("signal_strength", "?")
            ip = data.get("ip_address", "unknown IP")
            internet = "✓ internet" if data.get("internet_accessible") else "✗ no internet"
            msg = f"Connected to '{ssid}' — Signal: {signal}% — IP: {ip} — {internet}"
        else:
            msg = "Wi-Fi is not connected."

        return ToolResult.ok(msg, data=data)
    except Exception as exc:
        log.exception("get_wifi_status_error")
        return ToolResult.fail(str(exc))


# ── Tool: list_wifi_networks ──────────────────────────────────────────────────

@registry.register(
    name="list_wifi_networks",
    description="List available Wi-Fi networks nearby.",
    parameters={},
)
async def list_wifi_networks() -> ToolResult:
    try:
        stdout, _ = _run_netsh("wlan", "show", "networks", "mode=bssid", timeout=15)
        networks = []
        current: dict = {}

        for line in stdout.splitlines():
            line = line.strip()
            if line.startswith("SSID") and "BSSID" not in line:
                if current:
                    networks.append(current)
                    current = {}
                match = re.match(r"SSID\s+\d+\s*:\s*(.*)", line)
                if match:
                    current["ssid"] = match.group(1).strip()
            elif "Authentication" in line:
                match = re.search(r":\s*(.+)", line)
                if match:
                    current["security"] = match.group(1).strip()
            elif "Signal" in line:
                match = re.search(r":\s*(\d+)%", line)
                if match:
                    current["signal"] = int(match.group(1))
        if current:
            networks.append(current)

        networks = [n for n in networks if n.get("ssid")]
        networks.sort(key=lambda n: n.get("signal", 0), reverse=True)

        if not networks:
            return ToolResult.ok("No Wi-Fi networks found nearby.", data=[])

        return ToolResult.ok(f"Found {len(networks)} Wi-Fi network(s) nearby.", data=networks)
    except Exception as exc:
        return ToolResult.fail(str(exc))


# ── Tool: get_network_info ────────────────────────────────────────────────────

@registry.register(
    name="get_network_info",
    description="Get IP address, gateway, DNS, and adapter information.",
    parameters={},
)
async def get_network_info() -> ToolResult:
    try:
        adapters = []
        for name, addrs in psutil.net_if_addrs().items():
            adapter_info: dict = {"name": name, "addresses": []}
            stats = psutil.net_if_stats().get(name)
            if stats:
                adapter_info["is_up"] = stats.isup
                adapter_info["speed_mbps"] = stats.speed
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    adapter_info["ipv4"] = addr.address
                    adapter_info["netmask"] = addr.netmask
                elif addr.family == socket.AF_INET6:
                    adapter_info["ipv6"] = addr.address.split("%")[0]
            adapters.append(adapter_info)

        # Get default gateway
        stdout, _ = _run_netsh("interface", "ip", "show", "config")
        gateways = re.findall(r"Default Gateway\s*:\s*([\d.]+)", stdout)
        dns_servers = re.findall(r"DNS Servers\s*:\s*([\d.]+)", stdout)

        result = {
            "adapters": adapters,
            "default_gateway": gateways[0] if gateways else None,
            "dns_servers": list(set(dns_servers)),
        }

        connected_adapters = [a for a in adapters if a.get("is_up") and a.get("ipv4")]
        summary = f"{len(connected_adapters)} active adapter(s)."
        if result["default_gateway"]:
            summary += f" Gateway: {result['default_gateway']}."

        return ToolResult.ok(summary, data=result)
    except Exception as exc:
        return ToolResult.fail(str(exc))


# ── Tool: network_diagnostics ─────────────────────────────────────────────────

@registry.register(
    name="network_diagnostics",
    description="Run a full network connectivity diagnostic: adapter, IP, gateway ping, DNS, internet.",
    parameters={},
)
async def network_diagnostics() -> ToolResult:
    results: dict = {}
    issues: list[str] = []

    # Step 1: Check adapter
    wifi_result = await get_wifi_status()
    results["wifi"] = wifi_result.data

    if not (wifi_result.data or {}).get("connected"):
        issues.append("Wi-Fi adapter is not connected to a network.")

    # Step 2: Check IP
    ip = (wifi_result.data or {}).get("ip_address")
    if ip:
        results["ip_address"] = ip
        if ip.startswith("169.254"):
            issues.append("IP address is a link-local address (169.254.x.x) — DHCP may have failed.")
    else:
        issues.append("No IP address assigned.")

    # Step 3: Ping gateway
    net_info = await get_network_info()
    gateway = (net_info.data or {}).get("default_gateway")
    if gateway:
        ping_result = subprocess.run(
            ["ping", "-n", "2", "-w", "2000", gateway],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
        )
        gateway_reachable = ping_result.returncode == 0
        results["gateway_ping"] = gateway_reachable
        if not gateway_reachable:
            issues.append(f"Cannot reach gateway ({gateway}). Router may be offline.")
    else:
        issues.append("No default gateway found.")
        gateway_reachable = False

    # Step 4: DNS resolution
    try:
        socket.getaddrinfo("google.com", 80, proto=socket.IPPROTO_TCP)
        results["dns_resolution"] = True
    except socket.gaierror:
        results["dns_resolution"] = False
        issues.append("DNS resolution failed. Try flushing DNS cache.")

    # Step 5: Internet ping
    try:
        ping_internet = subprocess.run(
            ["ping", "-n", "2", "-w", "3000", "8.8.8.8"],
            capture_output=True, text=True, timeout=12,
            creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
        )
        results["internet_reachable"] = ping_internet.returncode == 0
        if not results["internet_reachable"]:
            issues.append("Cannot reach internet (8.8.8.8). ISP or modem may be down.")
    except Exception:
        results["internet_reachable"] = False
        issues.append("Internet ping test failed.")

    if not issues:
        msg = "✓ Network looks healthy. All diagnostics passed."
    else:
        msg = "⚠ Network issues detected:\n" + "\n".join(f"• {i}" for i in issues)

    return ToolResult.ok(msg, data={**results, "issues": issues})


# ── Tool: flush_dns (MEDIUM risk) ─────────────────────────────────────────────

@registry.register(
    name="flush_dns",
    description="Flush the Windows DNS cache.",
    parameters={},
)
async def flush_dns() -> ToolResult:
    try:
        result = subprocess.run(
            ["ipconfig", "/flushdns"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
        )
        if result.returncode == 0:
            return ToolResult.ok("DNS cache flushed successfully.")
        return ToolResult.fail(f"DNS flush failed: {result.stderr}", error_code="FLUSH_FAILED")
    except Exception as exc:
        return ToolResult.fail(str(exc))


# ── Tool: connect_wifi (MEDIUM risk) ─────────────────────────────────────────

@registry.register(
    name="connect_wifi",
    description="Connect to a Wi-Fi network. Only works for previously saved networks.",
    parameters={"ssid": "str — network SSID to connect to"},
)
async def connect_wifi(ssid: str) -> ToolResult:
    # Sanitise SSID
    if any(c in ssid for c in ("|", "&", ";", "`", "$", "\n", "\r")):
        return ToolResult.fail("Invalid SSID characters.", error_code="INVALID_INPUT")

    try:
        result = subprocess.run(
            ["netsh", "wlan", "connect", f"name={ssid}"],
            capture_output=True, text=True, timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
        )
        if result.returncode == 0 and "completed successfully" in result.stdout.lower():
            return ToolResult.ok(f"Connecting to '{ssid}'…")
        return ToolResult.fail(
            f"Could not connect to '{ssid}'. "
            "The network may not be in your saved profiles. "
            "Connect manually from Windows Wi-Fi settings first.",
            error_code="CONNECT_FAILED",
        )
    except Exception as exc:
        return ToolResult.fail(str(exc))


# ── Tool: disconnect_wifi (MEDIUM risk) ──────────────────────────────────────

@registry.register(
    name="disconnect_wifi",
    description="Disconnect from the current Wi-Fi network.",
    parameters={},
)
async def disconnect_wifi() -> ToolResult:
    try:
        result = subprocess.run(
            ["netsh", "wlan", "disconnect"],
            capture_output=True, text=True, timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
        )
        if result.returncode == 0:
            return ToolResult.ok("Disconnected from Wi-Fi.")
        return ToolResult.fail("Failed to disconnect from Wi-Fi.", error_code="DISCONNECT_FAILED")
    except Exception as exc:
        return ToolResult.fail(str(exc))
