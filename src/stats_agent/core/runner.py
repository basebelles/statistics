"""Generic run loop: fetch → normalize → discover → summarize → persist state."""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path

from stats_agent.core.protocols import StatPipeline
from stats_agent.core.state import RunState, load_state, save_state


@dataclass(frozen=True)
class RunResult:
    start_date: str
    end_date: str
    row_count: int
    event_count: int
    new_artifacts: int
    artifact_paths: tuple[Path, ...]


def _gemini_inter_request_delay_sec(cli_seconds: float | None) -> float:
    if cli_seconds is not None:
        return max(0.0, float(cli_seconds))
    raw = (os.environ.get("GEMINI_INTER_REQUEST_DELAY_SEC") or "").strip()
    if not raw:
        return 0.0
    try:
        return max(0.0, float(raw))
    except ValueError:
        return 0.0


def run_pipeline(
    pipeline: StatPipeline,
    *,
    start_date: str,
    end_date: str,
    state_path: Path,
    artifacts_dir: Path,
    skip_llm: bool,
    llm_model: str | None,
    force: bool = False,
    gemini_inter_request_delay_sec: float | None = None,
) -> RunResult:
    raw = pipeline.fetch_raw(start_date, end_date)
    normalized = pipeline.normalize(raw)
    events = pipeline.discover_emittables(normalized)
    state = load_state(state_path)

    delay_sec = _gemini_inter_request_delay_sec(gemini_inter_request_delay_sec)
    use_llm_path = not skip_llm and bool(os.environ.get("GEMINI_API_KEY"))

    paths: list[Path] = []
    wrote = 0
    for ev in events:
        key = ev.emission_key
        if not force and not state.should_emit(key):
            continue
        text = pipeline.summarize(
            ev, skip_llm=skip_llm, llm_model=llm_model
        )
        path = pipeline.write_artifact(ev, text, artifacts_dir)
        state.record(key)
        paths.append(path)
        wrote += 1
        if delay_sec > 0.0 and use_llm_path:
            time.sleep(delay_sec)

    save_state(state_path, state)
    return RunResult(
        start_date=start_date,
        end_date=end_date,
        row_count=len(normalized),
        event_count=len(events),
        new_artifacts=wrote,
        artifact_paths=tuple(paths),
    )
