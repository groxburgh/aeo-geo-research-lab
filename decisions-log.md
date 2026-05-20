# Decisions Log

Why we chose X over Y. Capture reasoning in the moment so future context is not lost.

Format: each decision gets a dated entry with Decision, Alternative(s) Considered, and Rationale.

---

## 2026-04-19: Primary research over monitoring or self-visibility tracking

**Decision:** Build a primary research observatory that generates original cross-engine AEO/GEO findings.

**Alternatives considered:**
- Field monitoring only (covered by existing weekly Gemini research task)
- Self-visibility tracker (measuring only the operator's own content)

**Rationale:** The operator's moat is positioning, not infrastructure. Descriptive and longitudinal original research in a defined niche creates a content and sales asset no direct competitor currently publishes. Self-visibility tracking alone is a personal dashboard and does not produce publishable findings. Field monitoring is already handled by a separate Gemini task and does not need to be duplicated.

---

## 2026-04-19: Three engines (ChatGPT, Perplexity, Claude); Google AI Mode excluded

**Decision:** V1 covers ChatGPT (via OpenAI API with web search), Perplexity (via Sonar API), and Claude (via Anthropic API with web search tool).

**Alternatives considered:**
- ChatGPT only (Indig-style single-engine approach)
- All four engines including Google AI Mode

**Rationale:** Cross-engine comparison is the differentiator. Semrush and Profound publish multi-engine snapshots but not openly and not monthly. Google AI Mode has no API; scraping introduces legal and reliability risk for a public research project. Gemini is deferred to V4 pending grounding reliability assessment. Excluding Google AI Mode will be declared openly in published methodology.

---

## 2026-04-19: Query set of 350 diverse + 150 focused, across three ICP-adjacent zones

**Decision:** The full corpus is 500 queries. 350 cover diverse categories for methodological credibility. 150 cover three ICP zones (content operations and marketing, B2B SaaS and fintech, AEO/GEO itself) at 50 each.

**Alternatives considered:**
- Focused only (~200 queries entirely within ICP zones, for efficiency)
- Single-zone narrow focus (content operations only)

**Rationale:** The operator prioritized finding quality above all else. Broad-corpus diversity protects against skeptic dismissal as niche-specific. Focused queries double as ICP intelligence for sales conversations. The budget constraint (see next entry) required revising the V1 execution scope, not the query set design.

---

## 2026-04-19: $40/month budget enforces narrow V1 scope

**Decision:** V1 runs a 50-to-60 query subset, entirely within the three ICP zones, monthly, three runs per query per engine.

**Alternatives considered:**
- Full 500-query corpus weekly (~$1,100/month, infeasible self-funded)
- Two-tier cadence: full monthly + 100-query weekly stability subset (~$200-300/month, also too expensive)
- 300-query single-engine weekly (~$25-35/month, kills the cross-engine wedge)
- Sponsored funding

**Rationale:** Self-funded V1 preserves editorial independence during proof-of-concept. Three runs per query is the minimum viable noise-resistance threshold given documented citation-set volatility; dropping below it makes findings unpublishable. Monthly cadence still produces a longitudinal record (absent in competitor work) even at low frequency. The full 350+150 query design is retained as a North Star for expanded scope in V2+ once revenue or sponsorship justifies it.

---

## 2026-04-19: Self-fund V1; productize bespoke research as commercial output

**Decision:** No external funding for V1. Once two to three monthly reports exist, offer productized bespoke AEO/GEO research engagements to prospects as the commercial output.

**Alternatives considered:**
- Accept sponsor funding to expand scope immediately
- Sell bespoke research to a current pipeline prospect before V1 public reports exist

**Rationale:** Sponsored research on an unproven methodology weakens editorial independence and gives the operator worse negotiating leverage. Publishing first creates the credibility asset that makes later sponsorship or bespoke engagements easier to sell on the operator's terms. Bespoke research without prior public proof-of-concept is harder to sell for the same reason.

---

## 2026-04-19: Three runs minimum per query per engine per month

**Decision:** Every query runs three times per engine per month. Reports present distributions, not single-run point estimates.

**Alternatives considered:**
- Single run per query (cheaper, faster)
- Five or more runs per query (more statistically rigorous)

**Rationale:** Published research confirms AI citation sets are highly volatile run-to-run. Single-run data is noise and publishing it as a finding is misleading. Three runs is the minimum to report a median with any meaningful range estimate. Five would be better but the budget constraint makes it infeasible at V1 scope.

---

## 2026-04-19: GitHub Actions + public repo as hosting and research artifact

**Decision:** The project lives in a public GitHub repository. Scheduled execution via GitHub Actions. SQLite database and monthly reports committed to the repo. No VPS.

**Alternatives considered:**
- Shared VPS with the existing Hermes project (solid but decouples the artifact from the running code)
- New VPS (extra fixed cost with no added value for monthly cadence)
- Local cron only (defeats the scheduled reliability goal)

**Rationale:** The repo itself is the research artifact. A public repo with prompts, config, code, data, and reports all version-controlled is a qualitatively better credibility artifact than a PDF report. Actions handles monthly scheduling natively with zero infrastructure cost. Public from day one forces methodology discipline. Decouples cleanly from Hermes, which fails in isolation instead of taking down both.

---

## 2026-04-19: Methodology public from day one

**Decision:** The prompt set, run protocol, model versions, normalization rules, and known limitations are documented in METHODOLOGY.md and committed on the first run.

**Alternatives considered:**
- Publish methodology after the first report is successful
- Keep methodology private to protect a perceived competitive advantage

**Rationale:** Methodology transparency is the project's moat, not a weakness to hide. At small sample size, credibility comes from auditability, not volume. A skeptic who can inspect the full method is more likely to trust the findings than one who cannot.

---

## 2026-05-02: Claude web search capped at 1 per query (max_uses=1)

**Decision:** The `web_search_20250305` tool parameter `max_uses` is set to 1 for all Claude queries, down from the initial 3.

**Alternatives considered:**
- Keep max_uses=3 and rely on the $40 circuit breaker to cut the run short each month
- Switch to Claude Haiku to reduce token costs while keeping max_uses=3

**Rationale:** Two compounding reasons. First, budget: the first production run cost ~$20 on Claude alone (4.7M input tokens + 277 web searches), pushing the three-engine total above $40. Setting max_uses=1 reduces both web search fees and input token volume (less search result context), bringing the estimated total to ~$33. Second, methodological consistency: with max_uses=3, Claude made an average of 1.57 searches per query through iterative refinement, while Perplexity always makes 1 API call and OpenAI's web_search_preview typically makes 1 search. The multi-search iteration gave Claude a qualitatively different retrieval process. Fixing all three engines at effectively 1 primary web search per query creates a more defensible apples-to-apples comparison for citation pattern analysis. This change takes effect from the 2026-05 sweep.

---

## 2026-05-13: run_exists excludes error rows; clear_error_run pattern for retry

**Decision:** `run_exists` SQL now includes `AND error IS NULL`. A new `clear_error_run()` function deletes the error row (and its costs row) before the existence check, allowing the runner to retry cleanly.

**Alternatives considered:**
- Leave `run_exists` as-is and require manual SQL to clear error rows before re-run
- Use `INSERT OR REPLACE` to overwrite error rows (risks silently overwriting valid data)

**Rationale:** The TECH-SPEC says "a re-run after partial failure picks up where it left off" — error rows contradict this if they block retry. The `clear_error_run` + `run_exists` pattern preserves idempotency for successful rows while making error rows automatically retryable. Deleting cost rows for error runs is safe because all error runs have `cost_usd = 0.0` and do not affect the budget calculation.

---

## 2026-05-13: Anthropic SDK pinned to 0.56.0 (minimum for web search citation extraction)

**Decision:** Upgrade `anthropic` from `0.49.0` to `0.56.0` in `requirements.txt`.

**Alternatives considered:**
- Stay on 0.49.0 and parse citations from inline text (fragile, unreliable)
- Upgrade to latest (0.101.0) for maximum currency

**Rationale:** SDK 0.49.0 has no typed classes for the block types the Anthropic API returns when using `web_search_20250305`: `ServerToolUseBlock`, `WebSearchToolResultBlock`, and `WebSearchResultBlock` were all added in 0.56.0. Without these types the SDK cannot correctly deserialise the response and citation extraction silently returns 0. Pinning to 0.56.0 (the minimum version with working support) rather than latest reduces the surface area for unexpected breaking changes in a research-integrity context where output stability matters. The SDK can be bumped further in a dedicated session if new API features are needed.

---

## 2026-04-19: Notion as review gate only, not primary store

**Decision:** Raw data lives in a SQLite database committed to the repo. Monthly reports are markdown files committed to the repo. Notion receives a summary post of each generated report as a human review gate before external announcement.

**Alternatives considered:**
- Notion as primary store (poor fit for structured citation data, hard to version)
- No review gate (auto-publish on generation)

**Rationale:** Structured research data belongs in a versioned database. Notion's strength is review and collaboration, which maps cleanly to the approve-before-announce workflow. Removing the human review step risks an automated report with a flaw being announced externally before the operator sees it.

---

## 2026-05-19: tldextract replaces hand-rolled eTLD+1 normalization

**Decision:** Replace the `hostname.split(".")[-2:]` domain normalization in `Citation.extract_domain()` with `tldextract==5.3.1` using a vendored offline PSL cache.

**Alternatives considered:**
- Fix the split manually for known ccSLDs (allowlist approach)
- `publicsuffix2` / `publicsuffixlist` libraries
- Continue with `_INVALID_DOMAINS` blocklist in report.py

**Rationale:** The hand-rolled split incorrectly collapses `bbc.co.uk → co.uk`, `guardian.co.uk → co.uk`, and all other ccSLDs — this was the root cause of `co.uk` and `org.uk` appearing as top cross-engine cited domains in the May 2026 report (a data quality failure). A blocklist in `report.py` is a band-aid that requires manual maintenance and has no coverage for `.com.au`, `.co.jp`, and dozens of other ccSLDs. `tldextract` is the canonical Python PSL library, actively maintained, and ships a bundled snapshot. The offline cache (`suffix_list_urls=()` + committed `.cache/tldextract/`) ensures month-to-month runs are byte-for-byte reproducible with no network dependency in GitHub Actions.

---

## 2026-05-19: Claude max_uses raised from 1 to 3 (calibration intent)

**Decision:** `max_uses` for the `web_search_20250305` tool raised from 1 to 3 starting June 2026.

**Alternatives considered:**
- Keep max_uses=1 and document the ~10-citation ceiling as a methodological choice
- Raise immediately to max_uses=5

**Rationale:** Independent analysis of Claude's Brave-backed retrieval (BrightEdge, wire.wise-relations.com Claude Code analysis) converges on ~10 results per `web_search` invocation. With max_uses=1 this creates a hard ceiling of ~10 citations per query regardless of topic richness — directly limiting the citation diversity metric this observatory is designed to measure. Budget cost of raising to max_uses=3 is approximately $5/month additional at full invocation (531 searches × $0.010 = $5.31), well within the $40 cap. max_uses=5 is deferred until June calibration data shows whether citations scale with invocations. June 2026 will serve as the calibration baseline; if mean invocations per query are well below 3, further raising is unlikely to help.

---

## 2026-05-19: Quarantine pattern for bad runs; partial UNIQUE index for slot reuse

**Decision:** Introduce a `quarantined` column and a `quarantine_reason` column on `runs`. Replace the inline `UNIQUE(query_id, engine, run_number, month)` constraint with a partial unique index `WHERE quarantined = 0`. Add `model_version` to the `run_exists()` predicate.

**Alternatives considered:**
- Delete bad rows (simpler, but destroys audit trail)
- Keep the inline UNIQUE constraint and move bad rows to a separate archive table
- Add `extraction_version` to the `run_exists()` predicate immediately

**Rationale:** The May 2026 ChatGPT data (170 rows from the wrong model snapshot + 7 from a partial re-run) must not be silently mixed into cross-engine comparisons, but deleting them would make it impossible to explain the May report gap later. The quarantine pattern preserves the audit trail while making the data invisible to the pipeline and to report queries (via the `runs_active` view). The partial unique index (`WHERE quarantined = 0`) allows a quarantined row and a fresh replacement to coexist in the same slot — without this, any re-run after quarantine would fail with a UNIQUE constraint error. The `model_version` check in `run_exists()` makes the pipeline self-healing when a model pin changes: existing rows for the old model become invisible and are automatically re-fetched on the next run. `extraction_version` is added to the schema but deferred from the `run_exists()` predicate — adding it now would trigger a full re-run of all correct May Perplexity and Claude data, which is unnecessary.
