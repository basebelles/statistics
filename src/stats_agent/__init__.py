"""Pluggable stat monitoring pipelines (fetch → normalize → events → summarize → artifacts)."""

from stats_agent.core.protocols import Emittable, StatPipeline
from stats_agent.core.registry import get_pipeline, list_pipelines, register_pipeline
from stats_agent.core.runner import RunResult, run_pipeline

__all__ = [
    "Emittable",
    "StatPipeline",
    "RunResult",
    "get_pipeline",
    "list_pipelines",
    "register_pipeline",
    "run_pipeline",
]
