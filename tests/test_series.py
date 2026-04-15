import pandas as pd

from umpscorecards.normalize import normalize_guardians_frame
from umpscorecards.series import find_completed_series


def test_find_completed_series_from_fixture():
    raw = pd.read_csv("tests/fixtures/sample_cle_games.csv")
    norm = normalize_guardians_frame(raw)
    series_list = find_completed_series(norm)
    keys = {s.series_key for s in series_list}
    # CHC run ends 2026-04-05 before KC; KC run ends before ATL
    assert any(k.startswith("CHC_") for k in keys)
    assert any(k.startswith("KC_") for k in keys)
    # Last block is ATL with no following row -> not completed
    assert not any(k.startswith("ATL_") for k in keys)


def test_single_opponent_window_no_completed():
    df = pd.DataFrame(
        {
            "game_pk": [1, 2],
            "date": ["2026-04-01", "2026-04-02"],
            "home_team": ["CLE", "CLE"],
            "away_team": ["KC", "KC"],
            "umpire": ["A", "B"],
            "favor": [0.1, -0.1],
        }
    )

    norm = normalize_guardians_frame(df)
    assert find_completed_series(norm) == []


def test_completed_series_prompt_dict():
    raw = pd.read_csv("tests/fixtures/sample_cle_games.csv")
    norm = normalize_guardians_frame(raw)
    completed = find_completed_series(norm)
    chc = next(s for s in completed if s.opponent == "CHC")
    d = chc.to_llm_context()
    assert d["opponent"] == "CHC"
    assert d["game_count"] == 2
    assert "games" in d
