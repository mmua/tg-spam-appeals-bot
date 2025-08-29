"""Utility functions for the Appeals Bot."""

import logging
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


# UnbanService moved to services.py


def format_user_mention(
    first_name: Optional[str], username: Optional[str] = None
) -> str:
    """Format user mention string."""
    name = first_name or "Unknown"
    if username:
        return f"{name} (@{username})"
    return name


def escape_markdown(text: str) -> str:
    """Escape markdown special characters."""
    special_chars = [
        "_",
        "*",
        "[",
        "]",
        "(",
        ")",
        "~",
        "`",
        ">",
        "#",
        "+",
        "-",
        "=",
        "|",
        "{",
        "}",
        ".",
        "!",
    ]
    for char in special_chars:
        text = text.replace(char, f"\\{char}")
    return text


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[: max_length - 3] + "..."


def format_datetime(dt: object) -> str:
    """Format datetime object or string for display (YYYY-MM-DD HH:MM).

    Falls back to the first 16 chars of string representation, or "Unknown".
    """
    if isinstance(dt, datetime):
        return dt.strftime("%Y-%m-%d %H:%M")
    return str(dt)[:16] if dt else "Unknown"


def validate_appeal_text(text: str) -> tuple[bool, Optional[str]]:
    """Validate appeal text.

    Returns:
        (is_valid, error_message): Tuple where error_message is in Russian when invalid.
    """
    if not text or not text.strip():
        return False, "Текст апелляции не может быть пустым"

    if len(text.strip()) < 10:
        return False, "Текст апелляции должен содержать не менее 10 символов"

    if len(text) > 1000:
        return False, "Текст апелляции должен быть не длиннее 1000 символов"

    return True, None
