"""Persistent deduplication of emitted events (any pipeline)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class RunState:
    # JSON field name kept for backward compatibility with older state files.
    emitted_series_keys: list[str]

    @classmethod
    def empty(cls) -> RunState:
        return cls(emitted_series_keys=[])

    def should_emit(self, key: str) -> bool:
        return key not in set(self.emitted_series_keys)

    def record(self, key: str) -> None:
        if key not in self.emitted_series_keys:
            self.emitted_series_keys.append(key)


def load_state(path: Path) -> RunState:
    if not path.exists():
        return RunState.empty()
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        # Empty or whitespace-only file (e.g. created by touch); treat as no history.
        return RunState.empty()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"State file is not valid JSON: {path}\n"
            f"Fix the file, delete it, or rename it to start with a fresh state.\n"
            f"Original error: {e}"
        ) from e
    keys = data.get("emitted_series_keys", [])
    return RunState(emitted_series_keys=list(keys))


def save_state(path: Path, state: RunState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")
