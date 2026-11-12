"""
Audio tools — volume control, device enumeration, microphone test.
Uses pycaw (Windows Core Audio API) with PowerShell fallback.
"""
from __future__ import annotations

import subprocess
from typing import Optional

import structlog

from app.agent.router import registry
from app.models.schemas import ToolResult

log = structlog.get_logger(__name__)


def _ps_run(command: str, timeout: int = 10) -> tuple[str, int]:
    """Run a PowerShell command and return (output, returncode)."""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True, text=True, timeout=timeout,
        creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
    )
    return (result.stdout + result.stderr).strip(), result.returncode


# ── Tool: get_volume ──────────────────────────────────────────────────────────

@registry.register(
    name="get_volume",
    description="Get the current system audio volume level.",
    parameters={},
)
async def get_volume() -> ToolResult:
    try:
        # Try pycaw first (native Windows Core Audio)
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # type: ignore
        from comtypes import CLSCTX_ALL  # type: ignore

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_obj = interface.QueryInterface(IAudioEndpointVolume)
        level = volume_obj.GetMasterVolumeLevelScalar()
        muted = volume_obj.GetMute()
        percent = round(level * 100)

        status = "muted" if muted else f"{percent}%"
        return ToolResult.ok(f"Volume: {status}", data={"percent": percent, "muted": bool(muted)})

    except ImportError:
        pass
    except Exception as exc:
        log.warning("pycaw_get_volume_failed", error=str(exc))

    # PowerShell fallback
    try:
        out, _ = _ps_run(
            "(Get-AudioDevice -Playback).DefaultPlaybackDevice | "
            "ForEach-Object { $_.Volume }"
        )
        if out.strip().isdigit():
            return ToolResult.ok(f"Volume: {out.strip()}%", data={"percent": int(out.strip())})

        # Simpler fallback via WMI
        out2, _ = _ps_run("[math]::Round((Get-WmiObject -Query 'SELECT * FROM Win32_SoundDevice').MaxVoiceVolume)")
        return ToolResult.ok("Volume information retrieved.", data={"raw": out2})
    except Exception as exc:
        return ToolResult.fail(f"Could not retrieve volume: {exc}")


# ── Tool: set_volume ──────────────────────────────────────────────────────────

@registry.register(
    name="set_volume",
    description="Set the system audio volume to a specific level (0–100).",
    parameters={"level": "int — volume level 0 to 100"},
)
async def set_volume(level: int) -> ToolResult:
    if not 0 <= level <= 100:
        return ToolResult.fail("Volume must be between 0 and 100.", error_code="INVALID_ARGUMENTS")

    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # type: ignore
        from comtypes import CLSCTX_ALL  # type: ignore

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_obj = interface.QueryInterface(IAudioEndpointVolume)
        volume_obj.SetMasterVolumeLevelScalar(level / 100, None)

        return ToolResult.ok(f"Volume set to {level}%", data={"percent": level})

    except ImportError:
        pass
    except Exception as exc:
        log.warning("pycaw_set_volume_failed", error=str(exc))

    # PowerShell fallback via NirCmd or built-in SendKeys
    try:
        # Use the Windows scripting host to set volume via PowerShell
        ps_cmd = f"""
$vol = {level} / 100.0
$wshShell = New-Object -ComObject WScript.Shell
Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {{
    int f(); int g(); int h(); int i();
    int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext);
    int j();
    int GetMasterVolumeLevelScalar(out float pfLevel);
    int k(); int l(); int m(); int n();
    int SetMute([MarshalAs(UnmanagedType.Bool)] bool bMute, System.Guid pguidEventContext);
    int GetMute(out bool pbMute);
}}
[Guid("D666063F-1587-4E43-81F1-B948E807363F"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDevice {{
    int Activate([MarshalAs(UnmanagedType.LPStruct)] System.Guid iid, uint dwClsCtx, System.IntPtr pActivationParams, [MarshalAs(UnmanagedType.IUnknown)] out object ppInterface);
}}
'@
"""
        # Simpler approach: use nircmd if available, otherwise accept limitation
        nircmd_result = subprocess.run(
            ["nircmd.exe", "setsysvolume", str(int(level * 655.35))],
            capture_output=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
        )
        if nircmd_result.returncode == 0:
            return ToolResult.ok(f"Volume set to {level}%", data={"percent": level})
    except FileNotFoundError:
        pass
    except Exception:
        pass

    return ToolResult.fail(
        "Could not set volume. Install pycaw: pip install pycaw, or install nircmd.",
        error_code="DEPENDENCY_MISSING",
    )


# ── Tool: mute_audio ──────────────────────────────────────────────────────────

@registry.register(
    name="mute_audio",
    description="Mute the system audio output.",
    parameters={},
)
async def mute_audio() -> ToolResult:
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # type: ignore
        from comtypes import CLSCTX_ALL  # type: ignore

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_obj = interface.QueryInterface(IAudioEndpointVolume)
        volume_obj.SetMute(True, None)
        return ToolResult.ok("Audio muted.")
    except ImportError:
        return ToolResult.fail("pycaw not installed. Run: pip install pycaw", error_code="DEPENDENCY_MISSING")
    except Exception as exc:
        return ToolResult.fail(str(exc))


# ── Tool: unmute_audio ────────────────────────────────────────────────────────

@registry.register(
    name="unmute_audio",
    description="Unmute the system audio output.",
    parameters={},
)
async def unmute_audio() -> ToolResult:
    try:
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # type: ignore
        from comtypes import CLSCTX_ALL  # type: ignore

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        volume_obj = interface.QueryInterface(IAudioEndpointVolume)
        volume_obj.SetMute(False, None)
        return ToolResult.ok("Audio unmuted.")
    except ImportError:
        return ToolResult.fail("pycaw not installed. Run: pip install pycaw", error_code="DEPENDENCY_MISSING")
    except Exception as exc:
        return ToolResult.fail(str(exc))


# ── Tool: get_audio_devices ───────────────────────────────────────────────────

@registry.register(
    name="get_audio_devices",
    description="List available audio input and output devices.",
    parameters={},
)
async def get_audio_devices() -> ToolResult:
    try:
        from pycaw.pycaw import AudioUtilities  # type: ignore

        speakers = AudioUtilities.GetAllSpeakers()
        microphones = AudioUtilities.GetAllMicrophones() if hasattr(AudioUtilities, "GetAllMicrophones") else []

        devices = {
            "speakers": [str(s) for s in speakers],
            "microphones": [str(m) for m in microphones],
        }
        msg = f"Found {len(devices['speakers'])} speaker(s) and {len(devices['microphones'])} microphone(s)."
        return ToolResult.ok(msg, data=devices)
    except ImportError:
        # PowerShell fallback
        try:
            out, _ = _ps_run(
                "Get-WmiObject Win32_SoundDevice | Select-Object Name, Status | ConvertTo-Json"
            )
            return ToolResult.ok("Audio devices retrieved.", data={"raw": out})
        except Exception as exc:
            return ToolResult.fail(str(exc))
    except Exception as exc:
        return ToolResult.fail(str(exc))
