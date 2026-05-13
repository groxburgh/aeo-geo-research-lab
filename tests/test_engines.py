from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import responses as responses_lib

from src.engines.anthropic_engine import AnthropicEngine
from src.engines.openai_engine import OpenAIEngine
from src.engines.perplexity_engine import PerplexityEngine
from src.models import NormalizedResult

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def _build_openai_mock(data: dict) -> MagicMock:
    """Build a mock object that mirrors the OpenAI Responses API response structure."""
    output = []
    for item in data["output"]:
        mock_item = SimpleNamespace(type=item["type"])
        if item["type"] == "message":
            parts = []
            for p in item.get("content", []):
                annotations = [
                    SimpleNamespace(type=a["type"], url=a.get("url", ""), title=a.get("title"))
                    for a in p.get("annotations", [])
                ]
                parts.append(SimpleNamespace(type=p["type"], text=p.get("text", ""), annotations=annotations))
            mock_item.content = parts
        output.append(mock_item)

    usage = SimpleNamespace(
        input_tokens=data["usage"]["input_tokens"],
        output_tokens=data["usage"]["output_tokens"],
    )
    return SimpleNamespace(model=data["model"], output=output, usage=usage)


def _build_anthropic_mock(data: dict) -> MagicMock:
    """Build a mock object mirroring the Anthropic Messages API response structure."""
    content = []
    for block in data["content"]:
        if block["type"] == "web_search_tool_result":
            raw_content = block.get("content", [])
            results = [
                SimpleNamespace(type=r["type"], url=r["url"], title=r.get("title"))
                for r in raw_content
                if isinstance(r, dict)
            ]
            content.append(SimpleNamespace(type=block["type"], content=results))
        else:
            content.append(SimpleNamespace(
                type=block["type"],
                text=block.get("text", ""),
                name=block.get("name"),
            ))
    usage = SimpleNamespace(
        input_tokens=data["usage"]["input_tokens"],
        output_tokens=data["usage"]["output_tokens"],
    )
    return SimpleNamespace(model=data["model"], content=content, usage=usage)


class TestOpenAIEngine:
    def test_parse_response(self):
        data = _load("openai_response.json")
        mock_response = _build_openai_mock(data)

        with patch("openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.responses.create.return_value = mock_response

            engine = OpenAIEngine(api_key="test-key")
            result = engine.run_query("q-test", "Test prompt", 1, "2026-04")

        assert isinstance(result, NormalizedResult)
        assert result.engine == "chatgpt"
        assert result.model_version == "gpt-4o-2024-11-20"
        assert result.response_text == "Ready."
        assert result.input_tokens == 20
        assert result.output_tokens == 5
        assert result.error is None
        assert len(result.citations) == 1
        assert result.citations[0].url == "https://example.com/article"
        assert result.citations[0].domain == "example.com"
        assert result.citations[0].position == 1

    def test_error_returns_result_with_error_field(self):
        with patch("openai.OpenAI") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.responses.create.side_effect = Exception("API error")

            engine = OpenAIEngine(api_key="test-key")
            result = engine.run_query("q-test", "Test prompt", 1, "2026-04")

        assert result.error == "API error"
        assert result.response_text == ""
        assert result.citations == []


class TestPerplexityEngine:
    @responses_lib.activate
    def test_parse_response(self):
        data = _load("perplexity_response.json")
        responses_lib.add(
            responses_lib.POST,
            "https://api.perplexity.ai/chat/completions",
            json=data,
            status=200,
        )

        engine = PerplexityEngine(api_key="test-key")
        result = engine.run_query("q-test", "Test prompt", 1, "2026-04")

        assert isinstance(result, NormalizedResult)
        assert result.engine == "perplexity"
        assert result.model_version == "sonar"
        assert result.response_text == "Ready."
        assert result.input_tokens == 15
        assert result.output_tokens == 5
        assert result.error is None
        assert len(result.citations) == 2
        assert result.citations[0].url == "https://example.com/source1"
        assert result.citations[0].title is None
        assert result.citations[1].position == 2

    @responses_lib.activate
    def test_http_error_returns_result_with_error_field(self):
        responses_lib.add(
            responses_lib.POST,
            "https://api.perplexity.ai/chat/completions",
            status=429,
        )

        engine = PerplexityEngine(api_key="test-key")
        result = engine.run_query("q-test", "Test prompt", 1, "2026-04")

        assert result.error is not None
        assert result.response_text == ""


class TestAnthropicEngine:
    def test_parse_response(self):
        data = _load("anthropic_response.json")
        mock_response = _build_anthropic_mock(data)

        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.return_value = mock_response

            engine = AnthropicEngine(api_key="test-key")
            result = engine.run_query("q-test", "Test prompt", 1, "2026-04")

        assert isinstance(result, NormalizedResult)
        assert result.engine == "claude"
        assert result.model_version == "claude-sonnet-4-6-20251001"
        assert result.response_text == "Ready."
        assert result.input_tokens == 25
        assert result.output_tokens == 8
        assert result.error is None
        assert len(result.citations) == 1
        assert result.citations[0].url == "https://example.com/result"
        assert result.citations[0].title == "Example Result"

    def test_error_returns_result_with_error_field(self):
        with patch("anthropic.Anthropic") as mock_cls:
            mock_client = MagicMock()
            mock_cls.return_value = mock_client
            mock_client.messages.create.side_effect = Exception("API error")

            engine = AnthropicEngine(api_key="test-key")
            result = engine.run_query("q-test", "Test prompt", 1, "2026-04")

        assert result.error == "API error"
        assert result.response_text == ""
