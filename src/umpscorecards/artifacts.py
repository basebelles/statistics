"""Write markdown artifacts for a completed series."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from umpscorecards.series import CompletedSeries


def _safe_slug(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", s)


def write_series_markdown(
    out_dir: Path,
    series: CompletedSeries,
    summary_text: str,
) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    end = str(series.games["date"].iloc[-1])
    stamp = _safe_slug(end)
    fname = f"{stamp}_{_safe_slug(series.opponent)}_series.md"
    path = out_dir / fname
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        f"# Guardians vs {series.opponent} (series)",
        "",
        f"- **Generated (UTC):** {generated}",
        f"- **Total CLE-centric favor:** {series.total_cle_favor:.3f}",
        f"- **Games:** {len(series.games)}",
        "",
        "## Summary",
        "",
        summary_text,
        "",
        "## Games",
        "",
    ]
    for _, row in series.games.iterrows():
        loc = (
            "home"
            if row["home_team"] == "CLE"
            else "away"
        )
        lines.append(
            f"- {row['date']} ({loc}) vs {row['opponent']}: "
            f"umpire {row['umpire']}, CLE favor {row['cle_favor']:.3f}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path
