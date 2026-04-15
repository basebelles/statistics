"""LLM-generated two-sentence series summary."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from umpscorecards.series import CompletedSeries


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


def summarize_series_openai(series: CompletedSeries, *, model: str | None = None) -> str:
    """Call OpenAI Chat Completions; requires ``OPENAI_API_KEY``."""
    from openai import OpenAI

    client = OpenAI()
    stats = series.to_llm_context()
    m = model or os.environ.get("OPENAI_MODEL", "gpt-4o")
    resp = client.chat.completions.create(
        model=m,
        temperature=0.3,
        messages=[
            {
                "role": "user",
                "content": build_prompt(stats),
            }
        ],
    )
    text = resp.choices[0].message.content
    if not text:
        raise RuntimeError("Empty completion from OpenAI")
    return text.strip()


def template_summary(series: CompletedSeries) -> str:
    """Deterministic fallback when LLM is skipped."""
    s = series.to_llm_context()
    return (
        f"The Guardians played {s['game_count']} game(s) against {s['opponent']}; "
        f"UmpScorecards total Cleveland-centric favor was {s['total_cle_favor']}. "
        f"(LLM summary skipped.)"
    )
