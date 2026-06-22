"""
One-time patch: fix stale FK references in citations and costs.

When migrate_v2.py ran ALTER TABLE runs RENAME TO runs_old, SQLite 3.26.0+
automatically rewrote the FK references in citations and costs to point to
runs_old. After runs_old was dropped, those FKs became dangling — causing
'no such table: main.runs_old' whenever foreign_keys = ON.

This script recreates both tables with correct REFERENCES runs(run_id).
Safe to re-run: the check at the top skips if FKs are already correct.
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "observatory.db"


def _fk_target(conn: sqlite3.Connection, table: str) -> str | None:
    row = conn.execute(f"PRAGMA foreign_key_list({table})").fetchone()
    return row[2] if row else None  # index 2 is the referenced table name


def patch(db_path: Path) -> None:
    if not db_path.exists():
        print(f"ERROR: {db_path} not found"); sys.exit(1)

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA foreign_keys = OFF")

    cit_target = _fk_target(conn, "citations")
    cost_target = _fk_target(conn, "costs")

    if cit_target == "runs" and cost_target == "runs":
        print("FK references are already correct — nothing to do.")
        conn.close()
        return

    print(f"citations.run_id references '{cit_target}' -> fixing to 'runs'")
    print(f"costs.run_id    references '{cost_target}' -> fixing to 'runs'")

    # Fetch current columns so the recreated tables stay schema-compatible
    cit_cols = [r[1] for r in conn.execute("PRAGMA table_info(citations)")]
    cost_cols = [r[1] for r in conn.execute("PRAGMA table_info(costs)")]

    conn.executescript(f"""
        BEGIN;

        -- Recreate citations with correct FK
        CREATE TABLE citations_new (
            citation_id             TEXT PRIMARY KEY,
            run_id                  TEXT NOT NULL REFERENCES runs(run_id),
            url                     TEXT NOT NULL,
            title                   TEXT,
            position                INTEGER NOT NULL,
            domain                  TEXT NOT NULL,
            cited_at                TEXT NOT NULL,
            domain_v2               TEXT,
            normalization_version   TEXT NOT NULL DEFAULT 'v1'
        );
        INSERT INTO citations_new ({", ".join(cit_cols)})
            SELECT {", ".join(cit_cols)} FROM citations;
        DROP TABLE citations;
        ALTER TABLE citations_new RENAME TO citations;

        -- Recreate costs with correct FK
        CREATE TABLE costs_new (
            cost_id         TEXT PRIMARY KEY,
            run_id          TEXT NOT NULL REFERENCES runs(run_id),
            engine          TEXT NOT NULL,
            month           TEXT NOT NULL,
            cost_usd        REAL NOT NULL,
            recorded_at     TEXT NOT NULL
        );
        INSERT INTO costs_new ({", ".join(cost_cols)})
            SELECT {", ".join(cost_cols)} FROM costs;
        DROP TABLE costs;
        ALTER TABLE costs_new RENAME TO costs;

        COMMIT;
    """)

    conn.execute("PRAGMA foreign_keys = ON")

    # Verify
    cit_after = _fk_target(conn, "citations")
    cost_after = _fk_target(conn, "costs")
    print(f"citations.run_id now references '{cit_after}'")
    print(f"costs.run_id    now references '{cost_after}'")

    row = conn.execute("SELECT COUNT(*) FROM citations").fetchone()
    print(f"citations rows intact: {row[0]}")
    row = conn.execute("SELECT COUNT(*) FROM costs").fetchone()
    print(f"costs rows intact:     {row[0]}")

    conn.close()
    print("Patch complete. Commit data/observatory.db to the repo.")


if __name__ == "__main__":
    patch(DB_PATH)
