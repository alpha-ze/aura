"""
File management tools.
All paths are validated before any operation.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

import structlog

from app.agent.router import registry
from app.models.schemas import ToolResult
from app.security.path_validator import (
    validate_path,
    validate_filename,
    resolve_safe_path,
    is_dangerous_extension,
    PathValidationError,
)

log = structlog.get_logger(__name__)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _path_info(p: Path) -> dict:
    try:
        stat = p.stat()
        return {
            "name": p.name,
            "path": str(p),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / 1_048_576, 2),
            "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
            "is_directory": p.is_dir(),
            "extension": p.suffix.lower(),
        }
    except Exception:
        return {"name": p.name, "path": str(p)}


# ── Tool: search_files ────────────────────────────────────────────────────────

@registry.register(
    name="search_files",
    description="Search for files by name pattern, extension, or date in a directory.",
    parameters={
        "directory": "str — directory to search (e.g. 'Downloads', 'Desktop', or absolute path)",
        "pattern":   "str — optional filename pattern (e.g. '*.pptx', 'report*')",
        "extension": "str — optional file extension filter (e.g. '.pdf')",
        "modified_after": "str — optional ISO date to filter by (e.g. '2026-10-07')",
        "max_results": "int — maximum results to return (default 20)",
    },
)
async def search_files(
    directory: str = "Downloads",
    pattern: str = "*",
    extension: Optional[str] = None,
    modified_after: Optional[str] = None,
    max_results: int = 20,
) -> ToolResult:
    try:
        search_root = resolve_safe_path(directory)
    except PathValidationError as e:
        return ToolResult.fail(str(e), error_code="INVALID_PATH")

    if not search_root.exists() or not search_root.is_dir():
        return ToolResult.fail(f"Directory not found: {search_root}", error_code="DIR_NOT_FOUND")

    # Build glob pattern
    if extension and not extension.startswith("."):
        extension = f".{extension}"
    glob_pattern = pattern if pattern != "*" else "*"

    try:
        cutoff: Optional[datetime] = None
        if modified_after:
            cutoff = datetime.fromisoformat(modified_after).replace(tzinfo=timezone.utc)

        results = []
        for item in search_root.rglob(glob_pattern):
            if len(results) >= max_results:
                break
            if extension and item.suffix.lower() != extension.lower():
                continue
            if cutoff:
                try:
                    mtime = datetime.fromtimestamp(item.stat().st_mtime, tz=timezone.utc)
                    if mtime < cutoff:
                        continue
                except OSError:
                    continue
            results.append(_path_info(item))

        if not results:
            return ToolResult.ok(
                f"No files matching '{pattern}' found in {search_root.name}.",
                data=[],
            )

        return ToolResult.ok(
            f"Found {len(results)} file(s) matching '{pattern}' in {search_root.name}.",
            data=results,
        )
    except PermissionError:
        return ToolResult.fail("Permission denied searching that directory.", error_code="ACCESS_DENIED")
    except Exception as exc:
        log.exception("search_files_error")
        return ToolResult.fail(str(exc))


# ── Tool: get_recent_files ────────────────────────────────────────────────────

@registry.register(
    name="get_recent_files",
    description="Get recently modified files from common user folders.",
    parameters={
        "hours": "int — how many hours back to look (default 24)",
        "max_results": "int — max files to return (default 15)",
    },
)
async def get_recent_files(hours: int = 24, max_results: int = 15) -> ToolResult:
    home = Path.home()
    search_dirs = [
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
    ]
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=hours)
    results = []

    for folder in search_dirs:
        if not folder.exists():
            continue
        try:
            for item in folder.rglob("*"):
                if item.is_dir():
                    continue
                try:
                    mtime = datetime.fromtimestamp(item.stat().st_mtime, tz=timezone.utc)
                    if mtime >= cutoff:
                        results.append({**_path_info(item), "folder": folder.name})
                except OSError:
                    continue
        except PermissionError:
            continue

    results.sort(key=lambda x: x.get("modified", ""), reverse=True)
    results = results[:max_results]

    return ToolResult.ok(
        f"Found {len(results)} recently modified file(s) in the last {hours} hours.",
        data=results,
    )


# ── Tool: get_downloads ───────────────────────────────────────────────────────

@registry.register(
    name="get_downloads",
    description="List files in the user's Downloads folder, optionally filtered by date.",
    parameters={"days": "int — days back to look (default 7)"},
)
async def get_downloads(days: int = 7) -> ToolResult:
    downloads = Path.home() / "Downloads"
    if not downloads.exists():
        return ToolResult.fail("Downloads folder not found.", error_code="DIR_NOT_FOUND")

    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=days)
    files = []
    try:
        for item in sorted(downloads.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True):
            if item.is_file():
                try:
                    mtime = datetime.fromtimestamp(item.stat().st_mtime, tz=timezone.utc)
                    if mtime >= cutoff:
                        files.append(_path_info(item))
                except OSError:
                    continue
    except PermissionError:
        return ToolResult.fail("Permission denied reading Downloads.", error_code="ACCESS_DENIED")

    return ToolResult.ok(f"Found {len(files)} file(s) in Downloads from the last {days} days.", data=files)


# ── Tool: open_file ───────────────────────────────────────────────────────────

@registry.register(
    name="open_file",
    description="Open a file using its default application (like double-clicking it).",
    parameters={"path": "str — absolute path or shorthand (Desktop/Downloads/etc.)"},
)
async def open_file(path: str) -> ToolResult:
    try:
        resolved = resolve_safe_path(path)
        validated = validate_path(resolved)
    except PathValidationError as e:
        return ToolResult.fail(str(e), error_code="INVALID_PATH")

    # Refuse to open executable files automatically
    if is_dangerous_extension(validated):
        return ToolResult.fail(
            f"AURA will not automatically open executable files ({validated.suffix}). "
            "Open it manually from Explorer if intended.",
            error_code="DANGEROUS_EXTENSION",
        )

    try:
        os.startfile(str(validated))  # type: ignore[attr-defined]
        return ToolResult.ok(f"Opened: {validated.name}", data={"path": str(validated)})
    except Exception as exc:
        return ToolResult.fail(f"Failed to open file: {exc}", error="OS_ERROR")


# ── Tool: show_in_explorer ────────────────────────────────────────────────────

@registry.register(
    name="show_in_explorer",
    description="Show a file or folder in Windows Explorer.",
    parameters={"path": "str — path to reveal"},
)
async def show_in_explorer(path: str) -> ToolResult:
    try:
        resolved = validate_path(resolve_safe_path(path))
    except PathValidationError as e:
        return ToolResult.fail(str(e), error_code="INVALID_PATH")

    try:
        if resolved.is_file():
            subprocess.Popen(["explorer", "/select,", str(resolved)])
        else:
            subprocess.Popen(["explorer", str(resolved)])
        return ToolResult.ok(f"Opened Explorer at: {resolved}")
    except Exception as exc:
        return ToolResult.fail(str(exc))


# ── Tool: rename_file ─────────────────────────────────────────────────────────

@registry.register(
    name="rename_file",
    description="Rename a file or folder.",
    parameters={
        "path": "str — current file path",
        "new_name": "str — new filename (just the name, not a full path)",
    },
)
async def rename_file(path: str, new_name: str) -> ToolResult:
    try:
        source = validate_path(resolve_safe_path(path))
        new_name = validate_filename(new_name)
    except PathValidationError as e:
        return ToolResult.fail(str(e), error_code="INVALID_PATH")

    destination = source.parent / new_name
    if destination.exists():
        return ToolResult.fail(
            f"A file named '{new_name}' already exists in that location.",
            error_code="ALREADY_EXISTS",
        )

    try:
        source.rename(destination)
        return ToolResult.ok(
            f"Renamed '{source.name}' → '{new_name}'",
            data={"old": str(source), "new": str(destination)},
        )
    except PermissionError:
        return ToolResult.fail("Permission denied.", error_code="ACCESS_DENIED")
    except Exception as exc:
        return ToolResult.fail(str(exc))


# ── Tool: move_file ───────────────────────────────────────────────────────────

@registry.register(
    name="move_file",
    description="Move a file or folder to a different location.",
    parameters={
        "source": "str — current path",
        "destination": "str — destination directory",
    },
)
async def move_file(source: str, destination: str) -> ToolResult:
    try:
        src = validate_path(resolve_safe_path(source))
        dst_dir = validate_path(resolve_safe_path(destination))
    except PathValidationError as e:
        return ToolResult.fail(str(e), error_code="INVALID_PATH")

    dst_path = dst_dir / src.name
    if dst_path.exists():
        return ToolResult.fail(f"Destination already has a file named '{src.name}'.", error_code="ALREADY_EXISTS")

    try:
        shutil.move(str(src), str(dst_path))
        return ToolResult.ok(
            f"Moved '{src.name}' to {dst_dir.name}",
            data={"source": str(src), "destination": str(dst_path)},
        )
    except PermissionError:
        return ToolResult.fail("Permission denied.", error_code="ACCESS_DENIED")
    except Exception as exc:
        return ToolResult.fail(str(exc))


# ── Tool: copy_file ───────────────────────────────────────────────────────────

@registry.register(
    name="copy_file",
    description="Copy a file to a destination directory.",
    parameters={
        "source": "str — file to copy",
        "destination": "str — destination directory",
    },
)
async def copy_file(source: str, destination: str) -> ToolResult:
    try:
        src = validate_path(resolve_safe_path(source))
        dst_dir = validate_path(resolve_safe_path(destination))
    except PathValidationError as e:
        return ToolResult.fail(str(e), error_code="INVALID_PATH")

    dst_path = dst_dir / src.name
    try:
        shutil.copy2(str(src), str(dst_path))
        return ToolResult.ok(f"Copied '{src.name}' to {dst_dir.name}", data={"destination": str(dst_path)})
    except PermissionError:
        return ToolResult.fail("Permission denied.", error_code="ACCESS_DENIED")
    except Exception as exc:
        return ToolResult.fail(str(exc))


# ── Tool: delete_file (HIGH risk) ────────────────────────────────────────────

@registry.register(
    name="delete_file",
    description="Delete a file permanently. Requires confirmation.",
    parameters={"path": "str — file to delete"},
)
async def delete_file(path: str) -> ToolResult:
    try:
        target = validate_path(resolve_safe_path(path))
    except PathValidationError as e:
        return ToolResult.fail(str(e), error_code="INVALID_PATH")

    try:
        if target.is_dir():
            shutil.rmtree(str(target))
        else:
            target.unlink()
        return ToolResult.ok(f"Deleted: {target.name}", data={"deleted": str(target)})
    except PermissionError:
        return ToolResult.fail("Permission denied.", error_code="ACCESS_DENIED")
    except Exception as exc:
        return ToolResult.fail(str(exc))


# ── Tool: create_folder ───────────────────────────────────────────────────────

@registry.register(
    name="create_folder",
    description="Create a new folder.",
    parameters={
        "parent": "str — parent directory (default: Desktop)",
        "name": "str — folder name",
    },
)
async def create_folder(name: str, parent: str = "Desktop") -> ToolResult:
    try:
        name = validate_filename(name)
        parent_path = validate_path(resolve_safe_path(parent))
    except PathValidationError as e:
        return ToolResult.fail(str(e), error_code="INVALID_PATH")

    new_folder = parent_path / name
    if new_folder.exists():
        return ToolResult.fail(f"Folder '{name}' already exists.", error_code="ALREADY_EXISTS")

    try:
        new_folder.mkdir(parents=False, exist_ok=False)
        return ToolResult.ok(f"Created folder: {name}", data={"path": str(new_folder)})
    except PermissionError:
        return ToolResult.fail("Permission denied.", error_code="ACCESS_DENIED")
    except Exception as exc:
        return ToolResult.fail(str(exc))
