"""LLM-generated two-sentence series summary (Google Gemini)."""

from __future__ import annotations

import os
import sys
import time
from typing import TYPE_CHECKING

from google.genai.errors import ClientError

if TYPE_CHECKING:
    from umpscorecards.series import CompletedSeries

_DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
_DEFAULT_MAX_RETRIES = 3
_BACKOFF_BASE_SEC = 1.0
_BACKOFF_CAP_SEC = 60.0
_RETRY_AFTER_CAP_SEC = 300.0


def _resolve_gemini_model(model: str | None) -> str:
    """CLI ``--model`` or ``GEMINI_MODEL``; treat empty string as unset.

    GitHub Actions often sets ``GEMINI_MODEL: ${{ vars.FOO }}`` which yields ``""``
    when the var is missing, and ``dict.get(..., default)`` does not apply.
    """
    if model is not None and str(model).strip():
        return str(model).strip()
    env = (os.environ.get("GEMINI_MODEL") or "").strip()
    return env or _DEFAULT_GEMINI_MODEL


def _resolve_max_retries() -> int:
    """``GEMINI_MAX_RETRIES``: extra attempts after the first failure (default 3 → up to 4 tries)."""
    raw = (os.environ.get("GEMINI_MAX_RETRIES") or "").strip()
    if not raw:
        return _DEFAULT_MAX_RETRIES
    try:
        n = int(raw, 10)
    except ValueError:
        return _DEFAULT_MAX_RETRIES
    return max(0, n)


def _retry_after_seconds(exc: ClientError) -> float | None:
    r = getattr(exc, "response", None)
    if r is None:
        return None
    headers = getattr(r, "headers", None)
    if not headers:
        return None
    raw = headers.get("Retry-After") or headers.get("retry-after")
    if raw is None:
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _sleep_before_retry(attempt_index: int, exc: ClientError) -> None:
    """``attempt_index`` is 0 on the first post-failure wait."""
    backoff = min(_BACKOFF_CAP_SEC, _BACKOFF_BASE_SEC * (2**attempt_index))
    retry_after = _retry_after_seconds(exc) or 0.0
    wait = min(_RETRY_AFTER_CAP_SEC, max(backoff, retry_after))
    time.sleep(wait)


def build_prompt(stats: dict) -> str:
    total = stats["total_cle_favor"]
    if total > 0:
        lean = "favored Cleveland in aggregate run expectancy"
    elif total < 0:
        lean = "favored the opposition in aggregate run expectancy"
    else:
        lean = "was effectively neutral in aggregate run expectancy"
    return (
        f"You are writing for a Cleveland Guardians baseball blog.\n"
        f"Facts (do not invent numbers): {stats!r}\n"
        f"The total Cleveland-centric favor sum is {total}; this {lean}.\n"
        f"Write exactly two sentences: witty, clear, and grounded only in the facts above."
    )


def summarize_series_gemini(series: CompletedSeries, *, model: str | None = None) -> str:
    """Call Gemini via ``google-genai``; requires ``GEMINI_API_KEY``.

    Retries on **429** (quota / rate limit) or **503** (transient overload) up to
    ``GEMINI_MAX_RETRIES`` times after the first failure, with backoff. If errors
    persist, falls back to :func:`template_summary` and prints a short warning to
    stderr unless ``GEMINI_STRICT=1`` (then re-raises the last error).
    """
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    m = _resolve_gemini_model(model)
    client = genai.Client(api_key=api_key)
    prompt = build_prompt(series.to_llm_context())
    strict = os.environ.get("GEMINI_STRICT", "").lower() in ("1", "true", "yes")
    max_retries = _resolve_max_retries()

    last_exc: ClientError | None = None
    for attempt in range(max_retries + 1):
        try:
            response = client.models.generate_content(
                model=m,
                contents=prompt,
                config=types.GenerateContentConfig(temperature=0.3),
            )
        except ClientError as e:
            last_exc = e
            code = getattr(e, "code", None)
            if code not in (429, 503):
                raise
            if attempt >= max_retries:
                break
            _sleep_before_retry(attempt, e)
            continue

        text = getattr(response, "text", None)
        if not text or not str(text).strip():
            raise RuntimeError("Empty completion from Gemini")
        return str(text).strip()

    assert last_exc is not None
    code = getattr(last_exc, "code", None)
    if strict:
        raise last_exc
    reason = "quota or rate limit" if code == 429 else "temporary overload"
    print(
        f"Warning: Gemini HTTP {code} ({reason}) for model {m!r}; "
        f"using template summary. "
        f"Try --skip-llm, another --model, or check billing/quotas. "
        f"See https://ai.google.dev/gemini-api/docs/rate-limits",
        file=sys.stderr,
    )
    return _template_with_api_note(series, note=f"Gemini API returned HTTP {code} ({reason}).")


def _template_with_api_note(series: CompletedSeries, *, note: str) -> str:
    s = series.to_llm_context()
    return (
        f"The Guardians played {s['game_count']} game(s) against {s['opponent']}; "
        f"UmpScorecards total Cleveland-centric favor was {s['total_cle_favor']}. "
        f"({note})"
    )


def template_summary(series: CompletedSeries) -> str:
    """Deterministic fallback when LLM is skipped or API key is missing."""
    s = series.to_llm_context()
    return (
        f"The Guardians played {s['game_count']} game(s) against {s['opponent']}; "
        f"UmpScorecards total Cleveland-centric favor was {s['total_cle_favor']}. "
        f"(LLM summary skipped.)"
    )
