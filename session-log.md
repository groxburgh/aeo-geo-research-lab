# Session Log

Running log of changes and immediate next steps. Append after every significant change. Newest entries at the bottom.

Format for each entry:

```
## YYYY-MM-DD (Session identifier)

**What changed:**
- Concrete list of files modified, functions added, tests run, commits made.

**Verification:**
- How the change was confirmed (re-read file, ran script, ran test, manual smoke check).

**Next step:**
- Single clearest next action, pointing to a specific file or phase in PRD.md Section 8 where relevant.
```

---

## 2026-04-19 (Session 0: Planning)

**What changed:**
- Brainstorming session with operator completed.
- Project scoped. PRD.md, CLAUDE.md, decisions-log.md, .gitignore, .env.example drafted outside the repo and staged for placement in root on first commit.
- TECH-SPEC.md still to be drafted before first coding session.

**Verification:**
- Scope decisions recorded in decisions-log.md.
- Budget constraint ($40/month) confirmed with operator.
- Cross-engine coverage confirmed (ChatGPT, Perplexity, Claude). Google AI Mode excluded, Gemini deferred to V4.

**Next step:**
- Draft TECH-SPEC.md, then initialize the repo, place all source-of-truth docs in root, and begin Phase 1 of PRD.md Section 8 (Repo and Environment Setup).

---

## 2026-04-19 (Session 1: Pre-build documentation)

**What changed:**
- `env.example` renamed to `.env.example`; `gitignore` renamed to `.gitignore` (dot-prefix fix)
- `TECH-SPEC.md` created: full schema (4 tables), three engine API contracts, prompts.yaml structure, GitHub Actions workflow spec, Notion integration spec, run.py interface
- `README.md` created: project purpose, engine coverage table, replication guide
- `METHODOLOGY.md` created: full research protocol (query set, run protocol, prompt stability sub-study, citation normalization, statistical approach, known limitations, version history)
- `LICENSE` created: MIT, 2026, Greg Roxburgh
- `CLAUDE.md` created from `CLAUDE (1).md` with architecture context added; old file deleted
- `PRD.md` renamed from `AEO-GEO-RESEARCH-PRD.md`

**Verification:**
- All 9 root files present: CLAUDE.md, PRD.md, TECH-SPEC.md, README.md, METHODOLOGY.md, LICENSE, decisions-log.md, session-log.md, .env.example, .gitignore
- TECH-SPEC.md covers all four SQLite tables, three engine API contracts, and GitHub Actions workflow
- METHODOLOGY.md includes prompt stability sub-study section (research integrity requirement)

**Next step:**
- Initialize GitHub repo (git init, create remote, first commit with all current files)
- Begin PRD.md Section 8, Phase 1: Python project structure (/src, /prompts, /reports, /data, /tests), requirements.txt, requirements-dev.txt

---

## 2026-04-24 (Session 2: Phase 1 — Repo and Environment Setup)

**What changed:**
- `requirements.txt` created: 5 pinned production deps (anthropic, openai, requests, python-dotenv, pyyaml)
- `requirements-dev.txt` created: 4 pinned dev deps (pytest, pytest-cov, responses, ruff)
- Directory skeleton created: `/src`, `/src/engines`, `/prompts`, `/reports`, `/data`, `/tests`, `/tests/fixtures`, `/.github/workflows`
- `src/schema.sql` created: full DDL for all 4 tables (queries, runs, citations, costs) using `CREATE TABLE IF NOT EXISTS`
- `src/models.py` created: fully implemented `NormalizedResult` and `Citation` dataclasses including `Citation.extract_domain()` helper
- Stub `src/` modules created (raise NotImplementedError): `db.py`, `budget.py`, `runner.py`, `report.py`, `notifier.py`
- Stub engine modules created: `src/engines/base.py` (abstract `Engine` class), `openai_engine.py`, `perplexity_engine.py`, `anthropic_engine.py` — each with pricing constants
- `run.py` entry point created: routes `test`, `run`, `report`, `report --notify` subcommands; all return stub exit 1
- `.github/workflows/monthly-sweep.yml` created: full workflow per TECH-SPEC (cron trigger, all 9 steps, failure handler)
- 5 empty stub test files created in `/tests/`
- `CLAUDE.md` updated: Python 3.12 version, dev commands, `NOTION_REVIEW_DATABASE_ID` secret, module responsibility table, key invariants

