from __future__ import annotations


def post_to_notion(db_path: str, month: str, report_path: str, notion_api_key: str, database_id: str) -> None:
    """Post monthly summary to Notion review database. Failure is non-fatal."""
    raise NotImplementedError
