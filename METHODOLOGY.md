# METHODOLOGY.md
## AEO/GEO Research Observatory — Research Protocol

**Version:** 1.0
**Effective from:** First run date (TBD)

This document is the authoritative description of how this research is conducted. Any change to the protocol is recorded in the Version History section and version-controlled in git.

---

## Research Questions

This study measures four things:

1. **Citation frequency** — Which domains does each AI engine cite when answering queries in a defined topic zone, and how consistently across repeated runs?
2. **Cross-engine overlap** — Which domains are cited by all three engines vs. by only one?
3. **Domain leaderboards** — Which domains are cited most often per engine, per topic zone, per month?
4. **Prompt sensitivity** — How much does minor rewording of the same query change the citation set returned by each engine?

This study does not measure ranking, click-through rate, or organic search performance. It measures AI citation behavior only.

---

## Query Set

### Construction

Queries are designed to reflect how a real B2B buyer or practitioner asks an AI engine for information — not how an SEO analyst would keyword-research a topic. Queries are written as natural-language questions or tasks.

Each query is classified by:
- **Zone** — One of three topic zones (see below)
- **Query type** — Commercial, informational, comparison, how-to, or navigational

### Topic Zones

**Zone 1: Content Operations and Marketing**
Queries about content strategy, content operations tooling, editorial workflow, AI content tools, and marketing technology for content teams.

**Zone 2: B2B SaaS and Fintech**
Queries about software categories, vendor selection, market leaders, integrations, and analyst perspectives relevant to Series A–C B2B SaaS and fintech companies.

**Zone 3: AEO/GEO**
Queries about AI engine optimization, generative engine optimization, citation building, AI search behavior, and the practice of optimizing for AI visibility.

### Scope

V1 runs 50–60 queries, all within the three zones above. The full design corpus of 500 queries (350 diverse + 150 focused) is the North Star for expanded scope in V2+ once budget permits.

### Version Control

The query set is stored in `/prompts/prompts.yaml` and is version-controlled. Any addition, removal, or rewording of a canonical query after the first run is a methodology change and must be recorded in the Version History section of this document.

---

## Engine Coverage

### Active Engines (V1)

**ChatGPT** — OpenAI Responses API with web search enabled. Model: `gpt-4o-2024-11-20` (exact version recorded per run). Citations extracted from `url_citation` annotations on `output_text` content parts in the API response.

**Perplexity** — Sonar API. Model: `sonar` (exact version recorded per run). Citations extracted from the `citations` array returned alongside the answer.

**Claude** — Anthropic Messages API with the web search tool. Model: `claude-sonnet-4-6` (exact version recorded per run). Citations extracted from `web_search_tool_result` content blocks (containing nested search result objects) in the API response. Web search capped at 3 invocations per query (`max_uses: 3`) from the June 2026 sweep onward; the May 2026 sweep ran with `max_uses: 1`, which imposed a ceiling of roughly 10 citations per query (see Version History 1.2 and the decisions log entry dated 2026-05-19).

### Excluded Engines

**Google AI Mode** — Excluded because no API is available. Web scraping is not used; it introduces legal risk and reliability issues incompatible with a public research project. This exclusion is declared in every report.

**Gemini** — Deferred to V4 pending a grounding reliability assessment. The API's citation output format and stability require evaluation before it can be incorporated into a longitudinal study.

---

## Run Protocol

### Cadence

The full query set runs once per month, scheduled for the first of each month at 02:00 UTC via GitHub Actions.

### Repetitions

Every query runs three times per engine per month. Reports present distributions (median citation set, range, variance) rather than single-run point estimates. Single-run citation data is noise: AI citation sets are documented to be volatile between identical runs. Three is the minimum viable repetition count to report a median with a meaningful range.

### Prompt Delivery

The exact prompt text from `prompts.yaml` is sent verbatim to all three engines. No system prompt is added. No few-shot examples are included. The same prompt text is sent to all three engines for a given query.

### Idempotency

A run (query + engine + run_number + month) is written to SQLite exactly once. If the pipeline fails mid-run and is restarted, it resumes from where it left off. Completed runs are never overwritten.

---

## Prompt Stability Sub-Study

### Purpose

To quantify how sensitive citation sets are to minor rewording of the same query — a known gap in published AEO/GEO research.

### Protocol

At least five canonical queries are each paired with one rewording variant. Both the canonical and the variant are run through all three engines with the standard three-repetition protocol every month.

### Analysis

For each canonical/variant pair, Jaccard similarity is computed on the domain sets returned:

```
Jaccard(A, B) = |A ∩ B| / |A ∪ B|
```

Where A is the set of domains cited across all three runs of the canonical prompt and B is the set of domains cited across all three runs of the variant prompt.

A Jaccard similarity of 1.0 means the domain sets are identical. A value of 0.0 means no overlap. Results are reported in the monthly report's prompt stability section.

### Variant Labeling

Variant queries are flagged with `is_variant: true` and `variant_of: <canonical_id>` in `prompts.yaml` and in the `queries` table. Report analysis uses these columns to separate canonical from variant runs.

---

## Citation Extraction and Normalization

### Per-Engine Extraction

Each engine returns citations in a different format. The pipeline normalizes them to a common schema before storage.

| Engine | Citation Source | Title Available |
|---|---|---|
| ChatGPT | `url_citation` annotations on `output_text` content parts | Yes |
| Perplexity | `citations` array — flat list of URL strings | No |
| Claude | `web_search_tool_result` content blocks; each result object has `url` and `title` | Yes |

### Domain Normalization