**Verification:**
- `pip install -r requirements.txt` — succeeded (Python 3.14.2 in local env)
- `pip install -r requirements-dev.txt` — succeeded
- `python run.py` — prints usage, exits 1 ✓
- `python run.py test` — prints stub message, exits 1 ✓
- `pytest` — 0 tests collected, no errors ✓
- `ruff check src/` — all checks passed ✓

**Next step:**
- Phase 2: Draft `prompts/prompts.yaml` — 50-60 queries across three ICP zones, tagged by zone and query_type, with 5 stability-variant pairs flagged

---

## 2026-04-25 (Session 3: Phase 2 — Query Set)

**What changed:**
- `prompts/prompts.yaml` created: 59 total entries (54 canonical + 5 stability variants)
- 18 canonical queries per zone: content-operations, b2b-saas-fintech, aeo-geo
- 5 stability-test canonical queries flagged (spread across all three zones): co-what-is-content-ops, saas-ai-marketing-tools, geo-what-is, geo-chatgpt-vs-perplexity, geo-original-research
- 5 corresponding reworded variants created with `is_variant: true` and correct `variant_of` references
- All IDs unique; all variant_of references resolve; YAML parses cleanly with yaml.safe_load
- Note: `zone` and `query_type` fields included in YAML per PRD Phase 2 Step 6 but not yet in `queries` DB table — will add as append-only columns in Phase 4 when db.py is implemented

**Verification:**
- `python3 -c "import yaml; yaml.safe_load(open('prompts/prompts.yaml'))"` — parses cleanly ✓
- 54 canonical, 5 variants, 18 per zone, 0 duplicate IDs, 0 bad variant refs ✓

**Next step:**
- Phase 3: Engine integrations — implement `src/engines/openai_engine.py`, `perplexity_engine.py`, `anthropic_engine.py`, then `src/db.py` and the `run.py test` pre-flight check

---

## 2026-04-26 (Session 4: Phase 3 — Engine Integrations and Data Layer)

**What changed:**
- `src/schema.sql` updated: added `zone` and `query_type` columns to `queries` table (append-only, default empty string)
- `src/db.py` implemented: `apply_schema`, `insert_query`, `run_exists`, `insert_result`, `get_month_cost`, and three read functions for report generation
- `src/budget.py` implemented: `check_budget` uses `get_month_cost`; returns False when spend >= budget
- `src/engines/openai_engine.py` implemented: Responses API, web_search_preview tool, citation extraction from web_search_call items
- `src/engines/perplexity_engine.py` implemented: plain requests POST to Sonar API, citation extraction from flat citations array
- `src/engines/anthropic_engine.py` implemented: Messages API with web_search_20250305 tool, citation extraction from web_search_result blocks
- `run.py` updated: `test` command fully implemented (env vars, prompts.yaml, DB schema, live engine connectivity); `load_dotenv('.env.local')` added at startup
- `tests/fixtures/` populated with three recorded-style API response fixtures
- `tests/test_db.py`, `tests/test_budget.py`, `tests/test_engines.py` fully implemented

**Verification:**
- `pytest tests/test_db.py tests/test_budget.py tests/test_engines.py -v` — 18/18 passed ✓
- `ruff check src/ tests/` — clean ✓
- `python run.py test` (live) — all 6 checks passed ✓

**Next step:**
- Phase 5: Implement `src/runner.py` (full sweep orchestration) and `run.py run` command, then Phase 5 report generation (`src/report.py`) and `run.py report`

