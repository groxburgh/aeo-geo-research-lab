from __future__ import annotations

import pytest

from src import db
from src.models import Citation, NormalizedResult


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
