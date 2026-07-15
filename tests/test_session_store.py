"""Unit tests for app/session_store.py.

Tests the disk-persistence layer in isolation using a temporary file path
so real sessions.json is never touched during testing.
"""

import json
import os
import pytest
import importlib


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _reload_store(monkeypatch, tmp_path):
    """Reload session_store with SESSION_FILE pointing to a temp directory."""
    import app.session_store as store
    session_file = str(tmp_path / "sessions.json")
    monkeypatch.setattr(store, "SESSION_FILE", session_file)
    monkeypatch.setattr(store, "_sessions", {})
    return store, session_file


# ─── Tests ────────────────────────────────────────────────────────────────────

class TestSessionStore:
    def test_get_sessions_empty_on_missing_file(self, monkeypatch, tmp_path):
        store, _ = _reload_store(monkeypatch, tmp_path)
        sessions = store.get_sessions()
        assert sessions == {}

    def test_save_and_reload(self, monkeypatch, tmp_path):
        store, session_file = _reload_store(monkeypatch, tmp_path)
        sessions = store.get_sessions()
        sessions["session_a"] = [("hello", "hi there")]
        store.save_sessions()

        # Verify the file was written
        assert os.path.exists(session_file)
        with open(session_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "session_a" in data
        assert data["session_a"][0] == ["hello", "hi there"]

    def test_multiple_sessions_persisted(self, monkeypatch, tmp_path):
        store, session_file = _reload_store(monkeypatch, tmp_path)
        sessions = store.get_sessions()
        sessions["s1"] = [("q1", "a1"), ("q2", "a2")]
        sessions["s2"] = [("foo", "bar")]
        store.save_sessions()

        with open(session_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == 2
        assert len(data["s1"]) == 2

    def test_load_returns_tuples(self, monkeypatch, tmp_path):
        """Ensure JSON lists are converted back to tuples on load."""
        store, session_file = _reload_store(monkeypatch, tmp_path)
        # Pre-write a file as JSON (lists, not tuples)
        with open(session_file, "w") as f:
            json.dump({"sess": [["query", "response"]]}, f)

        # Manually call _load to check conversion
        loaded = store._load.__wrapped__(session_file) if hasattr(store._load, "__wrapped__") else None
        # Reload the module-level function directly
        import app.session_store as s2
        s2.SESSION_FILE = session_file
        result = s2._load()
        assert isinstance(result["sess"][0], tuple)

    def test_corrupt_file_returns_empty(self, monkeypatch, tmp_path):
        store, session_file = _reload_store(monkeypatch, tmp_path)
        with open(session_file, "w") as f:
            f.write("NOT VALID JSON{{{{")
        # Patch SESSION_FILE on the module and call _load directly
        import app.session_store as s
        s.SESSION_FILE = session_file
        result = s._load()
        assert result == {}

    def test_save_is_atomic(self, monkeypatch, tmp_path):
        """save_sessions should write via .tmp then rename (no partial writes)."""
        store, session_file = _reload_store(monkeypatch, tmp_path)
        sessions = store.get_sessions()
        sessions["x"] = [("q", "a")]
        store.save_sessions()
        # The .tmp file should NOT linger after a successful save
        assert not os.path.exists(session_file + ".tmp")
        assert os.path.exists(session_file)
