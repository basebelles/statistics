"""Guardians pipeline extends fetch start for full opponent series."""

from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from umpscorecards.pipeline import GuardiansUmpScorecardsPipeline


@patch("umpscorecards.pipeline.fetch_guardians_games")
def test_fetch_raw_applies_lookback(mock_fetch: object) -> None:
    mock_fetch.return_value = pd.DataFrame()
    p = GuardiansUmpScorecardsPipeline()
    p.fetch_raw("2026-04-01", "2026-04-15")
    mock_fetch.assert_called_once()
    args, _kwargs = mock_fetch.call_args
    assert args[0] == "2026-03-11"  # 21 days before Apr 1
    assert args[1] == "2026-04-15"
