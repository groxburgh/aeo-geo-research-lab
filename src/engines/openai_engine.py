from __future__ import annotations

import logging
from datetime import datetime, timezone
from uuid import uuid4

import openai

from src.engines.base import Engine
from src.models import Citation, NormalizedResult

logger = logging.getLogger(__name__)

INPUT_COST_PER_TOKEN = 0.0000025   # GPT-4o pricing 2026-04
OUTPUT_COST_PER_TOKEN = 0.000010
WEB_SEARCH_COST = 0.030            # $30 per 1000 searches (web_search_preview, basic tier)


class OpenAIEngine(Engine):
    def __init__(self, api_key: str) -> None:
        self._client = openai.OpenAI(api_key=api_key)

    def run_query(self, query_id: str, prompt: str, run_number: int, month: str) -> NormalizedResult:
        run_id = str(uuid4())
        ran_at = datetime.now(timezone.utc).isoformat()
        try:
            response = self._client.responses.create(
                model="gpt-4o-2024-11-20",
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
                if item.type == "message":
                    for part in item.content:
                        if part.type == "output_text":
                            for annotation in part.annotations:
                                if annotation.type == "url_citation":
                                    domain = Citation.extract_domain(annotation.url)
                                    citations.append(Citation(
                                        citation_id=str(uuid4()),
                                        url=annotation.url,
                                        title=annotation.title,
                                        position=position,
                                        domain=domain,
                                    ))
                                    position += 1

            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            web_search_uses = sum(1 for item in response.output if item.type == "web_search_call")
            cost_usd = (
                (input_tokens * INPUT_COST_PER_TOKEN)
                + (output_tokens * OUTPUT_COST_PER_TOKEN)
                + (web_search_uses * WEB_SEARCH_COST)
            )

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
            logger.exception("OpenAI call failed for query_id=%s run=%s", query_id, run_number)
            return NormalizedResult(
                run_id=run_id,
                query_id=query_id,
                engine="chatgpt",
                model_version="error:no-response",
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
