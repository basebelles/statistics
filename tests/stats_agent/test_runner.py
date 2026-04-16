"""Runner behavior (dedupe vs --force)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from stats_agent.core.runner import run_pipeline


@dataclass
class _Ev:
    emission_key: str

    def to_llm_context(self) -> dict:
        return {}


class _FakePipeline:
    id = "test-pipe"
    label = "test"

    def fetch_raw(self, start_date: str, end_date: str) -> pd.DataFrame:
        return pd.DataFrame({"x": [1]})

    def normalize(self, raw: pd.DataFrame) -> pd.DataFrame:
        return raw

    def discover_emittables(self, normalized: pd.DataFrame) -> list:
        return [_Ev("key-a"), _Ev("key-b")]

    def summarize(self, event, *, skip_llm: bool, llm_model: str | None) -> str:
        return "ok"

    def write_artifact(self, event, summary: str, out_dir: Path) -> Path:
        out_dir.mkdir(parents=True, exist_ok=True)
        p = out_dir / f"{event.emission_key}.md"
        p.write_text(summary)
        return p


def test_runner_skips_emitted_keys(tmp_path: Path) -> None:
    state = tmp_path / "s.json"
    state.write_text('{"emitted_series_keys": ["key-a", "key-b"]}', encoding="utf-8")
    art = tmp_path / "out"
    p = _FakePipeline()
    r = run_pipeline(
        p,
        start_date="2026-01-01",
        end_date="2026-01-31",
        state_path=state,
        artifacts_dir=art,
        skip_llm=True,
        llm_model=None,
        force=False,
    )
    assert r.new_artifacts == 0


def test_force_rewrites_despite_state(tmp_path: Path) -> None:
    state = tmp_path / "s.json"
    state.write_text('{"emitted_series_keys": ["key-a", "key-b"]}', encoding="utf-8")
    art = tmp_path / "out"
    p = _FakePipeline()
    r = run_pipeline(
        p,
        start_date="2026-01-01",
        end_date="2026-01-31",
        state_path=state,
        artifacts_dir=art,
        skip_llm=True,
        llm_model=None,
        force=True,
    )
    assert r.new_artifacts == 2
    assert (art / "key-a.md").exists()
    assert (art / "key-b.md").exists()
