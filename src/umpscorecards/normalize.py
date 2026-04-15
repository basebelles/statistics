"""Normalize raw game rows to opponent + Cleveland-centric favor."""

from __future__ import annotations

import pandas as pd

from umpscorecards.constants import GUARDIANS, REQUIRED_GAME_COLUMNS


class SchemaError(ValueError):
    """Raised when upstream column names drift."""


def validate_schema(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_GAME_COLUMNS if c not in df.columns]
    if missing:
        raise SchemaError(
            f"Missing columns {missing}; have {list(df.columns)}. "
            "Pin pybaseballstats or update REQUIRED_GAME_COLUMNS."
        )


def add_opponent_and_cle_favor(df: pd.DataFrame) -> pd.DataFrame:
    """Add ``opponent`` and ``cle_favor`` from home/away and UmpScorecards ``favor``.

    ``favor`` is run expectancy favor for the **home** team (positive = home helped).
    """
    out = df.copy()
    is_home = out["home_team"] == GUARDIANS
    out["opponent"] = out["away_team"].where(is_home, out["home_team"])
    out["cle_favor"] = out["favor"].where(is_home, -out["favor"])
    return out


def normalize_guardians_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to CLE games, validate schema, sort chronologically."""
    validate_schema(df)
    mask = (df["home_team"] == GUARDIANS) | (df["away_team"] == GUARDIANS)
    out = df.loc[mask].copy()
    out = add_opponent_and_cle_favor(out)
    out = out.sort_values(["date", "game_pk"], kind="mergesort").reset_index(drop=True)
    return out
