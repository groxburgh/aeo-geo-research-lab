# Product Requirements Document
## AEO/GEO Primary Research Observatory

**Repo (placeholder):** `aeo-geo-research-lab`
**Last Updated:** 2026-04-19
**Status:** V1 Scoping Complete, Ready for Build

---

## 1. Problem Statement

Publicly available AEO/GEO research comes from three kinds of publishers: academic papers with narrow scope and infrequent updates, enterprise platform vendors whose datasets are proprietary and commercially conflicted, and agencies running one-shot studies behind lead-gen walls. None of these publish an ongoing, methodologically transparent, cross-engine, longitudinal dataset for any specific niche.

This project fills that gap for three related zones: content operations and marketing, B2B SaaS and fintech, and AEO/GEO itself. These zones directly serve the operator's consulting ICP and positioning, and they are defensible for a solo-run research project at small scale because depth and continuity compensate for limited sample size.

---

## 2. Business Vision

A public GitHub repository that functions as both the research instrument and the research artifact. Each month, a scheduled GitHub Actions workflow runs a fixed query set across three AI engines, normalizes the citation output, writes raw data to a version-controlled SQLite database, and generates a markdown report committed back to the repo. Methodology is public from day one. The dataset grows month over month, producing a longitudinal record no current competitor publishes openly.

The research output serves two purposes. It is a credibility asset for the operator's content operations consulting practice: proof that the methodology is rigorous and the findings are honest. It is also a proof-of-concept for a productized commercial offer: bespoke AEO/GEO research engagements for prospects who want the same methodology applied to their own category or content set.

---

## 3. Target User

**Primary operator:** Greg Roxburgh, solo content operations consultant based in Seoul. Responsible for running monthly reviews, interpreting findings, and publishing analyses.

**Primary audience:** Content operations leaders, SEO and GEO practitioners, and marketing strategists at B2B SaaS and fintech companies that match the operator's ICP (50 to 500 employees, Series A to C). They care about which AI engines to optimize for, how stable citation behavior is month over month, and how to design content for AI visibility.

**Secondary audience:** Prospects evaluating the operator for retainer or bespoke research work. They use the repo as a methodology audit before engaging.

---

## 4. User Stories

### V1: Monthly Public Observatory (Current)
- [ ] As the operator, the full query set runs automatically on the first of each month across three AI engines (ChatGPT, Perplexity, Claude).
- [ ] As the operator, each query runs at least three times per engine per month so the report can present distributions rather than point estimates.
- [ ] As the operator, raw results are normalized and committed to a SQLite database stored in the repo.
- [ ] As the operator, a monthly report is auto-generated in markdown and committed to `/reports/YYYY-MM.md`.
- [ ] As the operator, a summary of each generated report is posted to a Notion database as a review gate before I announce externally.
- [ ] As the operator, API cost is tracked per run and a monthly total is logged in the report.
- [ ] As a reader, the full methodology is documented in the repo README and `METHODOLOGY.md`.
- [ ] As a reader, I can clone the repo and replicate the study with my own API keys.

### V2: Controlled A/B Experiments (Scaffolded)
- [ ] As the operator, I can register a test URL of my own and track its citation rate baseline.
- [ ] As the operator, I can log a structural modification to that URL and schedule a follow-up measurement.
- [ ] As the operator, the report distinguishes descriptive findings from controlled-experiment findings.

### V3: Productized Bespoke Research (Scaffolded)
- [ ] As the operator, I can run a custom query set for a paying client using the same infrastructure.
- [ ] As the operator, client data stays in a private branch or separate repo and is never published.
- [ ] As the operator, client deliverables are generated using the same report template as public runs.

### V4: Expanded Engine Coverage (Scaffolded)
- [ ] As the operator, Gemini is added as a fourth engine once its API grounding output stabilizes.
- [ ] As the operator, Google AI Mode is added if a compliant access path emerges.

---

## 5. Definition of Done (V1)

- [ ] Public GitHub repo created with a permissive license (MIT recommended).
- [ ] `README.md` describes purpose, methodology summary, and how to replicate.
- [ ] `METHODOLOGY.md` documents query construction, run protocol, engines, normalization rules, cost model, and known limitations.
- [ ] `prompts.yaml` contains the full 50-to-60 query set across three zones, tagged by zone and query type.
- [ ] Python integration with OpenAI API (ChatGPT with web search), Perplexity Sonar API, and Anthropic API (Claude with web search tool) all pass a connectivity test.
- [ ] SQLite schema created. Tables for runs, citations, queries, and costs.
- [ ] GitHub Actions workflow runs on schedule (first of month) and commits results back to the repo.
- [ ] First monthly report generated, reviewed, and published externally.
- [ ] Notion review-gate integration functional.
- [ ] Total cost for a full run confirmed under $40.
- [ ] No API keys exposed in logs, commits, or public files.

---

## 6. Out of Scope (V1)

- Google AI Mode (no API available)
- Gemini (deferred to V4 pending grounding reliability assessment)
- Controlled A/B experiments on operator-owned URLs (V2)
- Automated publishing of reports to LinkedIn or newsletter (manual publication only)
- Public dashboard or visualization layer
- Bespoke paid client engagements (V3 commercial output)
- Broad-corpus diverse queries outside the three ICP zones
- Sponsored or funded research in V1 (maintains editorial independence during proof-of-concept phase)

---

## 7. Research Integrity Principles

These principles are non-negotiable. They are what makes this project defensible at small scale. Every build and editorial decision must respect them.

1. **Three runs minimum.** Every query runs at least three times per engine per month. Reports use distributions (median, range, variance) rather than single-run point estimates. AI citation sets are known to be volatile between runs; single-run data is noise.

