from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.domain_normalizer import EXTRACTION_VERSION, normalize_domain
from src.models import NormalizedResult

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"

# Maps engine name to the currently pinned model version. run_exists() uses this to
# treat rows produced by a different model snapshot as needing a fresh run.
_CURRENT_MODELS: dict[str, str] = {
    "chatgpt": "gpt-4o-2024-11-20",
    "claude": "claude-sonnet-4-6",
    "perplexity": "sonar",
}


def _connect(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def apply_schema(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as conn:
        conn.executescript(_SCHEMA_PATH.read_text())


def insert_query(db_path: str, query: dict) -> None:
    sql = """
        INSERT OR IGNORE INTO queries
            (query_id, topic, prompt_text, is_variant, variant_of, zone, query_type, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """
    with _connect(db_path) as conn:
        conn.execute(sql, (
            query["id"],
            query["topic"],
            query["prompt"].strip(),
            1 if query.get("is_variant") else 0,
            query.get("variant_of"),
            query.get("zone", ""),
            query.get("query_type", ""),
            _now_utc(),
        ))


def run_exists(db_path: str, query_id: str, engine: str, run_number: int, month: str) -> bool:
    """Return True only when a valid, non-quarantined run from the current model exists.

    A row is considered valid when:
    - error IS NULL (not a failed run)
    - quarantined = 0 (not explicitly excluded)
    - model_version matches the currently configured model for this engine

    If the pinned model changes, all existing rows for that engine become invisible to
    this check and the next scheduled run automatically re-fetches them.
    """
    current_model = _CURRENT_MODELS.get(engine, "")
    sql = """
        SELECT 1 FROM runs
        WHERE query_id=? AND engine=? AND run_number=? AND month=?
          AND error IS NULL
          AND quarantined=0
          AND model_version=?
        LIMIT 1
    """
    with _connect(db_path) as conn:
        row = conn.execute(sql, (query_id, engine, run_number, month, current_model)).fetchone()
    return row is not None


def clear_error_run(db_path: str, query_id: str, engine: str, run_number: int, month: str) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "DELETE FROM costs WHERE run_id IN "
            "(SELECT run_id FROM runs WHERE query_id=? AND engine=? AND run_number=? AND month=? AND error IS NOT NULL)",
            (query_id, engine, run_number, month),
        )
        conn.execute(
            "DELETE FROM runs WHERE query_id=? AND engine=? AND run_number=? AND month=? AND error IS NOT NULL",
            (query_id, engine, run_number, month),
        )


def quarantine_runs(db_path: str, engine: str, month: str, reason: str) -> int:
    """Mark all active runs for engine+month as quarantined. Returns the number of rows affected."""
    sql = """
        UPDATE runs SET quarantined=1, quarantine_reason=?
        WHERE engine=? AND month=? AND quarantined=0
    """
    with _connect(db_path) as conn:
        cur = conn.execute(sql, (reason, engine, month))
        return cur.rowcount


def insert_result(db_path: str, result: NormalizedResult) -> None:
    now = _now_utc()
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO runs
                (run_id, query_id, engine, model_version, run_number, month,
                 prompt_sent, response_text, input_tokens, output_tokens,
                 cost_usd, ran_at, error, extraction_version, citations_extracted)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.run_id, result.query_id, result.engine, result.model_version,
                result.run_number, result.month, result.prompt_sent, result.response_text,
                result.input_tokens, result.output_tokens, result.cost_usd,
                result.ran_at, result.error,
                EXTRACTION_VERSION,
                1 if result.citations else 0,
            ),
        )
        for citation in result.citations:
            conn.execute(
                """
                INSERT INTO citations
                    (citation_id, run_id, url, title, position, domain, cited_at,
                     domain_v2, normalization_version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    citation.citation_id, result.run_id, citation.url,
                    citation.title, citation.position, citation.domain, result.ran_at,
                    normalize_domain(citation.url),
                    EXTRACTION_VERSION,
                ),
            )
        conn.execute(
            """
            INSERT INTO costs (cost_id, run_id, engine, month, cost_usd, recorded_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (str(uuid4()), result.run_id, result.engine, result.month, result.cost_usd, now),
        )


def get_month_cost(db_path: str, month: str) -> float:
    sql = "SELECT COALESCE(SUM(cost_usd), 0.0) FROM costs WHERE month = ?"
    with _connect(db_path) as conn:
        row = conn.execute(sql, (month,)).fetchone()
    return float(row[0])


def get_runs_for_month(db_path: str, month: str) -> list[dict]:
    sql = "SELECT * FROM runs_active WHERE month = ? ORDER BY ran_at"
    with _connect(db_path) as conn:
        return [dict(r) for r in conn.execute(sql, (month,)).fetchall()]


def get_citations_for_month(db_path: str, month: str) -> list[dict]:
    sql = """
        SELECT c.* FROM citations c
        JOIN runs_active r ON r.run_id = c.run_id
        WHERE r.month = ?
        ORDER BY c.cited_at, c.position
    """
    with _connect(db_path) as conn:
        return [dict(r) for r in conn.execute(sql, (month,)).fetchall()]


def get_costs_for_month(db_path: str, month: str) -> list[dict]:
    sql = "SELECT * FROM costs WHERE month = ? ORDER BY recorded_at"
    with _connect(db_path) as conn:
        return [dict(r) for r in conn.execute(sql, (month,)).fetchall()]
