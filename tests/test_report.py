from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest

from src import db, report as report_mod
from src.models import Citation, NormalizedResult


@pytest.fixture
def tmp_db(tmp_path):
    path = str(tmp_path / "test.db")
    db.apply_schema(path)
    return path


@pytest.fixture
def reports_dir(tmp_path):
    d = str(tmp_path / "reports")
    return d


def _insert_run(tmp_db, query_id, engine, run_number, domains):
    query = {
        "id": query_id, "topic": "Test", "prompt": "Test prompt",
        "is_variant": False, "variant_of": None,
        "zone": "aeo-geo", "query_type": "informational",
    }
    db.insert_query(tmp_db, query)
    result = NormalizedResult(
        run_id=str(uuid4()),
        query_id=query_id,
        engine=engine,
        model_version=f"{engine}-model-v1",
        run_number=run_number,
        month="2026-04",
        prompt_sent="Test prompt",
        response_text="Test response",
        input_tokens=10,
        output_tokens=5,
        cost_usd=0.0001,
        ran_at="2026-04-01T02:00:00+00:00",
        citations=[
            Citation(
                citation_id=str(uuid4()),
                url=f"https://{d}/page",
                title=d,
                position=i + 1,
                domain=d,
            )
            for i, d in enumerate(domains)
        ],
    )
    db.insert_result(tmp_db, result)


def test_generate_report_creates_file(tmp_db, reports_dir):
    _insert_run(tmp_db, "q-1", "chatgpt", 1, ["example.com"])
    path = report_mod.generate_report(tmp_db, "2026-04", reports_dir)
    assert Path(path).exists()
    assert path.endswith("2026-04.md")


def test_report_contains_expected_sections(tmp_db, reports_dir):
    _insert_run(tmp_db, "q-1", "chatgpt", 1, ["example.com", "other.org"])
    _insert_run(tmp_db, "q-1", "perplexity", 1, ["example.com"])
    path = report_mod.generate_report(tmp_db, "2026-04", reports_dir)
    content = Path(path).read_text()

    assert "## Budget Summary" in content
    assert "## Citation Frequency by Engine" in content
    assert "## Cross-Engine Domain Overlap" in content
    assert "## Prompt Stability Sub-Study" in content
    assert "## Model Versions" in content
    assert "## Raw Run Log" in content


def test_report_is_idempotent(tmp_db, reports_dir):
    _insert_run(tmp_db, "q-1", "chatgpt", 1, ["example.com"])
    path1 = report_mod.generate_report(tmp_db, "2026-04", reports_dir)
    path2 = report_mod.generate_report(tmp_db, "2026-04", reports_dir)
    assert path1 == path2


def test_jaccard_calculation():
    assert report_mod._jaccard({"a", "b", "c"}, {"b", "c", "d"}) == pytest.approx(0.5)
    assert report_mod._jaccard({"a"}, {"a"}) == pytest.approx(1.0)
    assert report_mod._jaccard({"a"}, {"b"}) == pytest.approx(0.0)
    assert report_mod._jaccard(set(), set()) == pytest.approx(1.0)
