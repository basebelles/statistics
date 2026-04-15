"""Protocols for pluggable stat pipelines (UmpScorecards, future batting/pitching, etc.)."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

import pandas as pd
from pathlib import Path


@runtime_checkable
class Emittable(Protocol):
    """One unit of output (e.g. a completed series, weekly rollup, milestone).

    Used for deduplication and LLM context. Implementations can be dataclasses.
    """

    @property
    def emission_key(self) -> str:
        """Stable id across runs; must be unique per logical event."""
        ...

    def to_llm_context(self) -> dict[str, Any]:
        """Structured facts for summarization (no prose rules here)."""
        ...


class StatPipeline(Protocol):
    """End-to-end pipeline for one stat domain and scope (team + source).

    Add a new pipeline by implementing this protocol and calling
    ``register_pipeline`` at import time (see ``umpscorecards.pipeline``).
    """

    @property
    def id(self) -> str:
        """Stable slug, e.g. ``guardians-umpscorecards`` or ``guardians-batting-weekly``."""
        ...

    @property
    def label(self) -> str:
        """Human-readable name for CLI help."""
        ...

    def fetch_raw(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Pull raw rows for the date window (API, CSV, scraper, etc.)."""
        ...

    def normalize(self, raw: pd.DataFrame) -> pd.DataFrame:
        """Canonical columns and sorts for this pipeline’s event detection."""
        ...

    def discover_emittables(self, normalized: pd.DataFrame) -> list[Emittable]:
        """Find events worth summarizing (series complete, week closed, etc.)."""
        ...

    def summarize(
        self,
        event: Emittable,
        *,
        skip_llm: bool,
        openai_model: str | None,
    ) -> str:
        """Produce short text (LLM or template)."""
        ...

    def write_artifact(
        self,
        event: Emittable,
        summary: str,
        out_dir: Path,
    ) -> Path:
        """Write markdown (or other) output; return path created."""
        ...
