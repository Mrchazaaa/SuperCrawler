from __future__ import annotations

import asyncio

import pytest

from supercrawler.common.scheduling.bounded_async_work_scheduler import BoundedAsyncWorkScheduler
from supercrawler.crawler.explore_url_operation_factory import ExploreUrlOperationFactory
from supercrawler.model.page import Page
from supercrawler.model.page_content import PageContent


class FailingOnceScraper:
    def __init__(self) -> None:
        self.calls = 0

    async def fetch_html(self, url: str) -> PageContent:
        self.calls += 1

        if self.calls == 1:
            raise RuntimeError("temporary failure")

        return PageContent([])


def test_create_returns_async_callable() -> None:
    factory = ExploreUrlOperationFactory(
        should_retry=lambda error: isinstance(error, RuntimeError),
        retries=1,
    )

    work = factory.create(
        target_url="https://example.com",
        base_url="https://example.com",
        scheduler=BoundedAsyncWorkScheduler(max_concurrency=1),
        scraper=FailingOnceScraper(),
        explored_pages=[],
        tracked_urls={"https://example.com"},
        tracked_urls_lock=asyncio.Lock(),
    )

    assert callable(work)


def test_create_retries_explore_work() -> None:
    scraper = FailingOnceScraper()
    explored_pages: list[Page] = []
    factory = ExploreUrlOperationFactory(
        should_retry=lambda error: isinstance(error, RuntimeError),
        retries=1,
    )

    work = factory.create(
        target_url="https://example.com",
        base_url="https://example.com",
        scheduler=BoundedAsyncWorkScheduler(max_concurrency=1),
        scraper=scraper,
        explored_pages=explored_pages,
        tracked_urls={"https://example.com"},
        tracked_urls_lock=asyncio.Lock(),
    )

    page = asyncio.run(work())

    assert scraper.calls == 2
    assert [page.url for page in explored_pages] == ["https://example.com"]
    assert page is explored_pages[0]


def test_create_preserves_failure_when_error_is_not_retryable() -> None:
    factory = ExploreUrlOperationFactory(
        should_retry=lambda error: False,
        retries=1,
    )

    work = factory.create(
        target_url="https://example.com",
        base_url="https://example.com",
        scheduler=BoundedAsyncWorkScheduler(max_concurrency=1),
        scraper=FailingOnceScraper(),
        explored_pages=[],
        tracked_urls={"https://example.com"},
        tracked_urls_lock=asyncio.Lock(),
    )

    with pytest.raises(RuntimeError, match="temporary failure"):
        asyncio.run(work())
