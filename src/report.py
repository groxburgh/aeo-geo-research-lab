from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from src import db

_BUDGET_CAP = 40.0


def _jaccard(a: set, b: set) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 1.0


def _domain(c: dict) -> str | None:
    """Return the best available domain for a citation row.

    Prefers domain_v2 (tldextract-normalized) when populated. Falls back to the
    legacy domain column for rows that pre-date the v2 migration. Returns None for
    rows where no valid domain could be extracted.
    """
    d = c.get("domain_v2")
    if d:
        return d
    legacy = c.get("domain", "")
    return legacy if legacy else None


def generate_report(db_path: str, month: str, reports_dir: str) -> str:
    runs = db.get_runs_for_month(db_path, month)
    citations = db.get_citations_for_month(db_path, month)
    costs = db.get_costs_for_month(db_path, month)

    total_cost = sum(c["cost_usd"] for c in costs)
    engines_covered = sorted({r["engine"] for r in runs})
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    budget_breached = total_cost >= _BUDGET_CAP

    lines: list[str] = []

    # 1. Header
    lines += [
        f"# AEO/GEO Research Observatory — {month}",
        "",
        f"**Generated:** {generated_at}  ",
        f"**Total runs:** {len(runs)}  ",
        f"**Total cost:** ${total_cost:.4f}  ",
        f"**Engines covered:** {', '.join(engines_covered) if engines_covered else 'none'}  ",
        "",
    ]

    # 2. Budget summary
    lines += [
        "## Budget Summary",
        "",
        "| | |",
        "|---|---|",
        f"| Spent | ${total_cost:.4f} |",
        f"| Cap | ${_BUDGET_CAP:.2f} |",
        f"| Circuit breaker fired | {'Yes' if budget_breached else 'No'} |",
        "",
    ]

    # 3. Run summary and per-engine citation frequency
    run_index = {r["run_id"]: r for r in runs}
    valid_runs = [r for r in runs if not r.get("error")]
    error_count_by_engine: dict[str, int] = defaultdict(int)
    valid_count_by_engine: dict[str, int] = defaultdict(int)
    for r in runs:
        if r.get("error"):
            error_count_by_engine[r["engine"]] += 1
        else:
            valid_count_by_engine[r["engine"]] += 1

    appearances: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    citing_runs: dict[str, dict[str, set]] = defaultdict(lambda: defaultdict(set))
    cites_per_run: dict[str, int] = defaultdict(int)
    for c in citations:
        run = run_index.get(c["run_id"])
        d = _domain(c)
        if run and d and not run.get("error"):
            eng = run["engine"]
            appearances[eng][d] += 1
            citing_runs[eng][d].add(c["run_id"])
            cites_per_run[c["run_id"]] += 1

    lines += ["## Run Summary", ""]
    lines += [
        "| Engine | Valid runs | Error runs | Runs citing | Zero-citation runs "
        "| Total citations | Citations per valid run | Min | Max | Unique domains |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for engine in engines_covered:
        vruns = [r for r in valid_runs if r["engine"] == engine]
        counts = [cites_per_run.get(r["run_id"], 0) for r in vruns]
        n_valid = len(vruns)
        total_c = sum(counts)
        n_zero = sum(1 for x in counts if x == 0)
        per_run = (total_c / n_valid) if n_valid else 0.0
        uniq = len(appearances[engine])
        mn = min(counts) if counts else 0
        mx = max(counts) if counts else 0
        lines.append(
            f"| {engine} | {n_valid} | {error_count_by_engine[engine]} | {n_valid - n_zero} "
            f"| {n_zero} | {total_c} | {per_run:.2f} | {mn} | {mx} | {uniq} |"
        )
    lines += [
        "",
        "_Per-run citation counts are shaped by engine-side result limits, which have been "
        "observed to change between months, and for Claude by search invocation mechanics "
        "(`max_uses`). Min and max are disclosed so per-run volume is never read as an "
        "unconstrained behavioural metric._",
        "",
    ]

    lines += ["## Citation Frequency by Engine", ""]
    for engine in engines_covered:
        total_runs = valid_count_by_engine[engine]
        top = sorted(
            citing_runs[engine].items(),
            key=lambda x: (len(x[1]), appearances[engine][x[0]]),
            reverse=True,
        )[:20]
        lines += [
            f"### {engine}",
            "",
            "| Domain | Runs citing | % of runs | Appearances |",
            "|---|---|---|---|",
        ]
        for domain, run_set in top:
            n_runs = len(run_set)
            pct = (n_runs / total_runs * 100) if total_runs else 0
            lines.append(
                f"| {domain} | {n_runs} | {pct:.1f}% | {appearances[engine][domain]} |"
            )
        if not top:
            lines.append("_No citations recorded for this engine this month._")
        lines.append("")
    lines += [
        "_% of runs is the share of the engine's valid runs whose answer cited the domain at "
        "least once. Appearances counts every citation of the domain, including repeats within "
        "a single answer. Reports generated before 2026-08-04 divided appearances by run count "
        "under this header, overstating every share; see decisions-log.md._",
        "",
    ]

    # 4. Cross-engine domain overlap
    lines += ["## Cross-Engine Domain Overlap", ""]
    domain_engines: dict[str, set[str]] = defaultdict(set)
    for c in citations:
        run = run_index.get(c["run_id"])
        d = _domain(c)
        if run and d:
            domain_engines[d].add(run["engine"])

    n_engines = len(engines_covered)
    all_n = sorted(d for d, e in domain_engines.items() if len(e) == n_engines)
    exactly_two = sorted(d for d, e in domain_engines.items() if len(e) == 2 and n_engines > 2)
    exactly_one = sorted(d for d, e in domain_engines.items() if len(e) == 1)

    if n_engines >= 3:
        lines += [
            f"**Cited by all {n_engines} engines ({len(all_n)}):** {', '.join(all_n) or 'none'}",
            "",
            f"**Cited by exactly 2 engines ({len(exactly_two)}):** {', '.join(exactly_two) or 'none'}",
            "",
            f"**Cited by exactly 1 engine ({len(exactly_one)}):** {len(exactly_one)} domains",
            "",
        ]
    elif n_engines == 2:
        lines += [
            f"**Cited by both engines ({len(all_n)}):** {', '.join(all_n) or 'none'}",
            "",
            f"**Cited by exactly 1 engine ({len(exactly_one)}):** {len(exactly_one)} domains",
            "",
        ]
    else:
        lines += ["_Cross-engine overlap requires at least 2 engines with citation data._", ""]

    zero_cit = [e for e in engines_covered if not appearances[e]]
    if zero_cit:
        active = [e for e in engines_covered if appearances[e]]
        lines.append(
            f"_Note: {', '.join(zero_cit)} returned no citations this month. "
            f"Overlap figures reflect {', '.join(active)} data only._"
        )
        lines.append("")

    # 5. Prompt stability section
    lines += ["## Prompt Stability Sub-Study", ""]
    variant_runs = [r for r in runs if r.get("query_id", "").endswith("-v2")]
    if not variant_runs:
        lines += ["No stability variant runs recorded this month.", ""]
    else:
        variant_ids = {r["query_id"] for r in variant_runs}
        run_query = {r["run_id"]: r["query_id"] for r in runs}
        run_engine = {r["run_id"]: r["engine"] for r in runs}

        def _domain_sets(query_id: str) -> tuple[set, dict[str, set]]:
            pooled: set = set()
            per_engine: dict[str, set] = {e: set() for e in engines_covered}
            for c in citations:
                d = _domain(c)
                if not d or run_query.get(c["run_id"]) != query_id:
                    continue
                pooled.add(d)
                per_engine[run_engine[c["run_id"]]].add(d)
            return pooled, per_engine

        header_engines = " | ".join(engines_covered)
        lines += [
            f"| Canonical | Variant | Pooled Jaccard | {header_engines} |",
            "|---|---|---|" + "---|" * len(engines_covered),
        ]
        for variant_id in sorted(variant_ids):
            canonical_id = variant_id[:-3]  # strip "-v2"
            c_pooled, c_eng = _domain_sets(canonical_id)
            v_pooled, v_eng = _domain_sets(variant_id)
            pooled_j = _jaccard(c_pooled, v_pooled)
            cells = []
            for e in engines_covered:
                union = c_eng[e] | v_eng[e]
                cells.append(
                    f"{len(c_eng[e] & v_eng[e]) / len(union):.3f}" if union else "n/a"
                )
            lines.append(
                f"| {canonical_id} | {variant_id} | {pooled_j:.3f} | "
                + " | ".join(cells)
                + " |"
            )
        lines += [
            "",
            "_Pooled Jaccard compares the union of all engines' domains for each phrasing, "
            "which smooths over per-engine differences. Per-engine columns compare each "
            "engine against itself across the two phrasings. n/a means the engine cited "
            "nothing on either phrasing._",
        ]
        if zero_cit:
            active = [e for e in engines_covered if appearances[e]]
            lines.append("")
            lines.append(
                f"_Note: Jaccard scores reflect {', '.join(active)} citation data only. "
                f"No citations were captured for {', '.join(zero_cit)} this month._"
            )
        lines.append("")

    # 6. Model versions
    lines += ["## Model Versions", ""]
    for engine in engines_covered:
        versions = sorted(
            {r["model_version"] for r in runs if r["engine"] == engine and not r.get("error")}
        )
        lines.append(f"**{engine}:** {', '.join(versions) if versions else 'n/a'}")
    lines.append("")

    # 7. Raw run log
    lines += [
        "## Raw Run Log",
        "",
        "<details><summary>Expand</summary>",
        "",
        "| query_id | engine | run | cost_usd | citations | error |",
        "|---|---|---|---|---|---|",
    ]
    cit_count: dict[str, int] = defaultdict(int)
    for c in citations:
        cit_count[c["run_id"]] += 1
    for r in runs:
        err = "yes" if r.get("error") else ""
        lines.append(
            f"| {r['query_id']} | {r['engine']} | {r['run_number']} "
            f"| ${r['cost_usd']:.5f} | {cit_count[r['run_id']]} | {err} |"
        )
    lines += ["", "</details>", ""]

    Path(reports_dir).mkdir(parents=True, exist_ok=True)
    out_path = str(Path(reports_dir) / f"{month}.md")
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    return out_path
