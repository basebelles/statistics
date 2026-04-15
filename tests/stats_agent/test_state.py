import json
from pathlib import Path

from stats_agent.core.state import RunState, load_state, save_state


def test_load_state_empty_file(tmp_path: Path) -> None:
    p = tmp_path / "state.json"
    p.write_text("", encoding="utf-8")
    assert load_state(p) == RunState.empty()


def test_load_state_whitespace_only(tmp_path: Path) -> None:
    p = tmp_path / "state.json"
    p.write_text("   \n  ", encoding="utf-8")
    assert load_state(p) == RunState.empty()


def test_load_state_roundtrip(tmp_path: Path) -> None:
    p = tmp_path / "state.json"
    s = RunState(emitted_series_keys=["a", "b"])
    save_state(p, s)
    assert load_state(p).emitted_series_keys == ["a", "b"]


def test_load_state_invalid_json_raises(tmp_path: Path) -> None:
    p = tmp_path / "state.json"
    p.write_text("{not json", encoding="utf-8")
    try:
        load_state(p)
    except ValueError as e:
        assert "not valid JSON" in str(e)
        assert str(p) in str(e)
    else:
        raise AssertionError("expected ValueError")
