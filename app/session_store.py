"""Disk-persisted chat session store.

Saves session histories as a JSON file so they survive server restarts.
Thread-safe for single-process use (FastAPI default).

File location: ``data/sessions.json`` (auto-created).
"""

import json
import os
import logging
from typing import List, Tuple

logger = logging.getLogger(__name__)

SESSION_FILE = os.path.join("data", "sessions.json")
os.makedirs("data", exist_ok=True)


def _load() -> dict[str, List[Tuple[str, str]]]:
    """Load the sessions dict from disk, returning empty dict on failure."""
    if not os.path.exists(SESSION_FILE):
        return {}
    try:
        with open(SESSION_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
        # JSON stores tuples as lists — convert back to list-of-tuples
        return {sid: [tuple(pair) for pair in turns] for sid, turns in raw.items()}
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning("Could not load sessions.json (%s). Starting fresh.", exc)
        return {}


def _save(sessions: dict[str, List[Tuple[str, str]]]) -> None:
    """Persist the sessions dict to disk atomically (write-then-rename)."""
    tmp_path = SESSION_FILE + ".tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, SESSION_FILE)
    except OSError as exc:
        logger.error("Could not save sessions.json: %s", exc)


# Module-level in-memory cache (loaded once at startup)
_sessions: dict[str, List[Tuple[str, str]]] = _load()


def get_sessions() -> dict[str, List[Tuple[str, str]]]:
    """Return the live in-memory sessions dict (backed by disk)."""
    return _sessions


def save_sessions() -> None:
    """Flush the current in-memory sessions to disk."""
    _save(_sessions)
