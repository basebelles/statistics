"""Register and resolve pipelines by id."""

from __future__ import annotations

from stats_agent.core.protocols import StatPipeline

_REGISTRY: dict[str, StatPipeline] = {}


def register_pipeline(pipeline: StatPipeline) -> StatPipeline:
    """Register a pipeline (typically at module import). Returns the same object."""
    pid = pipeline.id
    if pid in _REGISTRY:
        raise ValueError(f"Pipeline id already registered: {pid!r}")
    _REGISTRY[pid] = pipeline
    return pipeline


def get_pipeline(pipeline_id: str) -> StatPipeline:
    try:
        return _REGISTRY[pipeline_id]
    except KeyError as e:
        known = ", ".join(sorted(_REGISTRY)) or "(none)"
        raise KeyError(
            f"Unknown pipeline {pipeline_id!r}. Registered: {known}"
        ) from e


def list_pipelines() -> dict[str, StatPipeline]:
    return dict(_REGISTRY)
