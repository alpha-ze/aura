"""
Application management tools.
Launch, close, and list applications.
Uninstall requires HIGH-risk confirmation.
"""
from __future__ import annotations

import os
import subprocess
import winreg
from pathlib import Path
from typing import Optional

import psutil
import structlog

from app.agent.router import registry
from app.models.schemas import ToolResult

log = structlog.get_logger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_installed_apps_from_registry() -> list[dict]:
    """Read installed applications from the Windows registry uninstall keys."""
    apps = []
    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    for hive, path in registry_paths:
        try:
            key = winreg.OpenKey(hive, path)
        except FileNotFoundError:
            continue
        try:
            i = 0
            while True:
                try:
                    subkey_name = winreg.EnumKey(key, i)
                    i += 1
                    subkey = winreg.OpenKey(key, subkey_name)
                    try:
                        name, _ = winreg.QueryValueEx(subkey, "DisplayName")
                        if not name:
                            continue
                        entry: dict = {"name": name}
                        for field, reg_field in [
                            ("version", "DisplayVersion"),
                            ("publisher", "Publisher"),
                            ("install_date", "InstallDate"),
                            ("uninstall_string", "UninstallString"),
                        ]:
                            try:
                                val, _ = winreg.QueryValueEx(subkey, reg_field)
                                entry[field] = val
                            except FileNotFoundError:
                                pass
                        apps.append(entry)
                    except FileNotFoundError:
                        pass
                    finally:
                        winreg.CloseKey(subkey)
                except OSError:
                    break
        finally:
            winreg.CloseKey(key)

    # Deduplicate by name
    seen: set[str] = set()
    unique = []
    for app in apps:
        key_name = app["name"].lower()
        if key_name not in seen:
            seen.add(key_name)
            unique.append(app)

    return sorted(unique, key=lambda a: a["name"].lower())


# ── Tool: list_installed_apps ─────────────────────────────────────────────────

@registry.register(
    name="list_installed_apps",
    description="List applications installed on the computer.",
    parameters={"filter": "str — optional search term to filter results"},
)
async def list_installed_apps(filter: Optional[str] = None) -> ToolResult:
    try:
        apps = _get_installed_apps_from_registry()
        if filter:
            apps = [a for a in apps if filter.lower() in a["name"].lower()]

        if not apps:
            msg = f"No installed applications found matching '{filter}'." if filter else "No installed applications found."
            return ToolResult.ok(msg, data=[])

        return ToolResult.ok(f"Found {len(apps)} installed application(s).", data=apps)
    except Exception as exc:
        log.exception("list_installed_apps_error")
        return ToolResult.fail(str(exc))


# ── Tool: open_application ────────────────────────────────────────────────────

