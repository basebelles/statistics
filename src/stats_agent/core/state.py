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
    data = json.loads(path.read_text(encoding="utf-8"))
    keys = data.get("emitted_series_keys", [])
    return RunState(emitted_series_keys=list(keys))


def save_state(path: Path, state: RunState) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(state), indent=2), encoding="utf-8")
