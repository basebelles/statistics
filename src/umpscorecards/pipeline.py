"""Guardians + UmpScorecards implementation of :class:`stats_agent.core.protocols.StatPipeline`."""

from __future__ import annotations

import os
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

from stats_agent.core.protocols import Emittable, StatPipeline
from stats_agent.core.registry import register_pipeline
from umpscorecards.artifacts import write_series_markdown
from umpscorecards.constants import DEFAULT_FETCH_LOOKBACK_DAYS
from umpscorecards.fetch import fetch_guardians_games
from umpscorecards.llm_summary import summarize_series_gemini, template_summary
from umpscorecards.normalize import normalize_guardians_frame
from umpscorecards.series import CompletedSeries, find_completed_series


class GuardiansUmpScorecardsPipeline:
    """Fetch UmpScorecards data for CLE, detect completed series, summarize, write MD."""

    id = "guardians-umpscorecards"
    label = "Guardians UmpScorecards (series summaries)"

    def fetch_raw(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Fetch games from an **earlier** effective start so series aren’t truncated.

        A rolling window beginning mid-series (e.g. first day Apr 1) would otherwise
        include only the tail of a multi-game set vs one opponent.
        """
        raw_days = os.environ.get("GUARDIANS_UMPS_FETCH_LOOKBACK_DAYS")
        buf = int(raw_days) if raw_days is not None else DEFAULT_FETCH_LOOKBACK_DAYS
        start = date.fromisoformat(start_date)
        effective_start = start - timedelta(days=buf)
        return fetch_guardians_games(effective_start.isoformat(), end_date)

    def normalize(self, raw: pd.DataFrame) -> pd.DataFrame:
        return normalize_guardians_frame(raw)

    def discover_emittables(self, normalized: pd.DataFrame) -> list[Emittable]:
        return find_completed_series(normalized)

    def summarize(
        self,
        event: Emittable,
        *,
        skip_llm: bool,
        llm_model: str | None,
    ) -> str:
        cs = _as_completed_series(event)
        if skip_llm or not os.environ.get("GEMINI_API_KEY"):
            return template_summary(cs)
        return summarize_series_gemini(cs, model=llm_model)

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
