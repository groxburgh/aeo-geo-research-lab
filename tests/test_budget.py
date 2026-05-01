from __future__ import annotations

import pytest

from src import budget, db
from src.models import NormalizedResult


@pytest.fixture
def tmp_db(tmp_path):
    path = str(tmp_path / "test.db")
    db.apply_schema(path)
    return path


def _insert_cost(tmp_db, amount: float) -> None:
    query = {
        "id": "q-budget", "topic": "Budget test", "prompt": "Test",
        "is_variant": False, "variant_of": None, "zone": "aeo-geo", "query_type": "informational",
    }
    db.insert_query(tmp_db, query)
    result = NormalizedResult(
        run_id="run-budget-001",
        query_id="q-budget",
        engine="chatgpt",
        model_version="gpt-4o",
        run_number=1,
        month="2026-04",
        prompt_sent="Test",
        response_text="Test",
        input_tokens=0,
        output_tokens=0,
        cost_usd=amount,
        ran_at="2026-04-01T02:00:00+00:00",
    )
    db.insert_result(tmp_db, result)


def test_check_budget_true_when_empty(tmp_db):
    assert budget.check_budget(tmp_db, "2026-04", 40.0) is True


def test_check_budget_true_when_under(tmp_db):
    _insert_cost(tmp_db, 10.0)
    assert budget.check_budget(tmp_db, "2026-04", 40.0) is True


def test_check_budget_false_when_equal(tmp_db):
    _insert_cost(tmp_db, 40.0)
    assert budget.check_budget(tmp_db, "2026-04", 40.0) is False


def test_check_budget_false_when_over(tmp_db):
    _insert_cost(tmp_db, 41.0)
    assert budget.check_budget(tmp_db, "2026-04", 40.0) is False