@registry.register(
    name="open_application",
    description="Launch an installed application, website, or URL by name.",
    parameters={"name": "str — app name, executable, or website (e.g. 'Chrome', 'youtube.com', 'notepad')"},
)
async def open_application(name: str) -> ToolResult:
    # ── Website / URL detection ───────────────────────────────────────────────
    # If the user says "open youtube" or "open google.com", open in browser
    _WEBSITES: dict[str, str] = {
        "youtube":      "https://www.youtube.com",
        "google":       "https://www.google.com",
        "gmail":        "https://mail.google.com",
        "github":       "https://www.github.com",
        "netflix":      "https://www.netflix.com",
        "spotify web":  "https://open.spotify.com",
        "twitter":      "https://www.twitter.com",
        "x":            "https://www.x.com",
        "facebook":     "https://www.facebook.com",
        "instagram":    "https://www.instagram.com",
        "whatsapp web": "https://web.whatsapp.com",
        "chatgpt":      "https://chat.openai.com",
        "reddit":       "https://www.reddit.com",
    }
    name_lower = name.lower().strip()

    # Direct URL
    if name_lower.startswith("http://") or name_lower.startswith("https://"):
        try:
            os.startfile(name)  # type: ignore[attr-defined]
            return ToolResult.ok(f"Opened URL: {name}")
        except Exception as exc:
            return ToolResult.fail(str(exc))

    # Known website shorthand
    if name_lower in _WEBSITES:
        url = _WEBSITES[name_lower]
        try:
            os.startfile(url)  # type: ignore[attr-defined]
            return ToolResult.ok(f"Opened {name} in your browser.", data={"url": url})
        except Exception as exc:
            return ToolResult.fail(str(exc))

    # Domain-like name (e.g. "youtube.com")
    if "." in name_lower and " " not in name_lower and len(name_lower) < 60:
        url = f"https://{name_lower}" if not name_lower.startswith("http") else name_lower
        try:
            os.startfile(url)  # type: ignore[attr-defined]
            return ToolResult.ok(f"Opened {name} in your browser.", data={"url": url})
        except Exception as exc:
            return ToolResult.fail(str(exc))

    # ── Application shorthand mappings ────────────────────────────────────────
    _SHORTHAND: dict[str, str] = {
        "chrome":          "chrome.exe",
        "google chrome":   "chrome.exe",
        "firefox":         "firefox.exe",
        "edge":            "msedge.exe",
        "microsoft edge":  "msedge.exe",
        "notepad":         "notepad.exe",
        "calculator":      "calc.exe",
        "calc":            "calc.exe",
        "explorer":        "explorer.exe",
        "file explorer":   "explorer.exe",
        "paint":           "mspaint.exe",
        "ms paint":        "mspaint.exe",
        "wordpad":         "wordpad.exe",
        "cmd":             "cmd.exe",
        "command prompt":  "cmd.exe",
        "powershell":      "powershell.exe",
        "settings":        "ms-settings:",
        "windows settings": "ms-settings:",
        "task manager":    "taskmgr.exe",
        "taskmgr":         "taskmgr.exe",
        "snipping tool":   "snippingtool.exe",
        "snip":            "snippingtool.exe",
        "powerpoint":      "POWERPNT.EXE",
        "ms powerpoint":   "POWERPNT.EXE",
        "word":            "WINWORD.EXE",
        "ms word":         "WINWORD.EXE",
        "excel":           "EXCEL.EXE",
        "ms excel":        "EXCEL.EXE",
        "outlook":         "OUTLOOK.EXE",
        "onenote":         "ONENOTE.EXE",
        "teams":           "Teams.exe",
        "microsoft teams": "Teams.exe",
        "vlc":             "vlc.exe",
        "vlc media player": "vlc.exe",
        "spotify":         "Spotify.exe",
        "discord":         "Discord.exe",
        "vscode":          "Code.exe",
        "code":            "Code.exe",
        "vs code":         "Code.exe",
        "visual studio code": "Code.exe",
        "zoom":            "Zoom.exe",
        "skype":           "Skype.exe",
        "slack":           "slack.exe",
        "telegram":        "Telegram.exe",
        "whatsapp":        "WhatsApp.exe",
        "terminal":        "wt.exe",
        "windows terminal": "wt.exe",
        "camera":          "microsoft.windows.camera:",
        "photos":          "ms-photos:",
        "maps":            "bingmaps:",
        "store":           "ms-windows-store:",
        "mail":            "outlookmail:",
    }

    executable = _SHORTHAND.get(name_lower, name)

    try:
        if executable.endswith(":"):
            # Windows URI scheme (ms-settings:, ms-photos:, etc.)
            os.startfile(executable)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(executable, shell=True)
        return ToolResult.ok(f"Launched: {name}", data={"executable": executable})
    except FileNotFoundError:
        return ToolResult.fail(
            f"Could not find '{name}'. "
            "Make sure it's installed. You can also try 'open chrome' or 'open notepad'.",
            error_code="NOT_FOUND",
        )
    except Exception as exc:
        return ToolResult.fail(str(exc))


# ── Tool: close_application ───────────────────────────────────────────────────

@registry.register(
    name="close_application",
    description="Close a running application gracefully.",
    parameters={"name": "str — application or process name (e.g. 'Chrome', 'chrome.exe')"},
)
async def close_application(name: str) -> ToolResult:
    name_lower = name.lower()
    if not name_lower.endswith(".exe"):
        name_lower_exe = name_lower + ".exe"
    else:
        name_lower_exe = name_lower

    closed = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            pname = proc.info["name"].lower()
            if pname == name_lower or pname == name_lower_exe:
                proc.terminate()
                closed.append(proc.info["name"])
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    if closed:
        return ToolResult.ok(f"Closed {closed[0]}.", data={"closed": closed})
    return ToolResult.fail(f"No running process found matching '{name}'.", error_code="NOT_FOUND")


# ── Tool: uninstall_application (HIGH risk) ───────────────────────────────────

@registry.register(
    name="uninstall_application",
    description="Uninstall an application. ALWAYS requires explicit user confirmation first.",
    parameters={"name": "str — exact application name as shown in installed apps list"},
)
async def uninstall_application(name: str) -> ToolResult:
    """
    This tool is HIGH risk and will always be intercepted by the safety layer
    for confirmation before reaching this implementation.
    """
    apps = _get_installed_apps_from_registry()
    match = next((a for a in apps if a["name"].lower() == name.lower()), None)

    if not match:
        return ToolResult.fail(
            f"Application '{name}' not found in the installed apps list. "
            "Try listing installed apps first to get the exact name.",
            error_code="NOT_FOUND",
        )

    uninstall_str = match.get("uninstall_string")
    if not uninstall_str:
        return ToolResult.fail(
            f"No uninstaller found for '{name}'. "
            "Try uninstalling it manually from Windows Settings → Apps.",
            error_code="NO_UNINSTALLER",
        )

    try:
        # Launch the uninstaller (usually opens a GUI)
        subprocess.Popen(uninstall_str, shell=True)
        return ToolResult.ok(
            f"Uninstaller launched for '{name}'. "
            "Follow the uninstaller prompts to complete removal.",
            data={"name": name},
        )
    except Exception as exc:
        return ToolResult.fail(f"Failed to launch uninstaller: {exc}")
