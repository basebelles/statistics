"""Backward-compatible entrypoint; delegates to :mod:`stats_agent.cli`."""

from stats_agent.cli import main

__all__ = ["main"]

if __name__ == "__main__":
    raise SystemExit(main())
