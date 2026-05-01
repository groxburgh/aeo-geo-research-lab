from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

import yaml
from dotenv import load_dotenv

load_dotenv(".env.local")

USAGE = """\
Usage: python run.py <command> [options]

Commands:
  test              Validate environment, prompts.yaml, DB schema, and engine connectivity
  run               Execute full monthly research sweep
  report            Generate markdown report from latest run data
  report --notify   Generate report and post summary to Notion
"""

REQUIRED_ENV_VARS = [
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "PERPLEXITY_API_KEY",
    "NOTION_API_KEY",
    "NOTION_REVIEW_DATABASE_ID",
]

REQUIRED_QUERY_FIELDS = {"id", "topic", "prompt", "is_variant", "variant_of"}

DB_PATH = "data/observatory.db"
PROMPTS_PATH = "prompts/prompts.yaml"


def _ok(msg: str) -> None:
    print(f"[OK] {msg}")


def _fail(msg: str) -> None:
    print(f"[FAIL] {msg}")


def cmd_test() -> int:
    failed = False

    # 1. Environment variables
    missing = [v for v in REQUIRED_ENV_VARS if not os.environ.get(v)]
    if missing:
        for v in missing:
            _fail(f"{v} not set")
        failed = True
    else:
        _ok("Environment variables")

    # 2. prompts.yaml
    try:
        with open(PROMPTS_PATH) as f:
            queries = yaml.safe_load(f)
        for i, entry in enumerate(queries):
            missing_fields = REQUIRED_QUERY_FIELDS - entry.keys()
            if missing_fields:
                raise ValueError(f"entry {i} missing fields: {missing_fields}")
        _ok(f"prompts/{PROMPTS_PATH.split('/')[-1]} ({len(queries)} entries)")
    except Exception as e:
        _fail(f"prompts.yaml: {e}")
        failed = True

    # 3. DB schema
    try:
        from src import db
        db.apply_schema(DB_PATH)
        _ok("Database schema")
    except Exception as e:
        _fail(f"Database schema: {e}")
        failed = True

    if failed:
        return 1

    # 4. Engine connectivity
    from src.engines.openai_engine import OpenAIEngine
    from src.engines.perplexity_engine import PerplexityEngine
    from src.engines.anthropic_engine import AnthropicEngine

    test_prompt = "Reply with one word: ready"
    engines = [
        ("OpenAI", OpenAIEngine(os.environ["OPENAI_API_KEY"])),
        ("Perplexity", PerplexityEngine(os.environ["PERPLEXITY_API_KEY"])),
        ("Anthropic", AnthropicEngine(os.environ["ANTHROPIC_API_KEY"])),
    ]

    for name, engine in engines:
        result = engine.run_query("test", test_prompt, 0, "test")
        if result.error is not None:
            _fail(f"{name} connectivity: {result.error}")
            failed = True
        elif not result.response_text.strip():
            _fail(f"{name} connectivity: empty response")
            failed = True
        else:
            _ok(f"{name} connectivity")

    return 1 if failed else 0


def cmd_run() -> int:
    from src import runner
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    budget = float(os.environ.get("MONTHLY_BUDGET_USD", "40"))
    return runner.run_sweep(DB_PATH, PROMPTS_PATH, month, budget)


def cmd_report(notify: bool) -> int:
    from src import report as report_mod
    month = datetime.now(timezone.utc).strftime("%Y-%m")
    path = report_mod.generate_report(DB_PATH, month, "reports")
    _ok(f"Report written to {path}")

    if notify:
        from src import notifier
        try:
            notifier.post_to_notion(
                DB_PATH, month, path,
                os.environ.get("NOTION_API_KEY", ""),
                os.environ.get("NOTION_REVIEW_DATABASE_ID", ""),
            )
            _ok("Notion notification sent")
        except Exception as e:
            print(f"[WARN] Notion notification failed: {e}")

    return 0


def main() -> int:
    args = sys.argv[1:]

    if not args:
        print(USAGE)
        return 1

    command = args[0]

    if command == "test":
        return cmd_test()

    if command == "run":
        return cmd_run()

    if command == "report":
        notify = "--notify" in args
        return cmd_report(notify)

    print(f"Unknown command: {command!r}\n")
    print(USAGE)
    return 1


if __name__ == "__main__":
    sys.exit(main())
