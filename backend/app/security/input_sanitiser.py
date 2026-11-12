"""
Input sanitisation and prompt injection defence.

External content (file contents, command output, web pages, etc.)
must NEVER be treated as agent instructions.
This module provides utilities to clearly separate trusted instructions
from untrusted data.
"""
from __future__ import annotations

import re
from typing import Any

import structlog

log = structlog.get_logger(__name__)

# Patterns that indicate attempted prompt injection
_INJECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"ignore\s+(previous|all)\s+instructions?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a", re.IGNORECASE),
    re.compile(r"new\s+system\s+prompt", re.IGNORECASE),
    re.compile(r"disregard\s+(your|all|previous)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(?:if\s+you\s+were|a)", re.IGNORECASE),
    re.compile(r"sudo\s+mode", re.IGNORECASE),
    re.compile(r"developer\s+mode", re.IGNORECASE),
    re.compile(r"jailbreak", re.IGNORECASE),
    re.compile(r"<\s*system\s*>", re.IGNORECASE),
    re.compile(r"\[INST\]|\[/INST\]", re.IGNORECASE),
]

# Max size for file content to be included in AI context (64 KB)
MAX_CONTENT_BYTES = 64 * 1024


def wrap_as_untrusted_data(content: str, source: str = "external") -> str:
    """
    Wrap external content in a clear boundary marker that tells the AI
    this is untrusted data, not instructions.

    The AI system prompt reinforces that content inside these markers
    must never be executed as instructions.
    """
    return (
        f"[UNTRUSTED_DATA source={source!r}]\n"
        f"{content}\n"
        f"[/UNTRUSTED_DATA]"
    )


def check_for_injection(text: str) -> list[str]:
    """
    Scan text for prompt injection patterns.
    Returns a list of detected pattern descriptions (empty = clean).
    """
    detected: list[str] = []
    for pattern in _INJECTION_PATTERNS:
        if pattern.search(text):
            detected.append(pattern.pattern)
    return detected


def sanitise_user_message(message: str) -> tuple[str, list[str]]:
    """
    Sanitise a direct user message.
    Returns (sanitised_message, warnings).
    User messages are trusted but we still log suspicious patterns.
    """
    warnings: list[str] = []
    detected = check_for_injection(message)
    if detected:
        log.warning(
            "suspicious_user_input",
            patterns=detected,
            message_preview=message[:100],
        )
        warnings.extend(detected)
    return message, warnings


def sanitise_file_content(content: str | bytes, filename: str = "file") -> str:
    """
    Prepare file content for inclusion in AI context as untrusted data.
    - Truncates oversized content
    - Wraps in untrusted data boundary
    - Logs injection attempts (does not block — the wrapper is the defence)
    """
    if isinstance(content, bytes):
        content = content.decode("utf-8", errors="replace")

    # Truncate to prevent token flooding
    if len(content.encode("utf-8")) > MAX_CONTENT_BYTES:
        content = content[: MAX_CONTENT_BYTES] + "\n[... content truncated ...]"
        log.warning("file_content_truncated", filename=filename)

    detected = check_for_injection(content)
    if detected:
        log.warning(
            "prompt_injection_attempt_in_file",
            filename=filename,
            patterns=detected,
            note="Content will be passed as untrusted data only",
        )

    return wrap_as_untrusted_data(content, source=filename)


def sanitise_command_output(output: str, command: str = "command") -> str:
    """Wrap command stdout/stderr as untrusted data."""
    detected = check_for_injection(output)
    if detected:
        log.warning(
            "injection_pattern_in_command_output",
            command=command,
            patterns=detected,
        )
    return wrap_as_untrusted_data(output, source=f"command_output:{command}")
