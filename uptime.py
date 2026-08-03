"""Process-uptime tracking for the Preview Environment Dashboard."""

from __future__ import annotations

import time

_START_TIME = time.time()


def uptime_seconds() -> int:
    return int(time.time() - _START_TIME)


def format_uptime(seconds: int) -> str:
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    parts = []
    if days:
        parts.append(f"{days}d")
    if hours or days:
        parts.append(f"{hours}h")
    if minutes or hours or days:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)
