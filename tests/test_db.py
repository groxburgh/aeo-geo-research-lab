from __future__ import annotations

import sqlite3

import pytest

from src import db
from src.models import Citation, NormalizedResult


def _make_result(*, error: str | None = None) -> NormalizedResult:
    from uuid import uuid4
    return NormalizedResult(
        run_id=str(uuid4()),
        query_id="q-001",
        engine="chatgpt",
        model_version="gpt-4o-2024-11-20",
        run_number=1,
        month="2026-04",
        prompt_sent="Test prompt",
        response_text="",
        input_tokens=0,
        output_tokens=0,
        cost_usd=0.0,
        ran_at="2026-04-01T02:00:00+00:00",
        citations=[],
        error=error,
    )


_QUERY = {
    "id": "q-001", "topic": "Test", "prompt": "Test prompt",
    "is_variant": False, "variant_of": None, "zone": "aeo-geo", "query_type": "informational",
}


@pytest.fixture
def tmp_db(tmp_path):
    path = str(tmp_path / "test.db")
    db.apply_schema(path)
    return path


@pytest.fixture
def sample_result():
    return NormalizedResult(
        run_id="run-001",
        query_id="q-001",
        engine="chatgpt",
        model_version="gpt-4o-2024-11-20",
        run_number=1,
        month="2026-04",
        prompt_sent="Test prompt",
        response_text="Test response",
        input_tokens=10,
        output_tokens=5,
        cost_usd=0.000075,
        ran_at="2026-04-01T02:00:00+00:00",
        citations=[
            Citation(
                citation_id="cit-001",
                url="https://example.com/page",
                title="Example",
                position=1,
                domain="example.com",
            )
        ],
    )


def test_apply_schema_creates_tables(tmp_db):
    import sqlite3
    conn = sqlite3.connect(tmp_db)
    tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert {"queries", "runs", "citations", "costs"}.issubset(tables)
    conn.close()


def test_apply_schema_idempotent(tmp_db):
    db.apply_schema(tmp_db)  # second call must not raise


def test_insert_query_and_ignore_duplicate(tmp_db):
    query = {
        "id": "q-001", "topic": "Test", "prompt": "Hello?",
        "is_variant": False, "variant_of": None, "zone": "aeo-geo", "query_type": "informational",
    }
    db.insert_query(tmp_db, query)
    db.insert_query(tmp_db, query)  # duplicate — must not raise or duplicate row


def test_run_exists_false_before_insert(tmp_db):
    assert db.run_exists(tmp_db, "q-001", "chatgpt", 1, "2026-04") is False


def test_run_exists_true_after_insert(tmp_db, sample_result):
    query = {
        "id": "q-001", "topic": "Test", "prompt": "Test prompt",
        "is_variant": False, "variant_of": None, "zone": "aeo-geo", "query_type": "informational",
    }
    db.insert_query(tmp_db, query)
    db.insert_result(tmp_db, sample_result)
    assert db.run_exists(tmp_db, "q-001", "chatgpt", 1, "2026-04") is True


def test_run_exists_false_for_error_row(tmp_db):
    db.insert_query(tmp_db, _QUERY)
    result = _make_result(error="API failed")
    db.insert_result(tmp_db, result)
    assert db.run_exists(tmp_db, result.query_id, result.engine, result.run_number, result.month) is False


def test_clear_error_run_removes_error_row(tmp_db):
    db.insert_query(tmp_db, _QUERY)
    result = _make_result(error="API failed")
    db.insert_result(tmp_db, result)
    db.clear_error_run(tmp_db, result.query_id, result.engine, result.run_number, result.month)
    conn = sqlite3.connect(tmp_db)
    assert conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM costs").fetchone()[0] == 0
    conn.close()


def test_clear_error_run_noop_for_success(tmp_db, sample_result):
    db.insert_query(tmp_db, _QUERY)
    db.insert_result(tmp_db, sample_result)
    db.clear_error_run(tmp_db, sample_result.query_id, sample_result.engine, sample_result.run_number, sample_result.month)
    assert db.run_exists(tmp_db, sample_result.query_id, sample_result.engine, sample_result.run_number, sample_result.month) is True


def test_insert_result_writes_all_tables(tmp_db, sample_result):
    import sqlite3
    query = {
        "id": "q-001", "topic": "Test", "prompt": "Test prompt",
        "is_variant": False, "variant_of": None, "zone": "aeo-geo", "query_type": "informational",
    }
    db.insert_query(tmp_db, query)
    db.insert_result(tmp_db, sample_result)

    conn = sqlite3.connect(tmp_db)
    assert conn.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM citations").fetchone()[0] == 1
    assert conn.execute("SELECT COUNT(*) FROM costs").fetchone()[0] == 1
    conn.close()


def test_get_month_cost_empty(tmp_db):
    assert db.get_month_cost(tmp_db, "2026-04") == 0.0


def test_get_month_cost_sum(tmp_db, sample_result):
    query = {
        "id": "q-001", "topic": "Test", "prompt": "Test prompt",
        "is_variant": False, "variant_of": None, "zone": "aeo-geo", "query_type": "informational",
    }
    db.insert_query(tmp_db, query)
    db.insert_result(tmp_db, sample_result)
    cost = db.get_month_cost(tmp_db, "2026-04")
    assert abs(cost - 0.000075) < 1e-9


def test_run_exists_false_when_model_version_differs(tmp_db):
    """A run recorded with an old model snapshot must not block a fresh run."""
    db.insert_query(tmp_db, _QUERY)
    old_model_result = _make_result()
    # Manually write a row with the old model version
    import sqlite3
    from src.domain_normalizer import EXTRACTION_VERSION
    conn = sqlite3.connect(tmp_db)
    conn.execute(
        """INSERT INTO runs
           (run_id, query_id, engine, model_version, run_number, month,
            prompt_sent, response_text, input_tokens, output_tokens,
            cost_usd, ran_at, error, extraction_version, citations_extracted)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (old_model_result.run_id, "q-001", "chatgpt", "gpt-4o-2024-08-06",
         1, "2026-04", "Test prompt", "", 0, 0, 0.0,
         "2026-04-01T02:00:00+00:00", None, EXTRACTION_VERSION, 0),
    )
    conn.commit()
    conn.close()
    # run_exists must return False because the stored model doesn't match the current pin
    assert db.run_exists(tmp_db, "q-001", "chatgpt", 1, "2026-04") is False


def test_run_exists_false_when_quarantined(tmp_db):
    """A quarantined row must not satisfy run_exists."""
    db.insert_query(tmp_db, _QUERY)
    result = _make_result()
    db.insert_result(tmp_db, result)
    assert db.run_exists(tmp_db, "q-001", "chatgpt", 1, "2026-04") is True
    db.quarantine_runs(tmp_db, "chatgpt", "2026-04", "test quarantine")
    assert db.run_exists(tmp_db, "q-001", "chatgpt", 1, "2026-04") is False


def test_quarantine_runs_returns_row_count(tmp_db):
    """quarantine_runs must return the number of rows it marked."""
    db.insert_query(tmp_db, _QUERY)
    db.insert_result(tmp_db, _make_result())
    count = db.quarantine_runs(tmp_db, "chatgpt", "2026-04", "test")
    assert count == 1
    # Second call on already-quarantined rows returns 0
    assert db.quarantine_runs(tmp_db, "chatgpt", "2026-04", "test again") == 0
