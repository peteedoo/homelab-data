import json
import tempfile
from pathlib import Path

from state import State, StateStore


def test_state_defaults():
    s = State()
    assert s.last_run is None
    assert s.prepped_urls == []


def test_state_idempotency():
    s = State()
    assert not s.is_prepped("https://example.com/job")
    s.mark_prepped("https://example.com/job")
    assert s.is_prepped("https://example.com/job")
    s.mark_prepped("https://example.com/job")
    assert len(s.prepped_urls) == 1


def test_state_store_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "state.json"
        store = StateStore(path)
        s = State(last_run="2026-06-25", prepped_urls=["https://example.com/job"])
        store.save(s)
        loaded = store.load()
        assert loaded.last_run == "2026-06-25"
        assert loaded.prepped_urls == ["https://example.com/job"]


def test_state_store_creates_default():
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "state.json"
        store = StateStore(path)
        loaded = store.load()
        assert loaded.last_run is None
        assert loaded.prepped_urls == []
