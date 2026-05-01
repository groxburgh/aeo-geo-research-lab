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
