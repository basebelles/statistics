"""Detect completed series from chronological opponent runs."""

from __future__ import annotations

from dataclasses import dataclass

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

    def to_llm_context(self) -> dict:
        """Alias for LLM input; prefer over ``to_prompt_dict`` in new code."""
        return self.to_prompt_dict()

    def to_prompt_dict(self) -> dict:
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

    The chronologically last run in the frame is treated as **incomplete** (no proof
    the next opponent has started within this window).
    """
    if df.empty or "opponent" not in df.columns:
        return []
    work = df.sort_values(["date", "game_pk"], kind="mergesort").reset_index(drop=True)
    work = work.copy()
    work["_run"] = _run_ids(work["opponent"])
    completed: list[CompletedSeries] = []
    for rid in work["_run"].unique():
        block = work[work["_run"] == rid].drop(columns=["_run"])
        last_pos = block.index[-1]
        if last_pos >= len(work) - 1:
            continue
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
