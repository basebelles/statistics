"""Fetch Guardians games from pybaseballstats (UmpScorecards API)."""

from __future__ import annotations

import pandas as pd
import pybaseballstats.umpire_scorecards as us
from pybaseballstats.consts.umpire_scorecard_consts import UmpireScorecardTeams


def fetch_guardians_games(
    start_date: str,
    end_date: str,
    *,
    game_type: str = "*",
) -> pd.DataFrame:
    """Return game rows for Cleveland in [start_date, end_date] (inclusive).

    Uses ``focus_team=GAURDIANS`` (spelling in library) to limit payload size.
    """
    pl_df = us.game_data(
        start_date=start_date,
        end_date=end_date,
        game_type=game_type,  # type: ignore[arg-type]
        focus_team=UmpireScorecardTeams.GAURDIANS,
        focus_team_home_away="*",
        opponent_team=UmpireScorecardTeams.ALL,
    )
    return pl_df.to_pandas()
