"""Team and schema constants aligned with pybaseballstats / UmpScorecards API."""

GUARDIANS = "CLE"

# Columns returned by pybaseballstats.umpire_scorecards.game_data (as pandas).
REQUIRED_GAME_COLUMNS = (
    "game_pk",
    "date",
    "home_team",
    "away_team",
    "umpire",
    "favor",
)
