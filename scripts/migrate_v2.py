"""
One-time migration script: upgrade observatory.db to schema v2.

Run once locally before the June 2026 sweep:
    python scripts/migrate_v2.py

What this does:
  1. Recreates the `runs` table with new columns and a partial UNIQUE index
     (WHERE quarantined = 0) so that a quarantined row and a fresh replacement
     can coexist in the same (query_id, engine, run_number, month) slot.
  2. Adds `domain_v2` and `normalization_version` columns to `citations`.
  3. Quarantines all May 2026 ChatGPT rows (both model versions).
  4. Backfills `domain_v2` for all existing citation rows using tldextract.
  5. Creates the `runs_active` view if it does not already exist.

After running, commit data/observatory.db to the repo.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

# Allow importing from project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.domain_normalizer import EXTRACTION_VERSION, normalize_domain

DB_PATH = Path(__file__).parent.parent / "data" / "observatory.db"

CHATGPT_OLD_MODEL_REASON = (
    "gpt-4o-2024-08-06 predates web_search_preview support; "
    "returned 0 citations across all 177 runs"
)
CHATGPT_PARTIAL_REASON = (
    "May 2026 partial re-run excluded: only 9 of 177 queries were re-run "
    "with gpt-4o-2024-11-20, introducing selection bias"
)


def _run(con: sqlite3.Connection, sql: str, params: tuple = ()) -> sqlite3.Cursor:
    return con.execute(sql, params)


def migrate(db_path: Path) -> None:
    if not db_path.exists():
        print(f"ERROR: database not found at {db_path}")
        sys.exit(1)

    con = sqlite3.connect(str(db_path))
    con.execute("PRAGMA foreign_keys = OFF")  # required during table recreation

    print(f"Migrating {db_path} ...")

    # ── Step 1: Recreate `runs` table ────────────────────────────────────────
    # Check whether the new columns already exist (idempotent re-run).
    existing_cols = {row[1] for row in con.execute("PRAGMA table_info(runs)")}
    needs_recreate = "quarantined" not in existing_cols

    if needs_recreate:
        print("  [1/5] Recreating runs table with new columns and partial UNIQUE index...")
        con.executescript("""
            BEGIN;

            ALTER TABLE runs RENAME TO runs_old;

            CREATE TABLE runs (
                run_id              TEXT PRIMARY KEY,
                query_id            TEXT NOT NULL REFERENCES queries(query_id),
                engine              TEXT NOT NULL,
                model_version       TEXT NOT NULL,
                run_number          INTEGER NOT NULL,
                month               TEXT NOT NULL,
                prompt_sent         TEXT NOT NULL,
                response_text       TEXT NOT NULL,
                input_tokens        INTEGER NOT NULL,
                output_tokens       INTEGER NOT NULL,
                cost_usd            REAL NOT NULL,
                ran_at              TEXT NOT NULL,
                error               TEXT,
                extraction_version  TEXT NOT NULL DEFAULT 'v1',
                citations_extracted INTEGER NOT NULL DEFAULT 0,
                quarantined         INTEGER NOT NULL DEFAULT 0,
                quarantine_reason   TEXT
            );

            INSERT INTO runs (
                run_id, query_id, engine, model_version, run_number, month,
                prompt_sent, response_text, input_tokens, output_tokens,
                cost_usd, ran_at, error
            )
            SELECT
                run_id, query_id, engine, model_version, run_number, month,
                prompt_sent, response_text, input_tokens, output_tokens,
                cost_usd, ran_at, error
            FROM runs_old;

            DROP TABLE runs_old;

            CREATE UNIQUE INDEX IF NOT EXISTS idx_runs_active
                ON runs(query_id, engine, run_number, month) WHERE quarantined = 0;

            COMMIT;
        """)
        print("     done.")
    else:
        print("  [1/5] runs table already has new columns — skipping recreation.")

    # ── Step 2: Add new citations columns ────────────────────────────────────
    cit_cols = {row[1] for row in con.execute("PRAGMA table_info(citations)")}
    if "domain_v2" not in cit_cols:
        print("  [2/5] Adding domain_v2 and normalization_version to citations...")
        con.execute("ALTER TABLE citations ADD COLUMN domain_v2 TEXT")
        con.execute(
            "ALTER TABLE citations ADD COLUMN normalization_version TEXT NOT NULL DEFAULT 'v1'"
        )
        con.commit()
        print("     done.")
    else:
        print("  [2/5] citations already has domain_v2 — skipping.")

    # ── Step 3: Quarantine bad May 2026 ChatGPT rows ─────────────────────────
    print("  [3/5] Quarantining May 2026 ChatGPT rows...")

    cur = con.execute(
        "SELECT COUNT(*) FROM runs WHERE engine='chatgpt' AND month='2026-05' "
        "AND model_version='gpt-4o-2024-08-06' AND quarantined=0"
    )
    old_model_count = cur.fetchone()[0]

    cur = con.execute(
        "SELECT COUNT(*) FROM runs WHERE engine='chatgpt' AND month='2026-05' "
        "AND model_version='gpt-4o-2024-11-20' AND quarantined=0"
    )
    new_model_count = cur.fetchone()[0]

    if old_model_count > 0:
        con.execute(
            "UPDATE runs SET quarantined=1, quarantine_reason=? "
            "WHERE engine='chatgpt' AND month='2026-05' AND model_version='gpt-4o-2024-08-06'",
            (CHATGPT_OLD_MODEL_REASON,),
        )
        print(f"     quarantined {old_model_count} rows (gpt-4o-2024-08-06).")
    else:
        print("     no gpt-4o-2024-08-06 rows to quarantine.")

    if new_model_count > 0:
        con.execute(
            "UPDATE runs SET quarantined=1, quarantine_reason=? "
            "WHERE engine='chatgpt' AND month='2026-05' AND model_version='gpt-4o-2024-11-20'",
            (CHATGPT_PARTIAL_REASON,),
        )
        print(f"     quarantined {new_model_count} rows (gpt-4o-2024-11-20 partial re-run).")
    else:
        print("     no gpt-4o-2024-11-20 rows to quarantine.")

    con.commit()

    # ── Step 4: Backfill domain_v2 ───────────────────────────────────────────
    print("  [4/5] Backfilling domain_v2 for existing citation rows...")
    rows = con.execute(
        "SELECT citation_id, url FROM citations WHERE domain_v2 IS NULL"
    ).fetchall()

    null_count = 0
    batch: list[tuple] = []
    for cid, url in rows:
        d2 = normalize_domain(url)
        if d2 is None:
            null_count += 1
        batch.append((d2, EXTRACTION_VERSION, cid))
        if len(batch) >= 500:
            con.executemany(
                "UPDATE citations SET domain_v2=?, normalization_version=? WHERE citation_id=?",
                batch,
            )
            batch.clear()

    if batch:
        con.executemany(
            "UPDATE citations SET domain_v2=?, normalization_version=? WHERE citation_id=?",
            batch,
        )

    con.commit()
    print(f"     backfilled {len(rows)} citations ({null_count} resolved to NULL — no valid domain).")

    # ── Step 5: Create runs_active view ──────────────────────────────────────
    print("  [5/5] Creating runs_active view...")
    con.execute("""
        CREATE VIEW IF NOT EXISTS runs_active AS
            SELECT * FROM runs WHERE quarantined = 0
    """)
    con.commit()
    print("     done.")

    # ── Summary ───────────────────────────────────────────────────────────────
    total_runs = con.execute("SELECT COUNT(*) FROM runs").fetchone()[0]
    active_runs = con.execute("SELECT COUNT(*) FROM runs_active").fetchone()[0]
    quarantined = total_runs - active_runs
    total_cit = con.execute("SELECT COUNT(*) FROM citations").fetchone()[0]
    backfilled = con.execute(
        "SELECT COUNT(*) FROM citations WHERE domain_v2 IS NOT NULL"
    ).fetchone()[0]

    con.close()

    print()
    print("Migration complete.")
    print(f"  runs total:      {total_runs}")
    print(f"  runs active:     {active_runs}")
    print(f"  runs quarantined:{quarantined}")
    print(f"  citations total: {total_cit}")
    print(f"  domain_v2 filled:{backfilled} / {total_cit}")
    if null_count:
        print(f"  domain_v2 NULL:  {null_count} (URLs with no extractable eTLD+1 — inspect if unexpected)")
    print()
    print("Next step: python run.py report  (to regenerate May 2026 report with cleaned data)")


if __name__ == "__main__":
    migrate(DB_PATH)
