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


def _client_error(code: int) -> ClientError:
    return ClientError(code, {"error": {"message": "x"}}, None)


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


@patch("umpscorecards.llm_summary.time.sleep")
@patch("google.genai.Client")
def test_summarize_gemini_falls_back_on_429_after_retries(
    mock_client_cls: MagicMock,
    _mock_sleep: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_gen = mock_client_cls.return_value.models.generate_content
    mock_gen.side_effect = [
        _client_error(429),
        _client_error(429),
        _client_error(429),
        _client_error(429),
    ]

    s = _minimal_series()
    out = summarize_series_gemini(s, model="gemini-2.5-flash")
    assert mock_gen.call_count == 4
    assert "HTTP 429" in out
    assert "Guardians" in out


@patch("umpscorecards.llm_summary.time.sleep")
@patch("google.genai.Client")
def test_summarize_gemini_retries_then_succeeds(
    mock_client_cls: MagicMock,
    _mock_sleep: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    mock_gen = mock_client_cls.return_value.models.generate_content
    mock_gen.side_effect = [_client_error(429), MagicMock(text="Two sentences.")]

    out = summarize_series_gemini(_minimal_series(), model="gemini-2.5-flash")
    assert mock_gen.call_count == 2
    assert out == "Two sentences."


@patch("google.genai.Client")
def test_summarize_gemini_max_retries_zero_single_429_falls_back(
    mock_client_cls: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_MAX_RETRIES", "0")
    mock_gen = mock_client_cls.return_value.models.generate_content
    mock_gen.side_effect = [_client_error(429)]

    out = summarize_series_gemini(_minimal_series(), model="gemini-2.5-flash")
    assert mock_gen.call_count == 1
    assert "HTTP 429" in out


@patch("umpscorecards.llm_summary.time.sleep")
@patch("google.genai.Client")
def test_summarize_gemini_strict_reraises_429_after_retries(
    mock_client_cls: MagicMock,
    _mock_sleep: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    monkeypatch.setenv("GEMINI_STRICT", "1")
    mock_gen = mock_client_cls.return_value.models.generate_content
    mock_gen.side_effect = [
        _client_error(429),
        _client_error(429),
        _client_error(429),
        _client_error(429),
    ]
    s = _minimal_series()
    with pytest.raises(ClientError):
        summarize_series_gemini(s, model="gemini-2.5-flash")
    assert mock_gen.call_count == 4