---

## 2026-04-26 (Session 5: Phase 5 — Runner and Report)

**What changed:**
- `src/runner.py` implemented: full sweep loop (59 queries × 3 engines × 3 runs), circuit breaker check before every call, idempotency via `run_exists`, GitHub Actions env var output
- `src/report.py` implemented: 7-section markdown report (header, budget, per-engine citation frequency, cross-engine overlap, prompt stability Jaccard, model versions, raw run log)
- `run.py` updated: `run` and `report` commands wired; `report --notify` calls notifier stub non-fatally
- `tests/test_runner.py`: 3 tests (writes results, skips duplicates, returns exit 2 on budget breach)
- `tests/test_report.py`: 4 tests (file created, sections present, idempotent, Jaccard correct)

**Verification:**
- `pytest` — 25/25 passed ✓
- `ruff check src/ tests/` — clean ✓

**Next step:**
- Run `python run.py run` locally (first live full sweep, ~$0.30, ~486 API calls)
- Then `python run.py report` to generate first monthly report
- Phase 6: GitHub Actions workflow smoke-test via workflow_dispatch
- Phase 7: Implement `src/notifier.py` (Notion review gate)

---

## 2026-05-02 (Session 6: First production run — push failure and budget fix)

**What changed:**
- `.github/workflows/monthly-sweep.yml`: added `permissions: contents: write` and `issues: write` to the `sweep` job — fixes 403 push failure caused by default read-only GITHUB_TOKEN
- `src/engines/anthropic_engine.py`: added `WEB_SEARCH_COST = 0.010` constant and updated cost calculation to count `tool_use` blocks with `name == "web_search"` — fixes budget undercount (~$0.01/search was not tracked)

**What happened on the first run:**
- All pipeline steps succeeded (validate, run, generate report, commit results)
- Push failed with exit code 128: `Permission to groxburgh/aeo-geo-research-lab.git denied to github-actions[bot]`
- The local commit in the runner was lost — the DB changes from this run are not in the repo
- Claude API consumed ~4.7M input tokens, ~236K output tokens, 277 web searches (expected for 59 queries × 3 runs)
- The $40 budget circuit breaker was not triggered; run completed normally

**Verification:**
- Workflow YAML re-read; permissions block present ✓
- `anthropic_engine.py` re-read; cost formula includes web search term ✓

**Next step:**
- Commit and push these fixes
- Re-trigger the workflow via `workflow_dispatch` to re-run the May 2026 sweep (previous run data was not persisted)

---

## 2026-05-13 (Session 9: Post-audit fixes — idempotency, citation extraction hardening, report quality)

**What changed:**
- `src/engines/anthropic_engine.py`: Added rate-limit retry (3 attempts, 5/10/20s exponential backoff). Replaced `result.type == "web_search_result"` type check with defensive URL-presence check (`getattr(result, "url", None)`) to capture citations regardless of SDK deserialisation variance. Added `_MAX_RETRIES` and `_RETRY_BASE_DELAY` constants. `model_version` in error handler changed from `"unknown"` to `"error:no-response"`.
- `src/engines/openai_engine.py`: Pinned model to `"gpt-4o-2024-11-20"` (previously `"gpt-4o"` which resolved to `gpt-4o-2024-08-06`, a checkpoint predating `web_search_preview` support). `model_version` in error handler changed to `"error:no-response"`.
- `src/engines/perplexity_engine.py`: `model_version` in error handler changed to `"error:no-response"`.
- `src/db.py`: `run_exists` query now includes `AND error IS NULL` — error rows no longer block retries. New `clear_error_run()` function deletes error rows (and their cost rows) before retry to avoid UNIQUE constraint violations.
- `src/runner.py`: Calls `db.clear_error_run()` immediately before `db.run_exists()` on every iteration.
- `src/report.py`: Added `_INVALID_DOMAINS` frozenset (co.uk, org.uk, and other eTLD-impersonating fragments) filtered from citation frequency tables. Added zero-citation engine notes to Cross-Engine Overlap and Prompt Stability sections.
- `TECH-SPEC.md`: Corrected §5.1 (ChatGPT citation extraction description) and §5.3 (Claude citation extraction description) to match actual code; corrected model pin and max_uses.
- `METHODOLOGY.md`: Corrected citation extraction descriptions for ChatGPT and Claude; updated citation extraction table; added COI disclosure section; added Version History 1.1 row.
- `tests/test_db.py`: Added `_make_result()` helper and `_QUERY` constant. Added three new tests: `test_run_exists_false_for_error_row`, `test_clear_error_run_removes_error_row`, `test_clear_error_run_noop_for_success`.
- `tests/test_runner.py`: Added `test_sweep_retries_error_rows` verifying that error rows are cleared and retried on subsequent sweep.

