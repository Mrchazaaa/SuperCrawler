from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock

from supercrawler.common.scheduling.work_outcome import WorkOutcome
from supercrawler.crawler.sub_domain_explorer import SubDomainExplorer
from supercrawler.model.page import Page
from supercrawler.model.page_content import PageContent

EXAMPLE_URL = "https://example.com"

def _create_explorer(url: str = EXAMPLE_URL) -> tuple[SubDomainExplorer, AsyncMock, Mock]:
    scheduler = AsyncMock()
    scheduler.schedule.return_value = url
    scheduler.execute.return_value = {}

    operation_factory = Mock()

    scraper = AsyncMock()

    explorer = SubDomainExplorer(
        url=url,
        scheduler=scheduler,
        scraper=scraper,
        operation_factory=operation_factory,
    )

    return explorer, scheduler, operation_factory


def test_explore_schedules_base_url_with_work_created_by_factory() -> None:
    explorer, scheduler, operation_factory = _create_explorer()

    results = asyncio.run(explorer.explore())

    assert results == []
    operation_factory.create.assert_called_once()
    create_kwargs = operation_factory.create.call_args.kwargs
    assert create_kwargs["target_url"] == EXAMPLE_URL
    assert create_kwargs["base_url"] == EXAMPLE_URL
    assert create_kwargs["scheduler"] is scheduler
    assert create_kwargs["scraper"] is explorer.scraper
    scheduler.schedule.assert_awaited_once_with(
        work=operation_factory.create.return_value,
        work_id=EXAMPLE_URL,
    )
    scheduler.execute.assert_awaited_once_with()


def test_explore_maps_success_and_failure_outcomes_to_results() -> None:
    explorer, scheduler, _ = _create_explorer()
    successful_page = Page(1, EXAMPLE_URL, PageContent(["/next"]))
    scheduler.execute.return_value = {
        successful_page.url: WorkOutcome(value=successful_page, succeeded=True),
        f"{EXAMPLE_URL}/missing": WorkOutcome(
            error=RuntimeError("boom"),
            succeeded=False,
        ),
    }

    results = asyncio.run(explorer.explore())

    assert [(result.url, result.status) for result in results] == [
        (EXAMPLE_URL, "success"),
        (f"{EXAMPLE_URL}/missing", "failure"),
    ]
    assert results[0].page is successful_page
    assert results[0].error is None
    assert results[1].page is None
    assert results[1].error == "boom"


def test_explore_returns_cached_results_on_second_call() -> None:
    explorer, scheduler, operation_factory = _create_explorer()
    successful_page = Page(1, EXAMPLE_URL, PageContent([]))
    expected_results = {
        EXAMPLE_URL: WorkOutcome(value=successful_page, succeeded=True),
    }
    scheduler.execute.return_value = expected_results

    first_results = asyncio.run(explorer.explore())
    second_results = asyncio.run(explorer.explore())

    assert first_results is second_results
    operation_factory.create.assert_called_once()
    scheduler.schedule.assert_awaited_once()
    scheduler.execute.assert_awaited_once()
