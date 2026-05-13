from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from src import db, runner
from src.models import Citation, NormalizedResult


def _make_result(query_id: str, engine: str, run_number: int, month: str) -> NormalizedResult:
    from uuid import uuid4
    return NormalizedResult(
        run_id=str(uuid4()),
        query_id=query_id,
        engine=engine,
        model_version="test-model",
        run_number=run_number,
        month=month,
        prompt_sent="test",
        response_text="Ready.",
        input_tokens=10,
        output_tokens=5,
        cost_usd=0.0001,
        ran_at="2026-04-01T02:00:00+00:00",
        citations=[
            Citation(
                citation_id=str(uuid4()),
                url="https://example.com",
                title="Example",
                position=1,
                domain="example.com",
            )
        ],
    )


@pytest.fixture
def tmp_db(tmp_path):
    path = str(tmp_path / "test.db")
    db.apply_schema(path)
    return path


@pytest.fixture
def mini_prompts(tmp_path):
    import yaml
    queries = [
        {
            "id": "q-test-1",
            "topic": "Test Query",
            "prompt": "What is content operations?",
            "is_variant": False,
            "variant_of": None,
            "zone": "content-operations",
            "query_type": "informational",
        }
    ]
    path = str(tmp_path / "prompts.yaml")
    with open(path, "w") as f:
        yaml.dump(queries, f)
    return path


def _mock_engine(query_id, engine_name):
    m = MagicMock()
    m.run_query.side_effect = lambda qid, prompt, run_number, month: _make_result(
        qid, engine_name, run_number, month
    )
    return m


@patch.dict("os.environ", {
    "OPENAI_API_KEY": "test", "PERPLEXITY_API_KEY": "test", "ANTHROPIC_API_KEY": "test"
})
@patch("src.runner.OpenAIEngine")
@patch("src.runner.PerplexityEngine")
@patch("src.runner.AnthropicEngine")
def test_sweep_writes_results(MockAnthropic, MockPerplexity, MockOpenAI, tmp_db, mini_prompts):
    MockOpenAI.return_value = _mock_engine("q-test-1", "chatgpt")
    MockPerplexity.return_value = _mock_engine("q-test-1", "perplexity")
    MockAnthropic.return_value = _mock_engine("q-test-1", "claude")

    exit_code = runner.run_sweep(tmp_db, mini_prompts, "2026-04", 40.0)

    assert exit_code == 0
    runs = db.get_runs_for_month(tmp_db, "2026-04")
    assert len(runs) == 9  # 1 query × 3 engines × 3 runs


@patch.dict("os.environ", {
    "OPENAI_API_KEY": "test", "PERPLEXITY_API_KEY": "test", "ANTHROPIC_API_KEY": "test"
})
@patch("src.runner.OpenAIEngine")
@patch("src.runner.PerplexityEngine")
@patch("src.runner.AnthropicEngine")
def test_sweep_skips_existing_runs(MockAnthropic, MockPerplexity, MockOpenAI, tmp_db, mini_prompts):
    MockOpenAI.return_value = _mock_engine("q-test-1", "chatgpt")
    MockPerplexity.return_value = _mock_engine("q-test-1", "perplexity")
    MockAnthropic.return_value = _mock_engine("q-test-1", "claude")

    runner.run_sweep(tmp_db, mini_prompts, "2026-04", 40.0)
    runner.run_sweep(tmp_db, mini_prompts, "2026-04", 40.0)  # second sweep

    runs = db.get_runs_for_month(tmp_db, "2026-04")
    assert len(runs) == 9  # still 9, not 18


@patch.dict("os.environ", {
    "OPENAI_API_KEY": "test", "PERPLEXITY_API_KEY": "test", "ANTHROPIC_API_KEY": "test"
})
@patch("src.runner.OpenAIEngine")
@patch("src.runner.PerplexityEngine")
@patch("src.runner.AnthropicEngine")
def test_sweep_engine_filter_runs_only_selected_engine(MockAnthropic, MockPerplexity, MockOpenAI, tmp_db, mini_prompts):
    MockOpenAI.return_value = _mock_engine("q-test-1", "chatgpt")
    MockPerplexity.return_value = _mock_engine("q-test-1", "perplexity")
    MockAnthropic.return_value = _mock_engine("q-test-1", "claude")

    exit_code = runner.run_sweep(tmp_db, mini_prompts, "2026-04", 40.0, engine_filter="perplexity")

    assert exit_code == 0
    runs = db.get_runs_for_month(tmp_db, "2026-04")
    assert len(runs) == 3  # 1 query × 1 engine × 3 runs
    assert all(r["engine"] == "perplexity" for r in runs)
    MockOpenAI.assert_not_called()
    MockAnthropic.assert_not_called()


@patch.dict("os.environ", {
    "OPENAI_API_KEY": "test", "PERPLEXITY_API_KEY": "test", "ANTHROPIC_API_KEY": "test"
})
@patch("src.runner.OpenAIEngine")
@patch("src.runner.PerplexityEngine")
@patch("src.runner.AnthropicEngine")
def test_sweep_retries_error_rows(MockAnthropic, MockPerplexity, MockOpenAI, tmp_db, mini_prompts):
    from uuid import uuid4
    query = {
        "id": "q-test-1", "topic": "Test Query", "prompt": "What is content operations?",
        "is_variant": False, "variant_of": None, "zone": "content-operations", "query_type": "informational",
    }
    db.insert_query(tmp_db, query)
    error_result = NormalizedResult(
        run_id=str(uuid4()),
        query_id="q-test-1",
        engine="perplexity",
        model_version="error:no-response",
        run_number=1,
        month="2026-04",
        prompt_sent="What is content operations?",
        response_text="",
        input_tokens=0,
        output_tokens=0,
        cost_usd=0.0,
        ran_at="2026-04-01T02:00:00+00:00",
        citations=[],
        error="API failed",
    )
    db.insert_result(tmp_db, error_result)

    MockOpenAI.return_value = _mock_engine("q-test-1", "chatgpt")
    MockPerplexity.return_value = _mock_engine("q-test-1", "perplexity")
    MockAnthropic.return_value = _mock_engine("q-test-1", "claude")

    exit_code = runner.run_sweep(tmp_db, mini_prompts, "2026-04", 40.0, engine_filter="perplexity")

    assert exit_code == 0
    runs = db.get_runs_for_month(tmp_db, "2026-04")
    assert len(runs) == 3
    assert all(r["error"] is None for r in runs)


@patch.dict("os.environ", {
    "OPENAI_API_KEY": "test", "PERPLEXITY_API_KEY": "test", "ANTHROPIC_API_KEY": "test"
})
@patch("src.runner.OpenAIEngine")
@patch("src.runner.PerplexityEngine")
@patch("src.runner.AnthropicEngine")
def test_sweep_returns_2_when_budget_exceeded(MockAnthropic, MockPerplexity, MockOpenAI, tmp_db, mini_prompts):
    MockOpenAI.return_value = _mock_engine("q-test-1", "chatgpt")
    MockPerplexity.return_value = _mock_engine("q-test-1", "perplexity")
    MockAnthropic.return_value = _mock_engine("q-test-1", "claude")

    # Run with a budget that will be exceeded after first API call (cost 0.0001 per call)
    exit_code = runner.run_sweep(tmp_db, mini_prompts, "2026-04", 0.00005)
    assert exit_code == 2
