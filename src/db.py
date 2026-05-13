from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from src.models import NormalizedResult

_SCHEMA_PATH = Path(__file__).parent / "schema.sql"


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
    sql = "SELECT 1 FROM runs WHERE query_id=? AND engine=? AND run_number=? AND month=? AND error IS NULL"
    with _connect(db_path) as conn:
        row = conn.execute(sql, (query_id, engine, run_number, month)).fetchone()
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


def insert_result(db_path: str, result: NormalizedResult) -> None:
    now = _now_utc()
    with _connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO runs
                (run_id, query_id, engine, model_version, run_number, month,
                 prompt_sent, response_text, input_tokens, output_tokens,
                 cost_usd, ran_at, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.run_id, result.query_id, result.engine, result.model_version,
                result.run_number, result.month, result.prompt_sent, result.response_text,
                result.input_tokens, result.output_tokens, result.cost_usd,
                result.ran_at, result.error,
            ),
        )
        for citation in result.citations:
            conn.execute(
                """
                INSERT INTO citations
                    (citation_id, run_id, url, title, position, domain, cited_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    citation.citation_id, result.run_id, citation.url,
                    citation.title, citation.position, citation.domain, result.ran_at,
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
    sql = "SELECT * FROM runs WHERE month = ? ORDER BY ran_at"
    with _connect(db_path) as conn:
        return [dict(r) for r in conn.execute(sql, (month,)).fetchall()]


def get_citations_for_month(db_path: str, month: str) -> list[dict]:
    sql = """
        SELECT c.* FROM citations c
        JOIN runs r ON r.run_id = c.run_id
        WHERE r.month = ?
        ORDER BY c.cited_at, c.position
    """
    with _connect(db_path) as conn:
        return [dict(r) for r in conn.execute(sql, (month,)).fetchall()]


def get_costs_for_month(db_path: str, month: str) -> list[dict]:
    sql = "SELECT * FROM costs WHERE month = ? ORDER BY recorded_at"
    with _connect(db_path) as conn:
        return [dict(r) for r in conn.execute(sql, (month,)).fetchall()]
