from __future__ import annotations

from supercrawler.model.page_content import PageContent
from supercrawler.model.page_exploration_result import PageExplorationResult


def serialize_configuration(
    *,
    url: str,
    log_level: str,
    persist_logs: bool,
    max_concurrency: int,
) -> dict[str, object]:
    return {
        "url": url,
        "log_level": log_level,
        "persist_logs": persist_logs,
        "max_concurrency": max_concurrency,
    }


def serialize_crawl_output(
    *,
    configuration: dict[str, object],
    started_at: str,
    logs_filepath: str,
    duration_seconds: float,
    results: list[PageExplorationResult],
) -> dict[str, object]:
    return {
        "configuration": configuration,
        "started_at": started_at,
        "logs_filepath": logs_filepath,
        "duration_seconds": duration_seconds,
        "results": [_serialize_result(result) for result in results],
    }


def _serialize_page_content(content: PageContent) -> dict[str, object]:
    return {
        "links": content.links,
    }


def _serialize_result(result: PageExplorationResult) -> dict[str, object]:
    return {
        "url": result.url,
        "status": result.status,
        "page_content": _serialize_page_content(result.page.content) if result.page is not None else None,
        "error": result.error,
    }