**Root cause summary:**
May 2026 data showed 0 citations for ChatGPT (wrong model checkpoint, web search not invoked) and Claude (SDK type mismatch in citation extraction + 79 errors from probable rate limiting). The db.run_exists bug meant those error rows blocked automatic retry. This session fixes all three root causes plus the co.uk domain contamination in reports and the stale documentation.

**Verification:**
- `ruff check src/ tests/` — clean ✓
- `pytest` — 30/30 passed (4 new tests) ✓

**Next step:**
- `python run.py run --engine claude` to retry the 79 May 2026 error rows
- `python run.py report` to regenerate the May 2026 report with full Claude data

---

## 2026-05-19 (Session 10: Pipeline remediation — schema v2, tldextract, quarantine, max_uses)

**What changed:**
- `src/schema.sql`: Added `extraction_version`, `citations_extracted`, `quarantined`, `quarantine_reason` columns to `runs`. Replaced inline `UNIQUE` constraint with a partial unique index `WHERE quarantined = 0` (allowing a quarantined row and a fresh replacement to coexist in the same slot). Added `domain_v2` and `normalization_version` to `citations`. Added `runs_active` view (filters `quarantined = 0`).
- `src/domain_normalizer.py`: New module. Wraps `tldextract.TLDExtract` with offline-safe config (`suffix_list_urls=()`, committed cache, bundled snapshot fallback). Exposes `normalize_domain(url) -> str | None` and `EXTRACTION_VERSION = "v2-tldextract-5.3"`. Correctly handles ccSLDs (`bbc.co.uk → bbc.co.uk`) and strips `co.uk`/`org.uk` bare-suffix artifacts to `None`.
- `src/models.py`: `Citation.extract_domain()` now delegates to `normalize_domain()`. The `urlparse` split is gone.
- `src/db.py`: `run_exists()` widened to check `quarantined=0` and `model_version` against `_CURRENT_MODELS` dict — rows from a wrong model snapshot are automatically invisible and will be re-fetched. New `quarantine_runs()` function. `insert_result()` now writes `extraction_version` and `citations_extracted` on every run, and `domain_v2` + `normalization_version` on every citation. All report-facing read functions (`get_runs_for_month`, `get_citations_for_month`) target `runs_active` view.
- `src/report.py`: Removed `_INVALID_DOMAINS` frozenset (superseded by tldextract). Citation frequency and overlap tables now use `domain_v2` (falls back to legacy `domain` for pre-migration rows). Cross-engine overlap section dynamically labels by actual engine count (2-engine: "Cited by both engines"; n-engine: "Cited by all N engines"). Run index pre-built for O(1) citation→run lookup.
- `src/engines/anthropic_engine.py`: `max_uses` raised from 1 to 3. Comment updated with monthly cost estimate (~$5 additional at max invocations).
- `requirements.txt`: Added `tldextract==5.3.1`.
- `.cache/tldextract/`: Vendored PSL snapshot committed to repo. Offline-safe; no network calls during GitHub Actions runs.
- `.gitignore`: Documented that `.cache/tldextract/` is intentionally committed.
- `scripts/migrate_v2.py`: New one-time migration script. Recreates `runs` table with new columns and partial index; adds `citations` columns; quarantines all 177 May 2026 ChatGPT rows (170 × gpt-4o-2024-08-06 + 7 × gpt-4o-2024-11-20 partial re-run); backfills `domain_v2` for all 2144 existing citations; creates `runs_active` view.
- `tests/test_db.py`: Three new tests: `test_run_exists_false_when_model_version_differs`, `test_run_exists_false_when_quarantined`, `test_quarantine_runs_returns_row_count`.
- `tests/test_domain_normalizer.py`: New file. 11 tests covering standard domains, subdomains, UK/AU ccSLDs, bare TLDs (→ None), empty inputs.
- `tests/test_runner.py`: Fixed `_ENGINE_MODELS` dict in `_make_result` so mock runs use the current pinned model version per engine (required by new `run_exists` predicate).