2. **Methodology public from day one.** The prompt set, run protocol, model versions, normalization rules, and any changes are version-controlled in the repo. The research is auditable.

3. **Null findings publish.** Months where no meaningful pattern emerges are reported as such. No selection bias toward positive findings. An explicit "no significant change from last month" section appears in every report when applicable.

4. **Scope honesty.** Every claim is framed with its scope: "in the content operations zone," "across ChatGPT, Perplexity, and Claude," "within the April 2026 dataset." No extrapolation to verticals or engines not tested.

5. **Prompt stability sub-study.** Each month, at least five queries are run with minor rewording variants to quantify prompt-variation sensitivity. This is a field gap the project explicitly addresses.

6. **Model version pinning.** Model versions are recorded for every run. Observed changes in model behavior are flagged as a confound, not ignored.

---

## 8. Living Project Plan

Ordered by dependency. Each phase builds on the previous.

### Phase 1: Repo and Environment Setup

- [ ] 1. **Create public GitHub repo.** Initialize `README.md`, `.gitignore`, `LICENSE`, `.env.example`.
- [ ] 2. **Python project structure.** Create `/src`, `/prompts`, `/reports`, `/data`, `/tests`. `requirements.txt` pins versions of openai, anthropic, requests, python-dotenv, pyyaml.
- [ ] 3. **Secrets configuration.** GitHub Secrets for `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `PERPLEXITY_API_KEY`, `NOTION_API_KEY`. Never committed. `.env.local` for local development, gitignored.
- [ ] 4. **Cost guardrail env var.** `MONTHLY_BUDGET_USD=40` defined in workflow config so runs can self-abort if they exceed budget.

### Phase 2: Query Set

- [ ] 5. **Draft the query set.** Target 50 to 60 queries. Roughly balanced across three zones: content operations and marketing, B2B SaaS and fintech, AEO/GEO itself.
- [ ] 6. **Tag each query.** Fields: `id`, `zone`, `query_type` (commercial, informational, comparison, how-to, navigational), `notes`. Store in `prompts.yaml`.
- [ ] 7. **Select stability-test queries.** Flag 5 queries that will be run each month with minor rewording variants for the prompt-stability sub-study.
- [ ] 8. **Commit query set v1.** Lock for first full run. Any future changes are versioned and noted in the methodology.

### Phase 3: Engine Integration

- [ ] 9. **ChatGPT integration.** OpenAI API with web search tool enabled. Extract response text and cited URLs.
- [ ] 10. **Perplexity integration.** Sonar API. Parse returned citations into the common schema.
- [ ] 11. **Claude integration.** Anthropic API with the web search tool. Extract citations from response blocks.
- [ ] 12. **Normalization layer.** All three engines write into one common schema: `run_id`, `query_id`, `engine`, `model_version`, `run_number`, `url`, `domain`, `citation_position`, `timestamp`, `cost_usd`.
- [ ] 13. **Connectivity test.** A `test` command confirms all three engines return valid, parseable responses. Pattern matches the existing content pipeline's `run.py test`.

### Phase 4: Data Layer

- [ ] 14. **SQLite schema.** Tables for runs, citations, queries, costs. Database lives at `/data/observatory.db` and is committed to the repo.
- [ ] 15. **Idempotent writes.** A query cannot be recorded twice for the same run number. Re-runs of a failed workflow do not corrupt data.
- [ ] 16. **Cost accumulator.** Per engine, per month. Written to `costs` table after every API call. Summed into monthly report.

### Phase 5: Report Generation

- [ ] 17. **Monthly report template.** Sections: executive summary, citation frequency by engine, cross-engine overlap (Jaccard similarity per query), domain leaderboard per engine, prompt-stability sub-study findings, cost summary, methodology changes, next month's plan.
- [ ] 18. **Report generator.** Reads from SQLite, writes markdown to `/reports/YYYY-MM.md`. Commits automatically.
- [ ] 19. **Statistical rigor.** All claims accompanied by sample size, median and range, and appropriate hedges. No point estimates without distributions.

### Phase 6: Scheduling

- [ ] 20. **GitHub Actions workflow.** `.github/workflows/monthly-sweep.yml`. Cron: first of each month, 02:00 UTC. Installs dependencies, runs full sweep, generates report, commits back, posts to Notion.
- [ ] 21. **Failure handling.** Workflow failures open a GitHub issue automatically with the error log. No silent failures.
- [ ] 22. **Budget circuit breaker.** If accumulated cost for the current run crosses $40, sweep stops, partial results are committed, and an issue is opened.

### Phase 7: Review Gate

- [ ] 23. **Notion integration.** After report generation, a summary is posted to a Notion database (to be created or identified) with Status: Needs Review. No external announcement until reviewed.
- [ ] 24. **Review workflow.** Operator reviews the report, approves or revises, then announces externally (LinkedIn post, newsletter, or both).

### Phase 8: Validation and Launch

- [ ] 25. **End-to-end local run.** Operator runs the full sweep locally first to validate the pipeline, confirm cost, and verify report quality.
- [ ] 26. **First scheduled run.** Workflow executes on schedule, produces first committed report.
- [ ] 27. **Publish `METHODOLOGY.md`.** Public documentation finalized.
- [ ] 28. **Publish first report externally.** LinkedIn article, newsletter, or both. Positions the research project publicly.

### Phase 9: Cost and Quality Monitoring

- [ ] 29. **Monthly cost summary in every report.** Per-engine breakdown, monthly total, year-to-date.
- [ ] 30. **Quality checklist at review gate.** Before external publication, confirm: distributions present, scope honestly framed, null findings acknowledged, methodology changes documented, cost within budget.
