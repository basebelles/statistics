# BaseBelles Stats — pluggable statistics monitors

Python package built around a small **pipeline** abstraction: fetch raw rows → **normalize** → **discover emittable events** → **summarize** (OpenAI or template) → write **artifacts** with **deduped state**.

The first shipped pipeline is **Guardians UmpScorecards** (completed series, Cleveland-centric favor). The same machinery can back **batting**, **pitching**, or other feeds by registering another pipeline.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run locally

Default pipeline: `guardians-umpscorecards`. Defaults: last **14 days** ending today, state `state/guardians-umpscorecards.json`, output `artifacts/guardians-umpscorecards/`.

```bash
stat-monitor --days 14
# equivalent:
guardians-umpscorecards --days 14
# explicit window:
stat-monitor --start-date 2026-04-01 --end-date 2026-04-15
```

- `**OPENAI_API_KEY`:** if set, calls OpenAI (`gpt-4o` or `OPENAI_MODEL`). If unset, uses a deterministic template.
- `**--skip-llm`:** always use the template.
- `**--pipeline ID`:** choose a registered pipeline (see below).

### Adding another pipeline (batting, pitching, …)

1. Implement `stats_agent.core.protocols.StatPipeline` (see `[src/stats_agent/core/protocols.py](src/stats_agent/core/protocols.py)`): `fetch_raw`, `normalize`, `discover_emittables`, `summarize`, `write_artifact`.
2. Define event objects that implement `Emittable` (`emission_key`, `to_llm_context`).
3. At **import time**, call `stats_agent.core.registry.register_pipeline(your_pipeline)`.
4. Import your module from `[src/stats_agent/cli.py](src/stats_agent/cli.py)` so the CLI sees the registration (same pattern as `import umpscorecards.pipeline`).
5. Run: `stat-monitor --pipeline your-pipeline-id` (optionally set `--state-path` / `--artifacts-dir` for isolation).

Shared pieces you reuse: `[stats_agent.core.runner.run_pipeline](src/stats_agent/core/runner.py)`, `[stats_agent.core.state](src/stats_agent/core/state.py)` for dedupe.

Reference implementation: `[src/umpscorecards/pipeline.py](src/umpscorecards/pipeline.py)`.

## Tests

```bash
pytest
```

## Automation (GitHub Actions)

Workflow: `[.github/workflows/umpscorecards.yml](.github/workflows/umpscorecards.yml)` runs the default pipeline on a schedule and `workflow_dispatch`.

- **State:** `state/guardians-umpscorecards.json` is cached between runs.
- **Artifacts:** Markdown under `artifacts/guardians-umpscorecards/` is uploaded.
- **Optional:** repository secret `OPENAI_API_KEY`, variable `OPENAI_MODEL`.

## Data notes (UmpScorecards pipeline)

`pybaseballstats` returns `home_team`, `away_team`, and `favor` (home-team run expectancy favor). The code maps that to Cleveland-centric `cle_favor`.

See `[docs/initial-plan.md](docs/initial-plan.md)` for the original design.