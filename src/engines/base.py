from __future__ import annotations

from abc import ABC, abstractmethod

from src.models import NormalizedResult


class Engine(ABC):
    @abstractmethod
    def run_query(self, query_id: str, prompt: str, run_number: int, month: str) -> NormalizedResult:
        """Execute a single query and return a normalized result."""
        ...
