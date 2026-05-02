from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import anthropic

from src.engines.base import Engine
from src.models import Citation, NormalizedResult

INPUT_COST_PER_TOKEN = 0.000003    # Claude Sonnet 4.6 pricing 2026-04
OUTPUT_COST_PER_TOKEN = 0.000015
WEB_SEARCH_COST = 0.010            # $10 per 1000 searches


class AnthropicEngine(Engine):
    def __init__(self, api_key: str) -> None:
        self._client = anthropic.Anthropic(api_key=api_key)

    def run_query(self, query_id: str, prompt: str, run_number: int, month: str) -> NormalizedResult:
        run_id = str(uuid4())
        ran_at = datetime.now(timezone.utc).isoformat()
        try:
            response = self._client.messages.create(
                model="claude-sonnet-4-6",
                tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 1}],
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
            )

            model_version = response.model
            response_text = ""
            citations: list[Citation] = []
            position = 1

            for block in response.content:
                if block.type == "text":
                    response_text += block.text
                elif block.type == "web_search_result":
                    domain = Citation.extract_domain(block.url)
                    citations.append(Citation(
                        citation_id=str(uuid4()),
                        url=block.url,
                        title=getattr(block, "title", None),
                        position=position,
                        domain=domain,
                    ))
                    position += 1

            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            web_search_uses = sum(
                1 for block in response.content
                if getattr(block, "type", None) == "tool_use" and getattr(block, "name", None) == "web_search"
            )
            cost_usd = (
                (input_tokens * INPUT_COST_PER_TOKEN)
                + (output_tokens * OUTPUT_COST_PER_TOKEN)
                + (web_search_uses * WEB_SEARCH_COST)
            )

            return NormalizedResult(
                run_id=run_id,
                query_id=query_id,
                engine="claude",
                model_version=model_version,
                run_number=run_number,
                month=month,
                prompt_sent=prompt,
                response_text=response_text,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                ran_at=ran_at,
                citations=citations,
            )

        except Exception as e:
            return NormalizedResult(
                run_id=run_id,
                query_id=query_id,
                engine="claude",
                model_version="unknown",
                run_number=run_number,
                month=month,
                prompt_sent=prompt,
                response_text="",
                input_tokens=0,
                output_tokens=0,
                cost_usd=0.0,
                ran_at=ran_at,
                error=str(e),
            )
