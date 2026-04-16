import pandas as pd
from unittest.mock import MagicMock, patch

import pytest

from google.genai.errors import ClientError

from umpscorecards.series import CompletedSeries
from umpscorecards.llm_summary import _resolve_gemini_model, summarize_series_gemini


def _minimal_series() -> CompletedSeries:
    df = pd.DataFrame(
        {
            "date": ["2026-04-01"],
            "home_team": ["CLE"],
            "away_team": ["KC"],
            "umpire": ["U"],
            "cle_favor": [0.1],
        }
    )
    return CompletedSeries(
        opponent="KC",
        games=df,
        total_cle_favor=0.1,
        series_key="KC_2026-04-01_1",
    )


def test_resolve_gemini_model_empty_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GEMINI_MODEL", "")
    assert _resolve_gemini_model(None) == "gemini-2.5-flash"


@patch("google.genai.Client")
def test_summarize_gemini_empty_env_uses_default_model(
    mock_client_cls: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MODEL", "")
    mock_gen = mock_client_cls.return_value.models.generate_content
    mock_gen.return_value = MagicMock(text="Two sentences.")

    summarize_series_gemini(_minimal_series(), model=None)
    assert mock_gen.call_args.kwargs["model"] == "gemini-2.5-flash"


@patch("google.genai.Client")
def test_summarize_gemini_falls_back_on_429(
    mock_client_cls: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_client_cls.return_value.models.generate_content.side_effect = ClientError(
        429, {"error": {"message": "RESOURCE_EXHAUSTED"}}, None
    )

    s = _minimal_series()
    out = summarize_series_gemini(s, model="gemini-2.5-flash")
    assert "HTTP 429" in out
    assert "Guardians" in out


@patch("google.genai.Client")
def test_summarize_gemini_strict_reraises_429(
    mock_client_cls: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_STRICT", "1")
    mock_client_cls.return_value.models.generate_content.side_effect = ClientError(
        429, {"error": {"message": "x"}}, None
    )
    s = _minimal_series()
    with pytest.raises(ClientError):
        summarize_series_gemini(s, model="gemini-2.5-flash")
