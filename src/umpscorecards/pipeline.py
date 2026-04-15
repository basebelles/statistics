"""Guardians + UmpScorecards implementation of :class:`stats_agent.core.protocols.StatPipeline`."""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

from stats_agent.core.protocols import Emittable, StatPipeline
from stats_agent.core.registry import register_pipeline
from umpscorecards.artifacts import write_series_markdown
from umpscorecards.fetch import fetch_guardians_games
from umpscorecards.llm_summary import summarize_series_openai, template_summary
from umpscorecards.normalize import normalize_guardians_frame
from umpscorecards.series import CompletedSeries, find_completed_series


class GuardiansUmpScorecardsPipeline:
    """Fetch UmpScorecards data for CLE, detect completed series, summarize, write MD."""

    id = "guardians-umpscorecards"
    label = "Guardians UmpScorecards (series summaries)"

    def fetch_raw(self, start_date: str, end_date: str) -> pd.DataFrame:
        return fetch_guardians_games(start_date, end_date)

    def normalize(self, raw: pd.DataFrame) -> pd.DataFrame:
        return normalize_guardians_frame(raw)

    def discover_emittables(self, normalized: pd.DataFrame) -> list[Emittable]:
        return find_completed_series(normalized)

    def summarize(
        self,
        event: Emittable,
        *,
        skip_llm: bool,
        openai_model: str | None,
    ) -> str:
        cs = _as_completed_series(event)
        if skip_llm or not os.environ.get("OPENAI_API_KEY"):
            return template_summary(cs)
        return summarize_series_openai(cs, model=openai_model)

    def write_artifact(
        self,
        event: Emittable,
        summary: str,
        out_dir: Path,
    ) -> Path:
        cs = _as_completed_series(event)
        return write_series_markdown(out_dir, cs, summary)


def _as_completed_series(event: Emittable) -> CompletedSeries:
    if isinstance(event, CompletedSeries):
        return event
    raise TypeError(
        f"Expected CompletedSeries for this pipeline, got {type(event).__name__}"
    )


PIPELINE = GuardiansUmpScorecardsPipeline()
register_pipeline(PIPELINE)
