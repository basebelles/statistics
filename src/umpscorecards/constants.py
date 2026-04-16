"""Team and schema constants aligned with pybaseballstats / UmpScorecards API."""

GUARDIANS = "CLE"

# Extra calendar days to fetch before ``start_date`` so multi-game series are not cut off
# at the rolling window (e.g. LAD @ Mar 30–31 + Apr 1 when the user window starts Apr 1).
# Override with env ``GUARDIANS_UMPS_FETCH_LOOKBACK_DAYS``.
DEFAULT_FETCH_LOOKBACK_DAYS = 21

# Columns returned by pybaseballstats.umpire_scorecards.game_data (as pandas).
REQUIRED_GAME_COLUMNS = (
    "game_pk",
    "date",
    "home_team",
    "away_team",
    "umpire",
    "favor",
)
