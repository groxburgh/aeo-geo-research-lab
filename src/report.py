from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from src import db

_BUDGET_CAP = 40.0


def _jaccard(a: set, b: set) -> float:
    union = a | b
    return len(a & b) / len(union) if union else 1.0


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

    # 3. Per-engine citation frequency
    lines += ["## Citation Frequency by Engine", ""]
    cit_by_engine: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    run_count_by_engine: dict[str, int] = defaultdict(int)
    for r in runs:
        run_count_by_engine[r["engine"]] += 1
    for c in citations:
        run = next((r for r in runs if r["run_id"] == c["run_id"]), None)
        if run:
            cit_by_engine[run["engine"]][c["domain"]] += 1

    for engine in engines_covered:
        total_runs = run_count_by_engine[engine]
        domain_counts = cit_by_engine[engine]
        top = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        lines += [f"### {engine}", "", "| Domain | Citations | % of runs |", "|---|---|---|"]
        for domain, count in top:
            pct = (count / total_runs * 100) if total_runs else 0
            lines.append(f"| {domain} | {count} | {pct:.1f}% |")
        lines.append("")

    # 4. Cross-engine domain overlap
    lines += ["## Cross-Engine Domain Overlap", ""]
    domain_engines: dict[str, set[str]] = defaultdict(set)
    for c in citations:
        run = next((r for r in runs if r["run_id"] == c["run_id"]), None)
        if run:
            domain_engines[c["domain"]].add(run["engine"])

    all_three = sorted(d for d, e in domain_engines.items() if len(e) == 3)
    exactly_two = sorted(d for d, e in domain_engines.items() if len(e) == 2)
    exactly_one = sorted(d for d, e in domain_engines.items() if len(e) == 1)

    lines += [
        f"**Cited by all 3 engines ({len(all_three)}):** {', '.join(all_three) or 'none'}",
        "",
        f"**Cited by exactly 2 engines ({len(exactly_two)}):** {', '.join(exactly_two) or 'none'}",
        "",
        f"**Cited by exactly 1 engine ({len(exactly_one)}):** {len(exactly_one)} domains",
        "",
    ]

    # 5. Prompt stability section
    lines += ["## Prompt Stability Sub-Study", ""]
    variant_runs = [r for r in runs if r.get("query_id", "").endswith("-v2")]
    if not variant_runs:
        lines += ["No stability variant runs recorded this month.", ""]
    else:
        variant_ids = {r["query_id"] for r in variant_runs}
        lines += ["| Canonical | Variant | Jaccard (domain sets) |", "|---|---|---|"]
        for variant_id in sorted(variant_ids):
            canonical_id = variant_id[:-3]  # strip "-v2"
            c_domains = {c["domain"] for c in citations
                         if any(r["run_id"] == c["run_id"] and r["query_id"] == canonical_id for r in runs)}
            v_domains = {c["domain"] for c in citations
                         if any(r["run_id"] == c["run_id"] and r["query_id"] == variant_id for r in runs)}
            j = _jaccard(c_domains, v_domains)
            lines.append(f"| {canonical_id} | {variant_id} | {j:.3f} |")
        lines.append("")

    # 6. Model versions
    lines += ["## Model Versions", ""]
    for engine in engines_covered:
        versions = sorted({r["model_version"] for r in runs if r["engine"] == engine})
        lines.append(f"**{engine}:** {', '.join(versions)}")
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
    cit_count = defaultdict(int)
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
