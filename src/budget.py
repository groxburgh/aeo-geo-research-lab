from __future__ import annotations

from src import db


def check_budget(db_path: str, month: str, budget_usd: float) -> bool:
    """Return True if spend is under budget (safe to proceed), False if circuit breaker should fire."""
    spent = db.get_month_cost(db_path, month)
    return spent < budget_usd