From the June 2026 sweep onward, domains are normalized to eTLD+1 with `tldextract` 5.3.1 using a vendored offline Public Suffix List cache (no network dependency at run time). The result is stored in `domain_v2`, and every citation row carries a `normalization_version` (`v2-tldextract-5.3` for current data). The legacy `domain` column is retained unchanged for provenance; `domain_v2` is the authoritative column for all analysis and reporting, and `report.py` prefers it wherever populated.

Example: `www.blog.hbr.org` resolves to `hbr.org`; `www.bbc.co.uk` resolves to `bbc.co.uk`.

**Legacy method (May 2026 data):** the v1 method took the last two dot-separated segments of the hostname after parsing with `urllib.parse.urlparse`. It collapsed country-code second-level domains incorrectly (`bbc.co.uk` resolved to `co.uk`), which is why `co.uk` and `org.uk` appear in the May 2026 report. The tldextract migration (decisions log, 2026-05-19) resolved this for all subsequent sweeps.

### Citation Position

Position is the 1-based order in which a citation appears in the engine's response. For Perplexity, position is the index in the `citations` array. For ChatGPT and Claude, position is the order of encounter when iterating the response content blocks.

---

## Statistical Approach

All claims are accompanied by sample size, distribution, and scope framing.

**Citation frequency** is reported as: the number of runs (out of 3) in which a domain appeared, per query, per engine. "Cited in 3/3 runs" is a strong signal. "Cited in 1/3 runs" is weak.

**Domain leaderboards** rank domains by the count of (query, engine, run) combinations in which they appeared during the month. This counts consistent citations across runs and queries, not raw appearance count.

**Cross-engine overlap** uses Jaccard similarity on domain sets per query. Full monthly overlap is also reported as three counts: domains cited by all three engines, by exactly two, by exactly one.

**No extrapolation.** Every claim is scoped to the engines tested, the queries run, and the month of the data. No inferences are made about engines not tested or queries not run.

---

## Cost Model

API cost is tracked per run and stored in the `costs` table. The pipeline self-enforces a $40/month cap via a circuit breaker checked before every API call.

Pricing as of V1 (2026-04):

| Engine | Input (per token) | Output (per token) |
|---|---|---|
| ChatGPT (gpt-4o) | $0.0000025 | $0.000010 |
| Perplexity (sonar) | $0.000001 | $0.000001 |
| Claude (claude-sonnet-4-6) | $0.000003 | $0.000015 |

Cost per run is computed by the engine integration class and stored immediately after the API call. The monthly total is reported in every monthly report.

If the circuit breaker fires, the partial run is committed, the report notes the budget breach, and a GitHub issue is opened automatically.

---

## Model Version Tracking

The exact model version string returned by each API is recorded in the `model_version` column of every run. If a model version changes between runs within a month (e.g., OpenAI silently upgrades `gpt-4o`), all observed versions are listed in the report's model version section and the change is flagged as a potential confound.

Model version changes are not treated as a reason to exclude data. They are disclosed transparently and the reader is left to assess the impact.

---

## Known Limitations

1. **Sample size** — 50–60 queries is a narrow sample. Findings are scoped to the three zones defined above and cannot be generalized to other categories.
2. **Monthly cadence** — The pipeline runs once per month. Intra-month changes in citation behavior are not captured.
3. **No Google AI Mode** — A significant engine is excluded. This is disclosed in every report.
4. **Domain normalization simplification** — eTLD+1 extraction has a known limitation with country-code second-level domains (see Citation Extraction section).
5. **Citation ≠ ranking** — This study measures whether a domain is cited, not its position in a ranked result or its influence on the answer.
6. **AI behavior volatility** — Citation sets are known to vary between runs of the same prompt. Three repetitions mitigate but do not eliminate this. It is a property of the research subject, not a flaw in the methodology.
7. **Self-funded scope constraint** — The $40/month budget cap is a business constraint, not a methodological preference. It is the reason V1 runs 50–60 queries monthly rather than the full 500-query corpus.

---

## Conflict of Interest

This research is conducted by Greg Roxburgh, a content operations consultant based in Seoul. The three topic zones studied (content operations, B2B SaaS/fintech, AEO/GEO) directly serve the operator's consulting ICP and professional positioning.

Findings are reported without selection: null results and months with no significant change are published as such. This observatory is self-funded. No sponsor or client relationship influences which findings are reported or how they are framed.

---

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | TBD (first run date) | Initial methodology. 50–60 queries, three engines, three runs per query per engine. |
| 1.1 | 2026-05-13 | Updated citation extraction descriptions to match actual API response structures. Added conflict-of-interest disclosure. Added max_uses: 1 note for Claude. Updated ChatGPT model to gpt-4o-2024-11-20. |
| 1.2 | 2026-05-19 | Domain normalization migrated to tldextract 5.3.1 with an offline PSL cache (normalization_version v2-tldextract-5.3); domain_v2 added as the authoritative column, legacy domain retained for provenance. Claude max_uses raised from 1 to 3, effective the June 2026 sweep. Quarantine pattern introduced (quarantined and quarantine_reason columns, partial unique index for slot reuse). Applied from the June 2026 sweep onward; recorded here retroactively on 2026-08-04. |
| 1.3 | 2026-08-04 | Reporting metric corrected: leaderboards previously divided citation appearances by run count under a "% of runs" header, overstating every share. Primary metric is now distinct runs citing, with appearances retained as a secondary column. Run Summary section added (valid, error, citing and zero-citation runs, min and max citations per run). Per-engine Jaccard added alongside the pooled figure in the Prompt Stability Sub-Study. Reports for 2026-06, 2026-07 and 2026-08 regenerated with the corrected metric. July 2026 Perplexity zero-citation runs disclosed rather than quarantined (see decisions log, 2026-08-04). |
