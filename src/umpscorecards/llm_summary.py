"""LLM-generated two-sentence series summary (Google Gemini)."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from umpscorecards.series import CompletedSeries

_DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"


def _resolve_gemini_model(model: str | None) -> str:
    """CLI ``--model`` or ``GEMINI_MODEL``; treat empty string as unset.

    GitHub Actions often sets ``GEMINI_MODEL: ${{ vars.FOO }}`` which yields ``""``
    when the var is missing, and ``dict.get(..., default)`` does not apply.
    """
    if model is not None and str(model).strip():
        return str(model).strip()
    env = (os.environ.get("GEMINI_MODEL") or "").strip()
    return env or _DEFAULT_GEMINI_MODEL


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

    On **429** (quota / rate limit) or **503** (transient overload), falls back to
    :func:`template_summary` and prints a short warning to stderr so the run can finish.
    Set ``GEMINI_STRICT=1`` to re-raise instead of falling back.
    """
    from google import genai
    from google.genai import types
    from google.genai.errors import ClientError

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    m = _resolve_gemini_model(model)
    client = genai.Client(api_key=api_key)
    prompt = build_prompt(series.to_llm_context())
    strict = os.environ.get("GEMINI_STRICT", "").lower() in ("1", "true", "yes")

    try:
        response = client.models.generate_content(
            model=m,
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.3),
        )
    except ClientError as e:
        code = getattr(e, "code", None)
        if not strict and code in (429, 503):
            reason = "quota or rate limit" if code == 429 else "temporary overload"
            print(
                f"Warning: Gemini HTTP {code} ({reason}) for model {m!r}; "
                f"using template summary. "
                f"Try --skip-llm, another --model, or check billing/quotas. "
                f"See https://ai.google.dev/gemini-api/docs/rate-limits",
                file=sys.stderr,
            )
            return _template_with_api_note(series, note=f"Gemini API returned HTTP {code} ({reason}).")
        raise
    text = getattr(response, "text", None)
    if not text or not str(text).strip():
        raise RuntimeError("Empty completion from Gemini")
    return str(text).strip()


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
