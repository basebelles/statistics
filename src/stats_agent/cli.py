"""CLI for any registered :class:`stats_agent.core.protocols.StatPipeline`."""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

from dotenv import load_dotenv

# Register built-in pipelines (add more imports as you add modules).
import umpscorecards.pipeline  # noqa: F401

from stats_agent.core.registry import get_pipeline, list_pipelines
from stats_agent.core.runner import run_pipeline


def _default_dates(days: int) -> tuple[str, str]:
    end = date.today()
    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()


def main(argv: list[str] | None = None) -> int:
    # Load `.env` from the current working directory (does not override existing env vars).
    load_dotenv()
    argv = argv if argv is not None else sys.argv[1:]
    ids = sorted(list_pipelines().keys())
    default_id = "guardians-umpscorecards"

    p = argparse.ArgumentParser(
        description="Run a registered stat pipeline (fetch → events → summarize → artifacts)."
    )
    p.add_argument(
        "--pipeline",
        default=default_id,
        metavar="ID",
        help=f"Pipeline id (default: {default_id}). Registered: {', '.join(ids) or 'none'}",
    )
    p.add_argument(
        "--days",
        type=int,
        default=14,
        help="Rolling window ending today (if start/end omitted)",
    )
    p.add_argument("--start-date", dest="start_date", default=None, help="YYYY-MM-DD")
    p.add_argument("--end-date", dest="end_date", default=None, help="YYYY-MM-DD")
    p.add_argument(
        "--state-path",
        type=Path,
        default=None,
        help="JSON dedupe store (default: state/<pipeline-id>.json)",
    )
    p.add_argument(
        "--artifacts-dir",
        type=Path,
        default=None,
        help="Output directory (default: artifacts/<pipeline-id>/)",
    )
    p.add_argument(
        "--skip-llm",
        action="store_true",
        help="Use template text instead of Gemini",
    )
    p.add_argument(
        "--model",
        dest="llm_model",
        default=None,
        help="Override GEMINI_MODEL (default: gemini-2.5-flash)",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Ignore dedupe state and rewrite summaries for all events in this window",
    )
    args = p.parse_args(argv)

    if args.start_date and args.end_date:
        start, end = args.start_date, args.end_date
    elif not args.start_date and not args.end_date:
        start, end = _default_dates(args.days)
    else:
        p.error("Provide both --start-date and --end-date, or neither.")

    pipeline = get_pipeline(args.pipeline)
    state_path = args.state_path or Path("state") / f"{pipeline.id}.json"
    artifacts_dir = args.artifacts_dir or Path("artifacts") / pipeline.id

    result = run_pipeline(
        pipeline,
        start_date=start,
        end_date=end,
        state_path=state_path,
        artifacts_dir=artifacts_dir,
        skip_llm=args.skip_llm,
        llm_model=args.llm_model,
        force=args.force,
    )
    action = "rebuilt" if args.force else "new"
    print(
        f"[{pipeline.id}] {result.start_date} .. {result.end_date}: "
        f"{result.row_count} rows, {result.event_count} event(s) in window, "
        f"{result.new_artifacts} {action} artifact(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
