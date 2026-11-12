"""
Path validation and sanitisation.
Prevents path traversal attacks and restricts operations to safe locations.
"""
from __future__ import annotations

import os
from pathlib import Path, PureWindowsPath
from typing import Optional

import structlog

log = structlog.get_logger(__name__)

# Directories that AURA is allowed to operate in by default
# (expanduser called at import time — safe because this runs locally)
_ALLOWED_ROOTS: list[Path] = [
    Path.home(),                          # C:\Users\<user>
    Path("C:/Users/Public"),
]

# Directories that are always forbidden regardless of permission mode
_FORBIDDEN_PATHS: list[str] = [
    "C:\\Windows",
    "C:\\Windows\\System32",
    "C:\\Windows\\SysWOW64",
    "C:\\Program Files\\Windows Defender",
    "C:\\ProgramData\\Microsoft\\Windows Defender",
]

# File extensions that AURA will never open/execute automatically
_DANGEROUS_EXTENSIONS: frozenset[str] = frozenset({
    ".exe", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".jse",
    ".wsf", ".wsh", ".msi", ".msp", ".reg", ".inf",
    ".scr", ".pif", ".com", ".dll", ".sys", ".drv",
})


class PathValidationError(ValueError):
    """Raised when a path fails security validation."""


def resolve_safe_path(raw_path: str) -> Path:
    """
    Resolve a raw path string to an absolute Path, expanding user shortcuts
    like ~ and environment variable shortcuts like Desktop/Downloads.

    Raises PathValidationError on any suspicious input.
    """
    if not raw_path or not isinstance(raw_path, str):
        raise PathValidationError("Path must be a non-empty string.")

    # Check for null bytes (common injection vector)
    if "\x00" in raw_path:
        raise PathValidationError("Path contains null bytes.")

    # Expand well-known shorthand names
    home = Path.home()
    shortcuts: dict[str, Path] = {
        "desktop":   home / "Desktop",
        "documents": home / "Documents",
        "downloads": home / "Downloads",
        "pictures":  home / "Pictures",
        "videos":    home / "Videos",
        "music":     home / "Music",
        "~":         home,
    }
    lower = raw_path.lower().strip("/\\").strip()
    if lower in shortcuts:
        return shortcuts[lower]

    # Expand ~ and env vars
    expanded = os.path.expandvars(os.path.expanduser(raw_path))

    try:
        resolved = Path(expanded).resolve()
    except (ValueError, OSError) as exc:
        raise PathValidationError(f"Cannot resolve path: {exc}") from exc

    return resolved


def validate_path(path: Path | str, *, allow_nonexistent: bool = False) -> Path:
    """
    Validate a Path for safety:
      - Must be absolute
      - Must not contain traversal sequences
      - Must not point to a forbidden system directory
      - If allow_nonexistent=False, must exist on disk

    Returns the resolved Path on success, raises PathValidationError otherwise.
    """
    if isinstance(path, str):
        path = resolve_safe_path(path)

    path = path.resolve()

    # Check for traversal in the string form
    path_str = str(path)
    if ".." in path_str:
        raise PathValidationError(f"Path traversal detected: {path_str!r}")

    # Check against forbidden system paths
    for forbidden in _FORBIDDEN_PATHS:
        try:
            path.relative_to(Path(forbidden))
            raise PathValidationError(
                f"Access to system path is not permitted: {path_str!r}"
            )
        except ValueError:
            pass  # Not a subpath — good

    # Check existence if required
    if not allow_nonexistent and not path.exists():
        raise PathValidationError(f"Path does not exist: {path_str!r}")

    log.debug("path_validated", path=path_str)
    return path


def is_dangerous_extension(path: Path | str) -> bool:
    """Return True if the file extension is in the dangerous set."""
    p = Path(path)
    return p.suffix.lower() in _DANGEROUS_EXTENSIONS


def validate_filename(name: str) -> str:
    """
    Validate a bare filename (no directory).
    Rejects names with path separators, null bytes, or Windows reserved names.
    """
    if not name or not isinstance(name, str):
        raise PathValidationError("Filename must be a non-empty string.")

    if "\x00" in name:
        raise PathValidationError("Filename contains null bytes.")

    if any(c in name for c in r'/\:*?"<>|'):
        raise PathValidationError(
            f"Filename contains illegal characters: {name!r}"
        )

    # Windows reserved device names
    reserved = {
        "CON", "PRN", "AUX", "NUL",
        "COM1","COM2","COM3","COM4","COM5","COM6","COM7","COM8","COM9",
        "LPT1","LPT2","LPT3","LPT4","LPT5","LPT6","LPT7","LPT8","LPT9",
    }
    stem = Path(name).stem.upper()
    if stem in reserved:
        raise PathValidationError(f"Filename is a Windows reserved name: {name!r}")

    return name
