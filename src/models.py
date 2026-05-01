from __future__ import annotations

from dataclasses import dataclass, field
from urllib.parse import urlparse


@dataclass
class Citation:
    citation_id: str
    url: str
    position: int
    domain: str
    title: str | None = None

    @staticmethod
    def extract_domain(url: str) -> str:
        hostname = urlparse(url).hostname or ""
        parts = hostname.split(".")
        return ".".join(parts[-2:]) if len(parts) >= 2 else hostname


@dataclass
class NormalizedResult:
    run_id: str
    query_id: str
    engine: str          # "chatgpt" | "perplexity" | "claude"
    model_version: str
    run_number: int
    month: str           # "YYYY-MM"
    prompt_sent: str
    response_text: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    ran_at: str          # ISO-8601 UTC
    citations: list[Citation] = field(default_factory=list)
    error: str | None = None
