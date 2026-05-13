from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import requests

from src.engines.base import Engine
from src.models import Citation, NormalizedResult

INPUT_COST_PER_TOKEN = 0.000001   # Sonar pricing 2026-04
OUTPUT_COST_PER_TOKEN = 0.000001
REQUEST_COST = 0.005               # $5 per 1000 requests

_API_URL = "https://api.perplexity.ai/chat/completions"


class PerplexityEngine(Engine):
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def run_query(self, query_id: str, prompt: str, run_number: int, month: str) -> NormalizedResult:
        run_id = str(uuid4())
        ran_at = datetime.now(timezone.utc).isoformat()
        try:
            resp = requests.post(
                _API_URL,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "sonar",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1500,
                    "search_recency_filter": "month",
                },
                timeout=60,
            )
            resp.raise_for_status()
            data = resp.json()

            model_version = data["model"]
            response_text = data["choices"][0]["message"]["content"]
            input_tokens = data["usage"]["prompt_tokens"]
            output_tokens = data["usage"]["completion_tokens"]
            cost_usd = (input_tokens * INPUT_COST_PER_TOKEN) + (output_tokens * OUTPUT_COST_PER_TOKEN) + REQUEST_COST

            citations: list[Citation] = []
            for i, url in enumerate(data.get("citations", [])):
                domain = Citation.extract_domain(url)
                citations.append(Citation(
                    citation_id=str(uuid4()),
                    url=url,
                    title=None,
                    position=i + 1,
                    domain=domain,
                ))

            return NormalizedResult(
                run_id=run_id,
                query_id=query_id,
                engine="perplexity",
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
                engine="perplexity",
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
