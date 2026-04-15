import pandas as pd
import pytest

from umpscorecards.constants import GUARDIANS
from umpscorecards.normalize import (
    SchemaError,
    add_opponent_and_cle_favor,
    normalize_guardians_frame,
    validate_schema,
)


def test_cle_favor_home_and_away():
    df = pd.DataFrame(
        {
            "game_pk": [1, 2],
            "date": ["2026-04-01", "2026-04-02"],
            "home_team": ["CLE", "NYY"],
            "away_team": ["CHC", "CLE"],
            "umpire": ["A", "B"],
            "favor": [1.0, 0.5],
        }
    )
    out = add_opponent_and_cle_favor(df)
    assert list(out["cle_favor"]) == [1.0, -0.5]
    assert list(out["opponent"]) == ["CHC", "NYY"]


def test_validate_schema_missing_column():
    df = pd.DataFrame({"game_pk": [1]})
    with pytest.raises(SchemaError):
        validate_schema(df)


def test_normalize_fixture_loads():
    df = pd.read_csv("tests/fixtures/sample_cle_games.csv")
    validate_schema(df)
    norm = normalize_guardians_frame(df)
    assert len(norm) == 7
    assert (norm["home_team"] == GUARDIANS).sum() >= 1
