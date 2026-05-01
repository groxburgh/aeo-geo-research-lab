from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import openai

from src.engines.base import Engine
from src.models import Citation, NormalizedResult

INPUT_COST_PER_TOKEN = 0.0000025   # GPT-4o pricing 2026-04
OUTPUT_COST_PER_TOKEN = 0.000010


class OpenAIEngine(Engine):
    def __init__(self, api_key: str) -> None:
        self._client = openai.OpenAI(api_key=api_key)

    def run_query(self, query_id: str, prompt: str, run_number: int, month: str) -> NormalizedResult:
        run_id = str(uuid4())
        ran_at = datetime.now(timezone.utc).isoformat()
        try:
            response = self._client.responses.create(
                model="gpt-4o",
                tools=[{"type": "web_search_preview"}],
                input=prompt,
                max_output_tokens=1500,
            )

            model_version = response.model

            response_text = ""
            for item in response.output:
                if item.type == "message":
                    for part in item.content:
                        if part.type == "output_text":
                            response_text += part.text

            citations: list[Citation] = []
            position = 1
            for item in response.output:
                if item.type == "web_search_call":
                    for result in item.results:
                        domain = Citation.extract_domain(result.url)
                        citations.append(Citation(
                            citation_id=str(uuid4()),
                            url=result.url,
                            title=getattr(result, "title", None),
                            position=position,
                            domain=domain,
                        ))
                        position += 1

            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost_usd = (input_tokens * INPUT_COST_PER_TOKEN) + (output_tokens * OUTPUT_COST_PER_TOKEN)

            return NormalizedResult(
                run_id=run_id,
                query_id=query_id,
                engine="chatgpt",
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
                engine="chatgpt",
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
