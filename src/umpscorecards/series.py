"""Detect completed series from chronological opponent runs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class CompletedSeries:
    opponent: str
    games: pd.DataFrame
    total_cle_favor: float
    series_key: str

    @property
    def emission_key(self) -> str:
        """Dedupe id for :class:`stats_agent.core.protocols.Emittable`."""
        return self.series_key

    def to_llm_context(self) -> dict[str, Any]:
        """Structured facts for summarization (:class:`stats_agent.core.protocols.Emittable`)."""
        games_records = self.games[
            ["date", "home_team", "away_team", "umpire", "cle_favor"]
        ].to_dict(orient="records")
        return {
            "opponent": self.opponent,
            "game_count": len(self.games),
            "total_cle_favor": round(self.total_cle_favor, 3),
            "games": games_records,
        }


def _run_ids(opponent: pd.Series) -> pd.Series:
    return (opponent != opponent.shift()).cumsum()


def find_completed_series(df: pd.DataFrame) -> list[CompletedSeries]:
    """Return series that have a later game in ``df`` against a different opponent.

    Rows must be chronological (``date``, ``game_pk``) as from
    :func:`normalize_guardians_frame`; the pipeline does not re-sort here.

    The chronologically last run in the frame is treated as **incomplete** (no proof
    the next opponent has started within this window).
    """
    if df.empty or "opponent" not in df.columns:
        return []
    work = df.reset_index(drop=True)
    work["_run"] = _run_ids(work["opponent"])
    n = len(work)
    completed: list[CompletedSeries] = []
    for _, g in work.groupby("_run", sort=False):
        last_pos = g.index[-1]
        if last_pos >= n - 1:
            continue
        block = g.drop(columns=["_run"])
        opponent = str(block["opponent"].iloc[0])
        total = float(block["cle_favor"].sum())
        end_date = str(block["date"].iloc[-1])
        key = f"{opponent}_{end_date}_{len(block)}"
        completed.append(
            CompletedSeries(
                opponent=opponent,
                games=block.reset_index(drop=True),
                total_cle_favor=total,
                series_key=key,
            )
        )
    return completed
