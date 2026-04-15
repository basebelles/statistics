"""Generic run loop: fetch → normalize → discover → summarize → persist state."""

from __future__ import annotations

from dataclasses import dataclass

from stats_agent.core.protocols import StatPipeline
from stats_agent.core.state import RunState, load_state, save_state
from pathlib import Path


@dataclass(frozen=True)
class RunResult:
    start_date: str
    end_date: str
    row_count: int
    event_count: int
    new_artifacts: int
    artifact_paths: tuple[Path, ...]


def run_pipeline(
    pipeline: StatPipeline,
    *,
    start_date: str,
    end_date: str,
    state_path: Path,
    artifacts_dir: Path,
    skip_llm: bool,
    openai_model: str | None,
) -> RunResult:
    raw = pipeline.fetch_raw(start_date, end_date)
    normalized = pipeline.normalize(raw)
    events = pipeline.discover_emittables(normalized)
    state = load_state(state_path)

    paths: list[Path] = []
    wrote = 0
    for ev in events:
        key = ev.emission_key
        if not state.should_emit(key):
            continue
        text = pipeline.summarize(
            ev, skip_llm=skip_llm, openai_model=openai_model
        )
        path = pipeline.write_artifact(ev, text, artifacts_dir)
        state.record(key)
        paths.append(path)
        wrote += 1

    save_state(state_path, state)
    return RunResult(
        start_date=start_date,
        end_date=end_date,
        row_count=len(normalized),
        event_count=len(events),
        new_artifacts=wrote,
        artifact_paths=tuple(paths),
    )