**Verification:**
- `ruff check src/ tests/ scripts/` — clean ✓
- `pytest` — 44/44 passed ✓
- `python scripts/migrate_v2.py` — 177 rows quarantined, 2144 citations backfilled, 0 null domains ✓
- `python run.py report` — May 2026 report regenerated ✓
  - `co.uk` and `org.uk` artifact domains absent ✓
  - "Engines covered: claude, perplexity" (ChatGPT correctly absent) ✓
  - Cross-engine overlap now reads "Cited by both engines (58)" — 2-engine framing ✓

**Next step:**
- Commit all changes and push
- June 2026 sweep is the first valid month for cross-engine comparison
- After June run, calibrate Claude citation yield at `max_uses=3` vs the May `max_uses=1` baseline

---

## 2026-05-13 (Session 8: Citation extraction bug fixes)

**What changed:**
- `src/engines/openai_engine.py`: Fixed citation extraction — citations are `url_citation` annotations on `output_text` content parts inside `message` items, not on `web_search_call.results` (which doesn't exist in the real API). Added `logger.exception` to the error handler.
- `src/engines/anthropic_engine.py`: Fixed citation extraction — citations live in `web_search_tool_result` blocks → `content` list → `web_search_result` items. Updated `web_search_uses` count to check for `server_tool_use` block type (not `tool_use`). Added `logger.exception` to the error handler.
- `requirements.txt`: Upgraded `anthropic` from `0.49.0` to `0.56.0`. SDK 0.49.0 had no typed classes for web search result blocks (`ServerToolUseBlock`, `WebSearchToolResultBlock`, `WebSearchResultBlock`); these were added in 0.56.0 and are required for correct citation extraction.
- `tests/fixtures/openai_response.json`: Updated to reflect the real Responses API response shape (annotations on output_text, no `results` on web_search_call).
- `tests/fixtures/anthropic_response.json`: Updated to reflect the real Messages API response shape (server_tool_use + web_search_tool_result + text blocks).
- `tests/test_engines.py`: Updated `_build_openai_mock` and `_build_anthropic_mock` to match corrected fixture structures.
- `scripts/dump_engine_responses.py`: New diagnostic script (one-off) that sends a single query to all three engines and dumps raw responses to `scripts/raw_responses/`. Not a permanent test harness. Could not be run locally due to SSL certificate issue; SDK type inspection used as ground truth instead.

**Root cause summary:**
The previous fixtures were written to match the broken extraction code rather than the real API, so unit tests passed while live runs returned 0 citations. The core issues: (1) OpenAI Responses API returns citations as `url_citation` annotations on response text, not as results on the search call item; (2) Anthropic Messages API returns web search results as `web_search_tool_result` blocks requiring SDK ≥ 0.56.0 to parse.

**Verification:**
- `ruff check src/ tests/` — clean ✓
- `pytest` — 26/26 passed ✓
- End-to-end live verification deferred to GitHub Actions workflow_dispatch (local API calls blocked by SSL certificate issue in local environment)

**Next step:**
- Commit and push these fixes
- Trigger `workflow_dispatch` to re-run the June 2026 sweep and verify non-zero citations from all three engines
- Check GitHub Actions logs for any Anthropic errors — they will now surface with full tracebacks instead of being silently swallowed

---

## 2026-05-02 (Session 7: Resilience and budget fixes)

**What changed:**
- `run.py`: added `--engine <name>` optional argument to the `run` command; updated USAGE string
- `src/runner.py`: added `engine_filter` parameter; reordered `_ENGINES` cheapest-first (perplexity → chatgpt → claude); only instantiates engine clients for the active set
- `.github/workflows/monthly-sweep.yml`: extracted "Configure git" to a dedicated early step; split "Run pipeline" into three per-engine steps with `continue-on-error` checkpoint pushes between them; added `if: always()` to "Commit results" and "Push" so partial Claude data is never lost
- `src/engines/anthropic_engine.py`: reduced `max_uses` from 3 to 1 (budget + methodological consistency)
- `tests/test_runner.py`: added `test_sweep_engine_filter_runs_only_selected_engine` (passes)
- `decisions-log.md`: logged max_uses decision with full rationale

**Verification:**
- `pytest` — 26/26 passed ✓
- Engine filter test confirms MockOpenAI and MockAnthropic never instantiated when filter="perplexity" ✓

**Next step:**
- Commit and push, then trigger `workflow_dispatch` to run the May 2026 sweep
- After run completes, verify three checkpoint commits appear in git log and Perplexity + ChatGPT data is in repo before Claude finishes

---

## 2026-06-23 (Session 11: Pre-run audit and June 2026 sweep unblocking)

**What changed:**
- `.github/workflows/monthly-sweep.yml`: Added `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` to top-level `env` block — opts into Node.js 24 before GitHub's forced cutover on 2026-06-16 (already in effect; without this the actions/checkout@v4 and actions/setup-python@v5 steps emit deprecation warnings)
- `scripts/patch_fk_refs.py`: New one-time patch script. Recreated `citations` and `costs` tables with correct `REFERENCES runs(run_id)`. Root cause: SQLite 3.26.0+ automatically rewrites FK references in sibling tables when `ALTER TABLE x RENAME TO y` is executed. `migrate_v2.py` renamed `runs → runs_old`, so SQLite silently updated both child tables to reference `runs_old`. After `DROP TABLE runs_old`, the FKs were dangling — causing `sqlite3.OperationalError: no such table: main.runs_old` whenever `PRAGMA foreign_keys = ON` triggered a FK check. Patch confirmed: 2144 citations and 531 costs rows intact after fix.
- `data/observatory.db`: FK references in citations and costs corrected (runs_old → runs).

**Pre-run audit findings:**
- June 2026 starts at $0 spend; ~$25-30 projected for first full 3-engine run
- All 177 May ChatGPT runs quarantined (wrong model checkpoint); June is first valid 3-engine month
- Claude produces 0 citations for all 18 co-* canonical queries — confirmed as real research signal (no web search invocation, not an extraction bug)
- `citations_extracted` column is 0 for all May Claude rows — migration backfill gap; does not affect June data quality
- GitHub secrets `OPENAI_API_KEY` and `ANTHROPIC_API_KEY` were stale; Greg updated them in repo settings

**Verification:**
- `scripts/patch_fk_refs.py` run locally: citations FK = 'runs' ✓, costs FK = 'runs' ✓, 2144 citations and 531 costs rows intact ✓
- ruff not re-run (no src/ changes this session)

**Next step:**
- Commit: `git add data/observatory.db .github/workflows/monthly-sweep.yml scripts/patch_fk_refs.py session-log.md`
- Push and re-trigger `workflow_dispatch` for the June 2026 sweep
- After run: `python run.py report` to generate reports/2026-06.md (first month with all 3 engines)
