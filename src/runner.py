from __future__ import annotations

import os
from datetime import datetime, timezone

import yaml

from src import budget, db
from src.engines.anthropic_engine import AnthropicEngine
from src.engines.openai_engine import OpenAIEngine
from src.engines.perplexity_engine import PerplexityEngine

_ENGINES = ["chatgpt", "perplexity", "claude"]
_RUNS_PER_QUERY = 3


def _current_month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def run_sweep(db_path: str, prompts_path: str, month: str, budget_usd: float) -> int:
    with open(prompts_path) as f:
        queries = yaml.safe_load(f)

    for query in queries:
        db.insert_query(db_path, query)

    if not budget.check_budget(db_path, month, budget_usd):
        print(f"[BUDGET] Monthly cap of ${budget_usd} already reached for {month}. Halting.")
        return 2

    engines = {
        "chatgpt": OpenAIEngine(os.environ["OPENAI_API_KEY"]),
        "perplexity": PerplexityEngine(os.environ["PERPLEXITY_API_KEY"]),
        "claude": AnthropicEngine(os.environ["ANTHROPIC_API_KEY"]),
    }

    total = len(queries) * len(_ENGINES) * _RUNS_PER_QUERY
    completed = 0
    circuit_fired = False

    for query in queries:
        query_id = query["id"]
        prompt = query["prompt"].strip()

        for engine_name in _ENGINES:
            engine = engines[engine_name]

            for run_number in range(1, _RUNS_PER_QUERY + 1):
                completed += 1

                if not budget.check_budget(db_path, month, budget_usd):
                    print(f"[BUDGET] Cap reached — skipping {query_id} {engine_name} run {run_number}")
                    circuit_fired = True
                    continue

                if db.run_exists(db_path, query_id, engine_name, run_number, month):
                    print(f"[SKIP] {query_id} {engine_name} run {run_number} already exists")
                    continue

                result = engine.run_query(query_id, prompt, run_number, month)
                db.insert_result(db_path, result)

                status = f"${result.cost_usd:.5f} {len(result.citations)} citations"
                if result.error:
                    status = f"ERROR: {result.error}"
                print(f"[{completed}/{total}] {query_id} {engine_name} run {run_number} — {status}")

    if os.environ.get("GITHUB_ACTIONS"):
        run_count = sum(
            1 for q in queries
            for e in _ENGINES
            for r in range(1, _RUNS_PER_QUERY + 1)
            if db.run_exists(db_path, q["id"], e, r, month)
        )
        total_cost = db.get_month_cost(db_path, month)
        github_env = os.environ.get("GITHUB_ENV", "")
        if github_env:
            with open(github_env, "a") as f:
                f.write(f"SWEEP_MONTH={month}\n")
                f.write(f"SWEEP_RUN_COUNT={run_count}\n")
                f.write(f"SWEEP_COST_USD={total_cost:.4f}\n")

    return 2 if circuit_fired else 0
