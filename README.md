# BaseBelles Stats — pluggable statistics monitors

Python package built around a small **pipeline** abstraction: fetch raw rows → **normalize** → **discover emittable events** → **summarize** (Google Gemini or template) → write **artifacts** with **deduped state**.

The first shipped pipeline is **Guardians UmpScorecards** (completed series, Cleveland-centric favor). The same machinery can back **batting**, **pitching**, or other feeds by registering another pipeline.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### API key for local runs

The CLI loads a **`.env`** file from your **current working directory** (via `python-dotenv`). It does **not** override variables you already exported in the shell.

1. Copy [`.env.example`](.env.example) to `.env`.
2. Set `GEMINI_API_KEY=...` in `.env` (that file is gitignored).

Alternatively, run `export GEMINI_API_KEY=...` in your shell before `stat-monitor`.

## Run locally

Default pipeline: `guardians-umpscorecards`. Defaults: last **14 days** ending today, state `state/guardians-umpscorecards.json`, output `artifacts/guardians-umpscorecards/`.

```bash
stat-monitor --days 14
# equivalent:
guardians-umpscorecards --days 14
# explicit window:
stat-monitor --start-date 2026-04-01 --end-date 2026-04-15
```

- **`GEMINI_API_KEY`:** if set, calls Gemini (`gemini-2.5-flash` or `GEMINI_MODEL`). If unset, uses a deterministic template.
- **`GEMINI_INTER_REQUEST_DELAY_SEC`:** optional seconds to **sleep after each** LLM-backed artifact (default `0`) to reduce burst traffic on first runs. **`--gemini-inter-request-delay SEC`** overrides this when passed.
- **`GEMINI_MAX_RETRIES`:** how many **extra** attempts to make after a **429** or **503** from Gemini (default `3`, so up to **four** `generate_content` calls per series before falling back).
- **`--skip-llm`:** always use the template.
- **`--model`:** override the Gemini model (same as `GEMINI_MODEL`).
- **`--pipeline ID`:** choose a registered pipeline (see below).
- **`--force`:** ignore dedupe state and **regenerate** markdown for every completed event in the current date window (still saves state keys afterward).

### Gemini quota and HTTP 429

If the API returns **429 RESOURCE_EXHAUSTED** (free-tier quota, rate limits, or billing) or **503** after retries, the tool **prints a warning to stderr** and **uses the template summary** for that series so the run still finishes. To **fail without template fallback** on API errors instead, set **`GEMINI_STRICT=1`** (retries still run first).

To avoid quota issues: use **`--skip-llm`**, add a small **`GEMINI_INTER_REQUEST_DELAY_SEC`** or **`--gemini-inter-request-delay`** on large backfills, try another model (**`--model gemini-2.0-flash`**, etc.), enable billing in Google AI Studio, or see [Gemini rate limits](https://ai.google.dev/gemini-api/docs/rate-limits).

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
- **Optional:** repository secret `GEMINI_API_KEY`, variable `GEMINI_MODEL` (optional).

## Data notes (UmpScorecards pipeline)

`pybaseballstats` returns `home_team`, `away_team`, and `favor` (home-team run expectancy favor). The code maps that to Cleveland-centric `cle_favor`.

**Series grouping and the date window:** Opponent “series” are **consecutive games vs the same opponent** in time. If your rolling window **starts after** the first game(s) of a real series (e.g. Dodgers on Mar 30–31 with the last game Apr 1, but `--days 14` starts Apr 1), the code would only see one game vs that team. The pipeline therefore **fetches extra history**: by default it moves the API `start_date` back **21 days** before the CLI window (`GUARDIANS_UMPS_FETCH_LOOKBACK_DAYS` to override). That keeps full multi-game sets together for counting and summaries.

See `[docs/initial-plan.md](docs/initial-plan.md)` for the original design.
