from __future__ import annotations

import pytest

from supercrawler.common.retryable_operation import RetryableOperation
from supercrawler.common.sequential_operation_invoker import SequentialOperationInvoker
from supercrawler.crawler.explore_url_operation_factory import ExploreUrlOperationFactory
from supercrawler.model.page import Page
from supercrawler.model.page_content import PageContent


class FailingOnceScraper:
    def __init__(self) -> None:
        self.calls = 0

    def fetch_html(self, url: str) -> PageContent:
        self.calls += 1

        if self.calls == 1:
            raise RuntimeError("temporary failure")

        return PageContent([])


def test_create_returns_retryable_operation() -> None:
    factory = ExploreUrlOperationFactory(
        should_retry=lambda error: isinstance(error, RuntimeError),
        retries=1,
    )

    operation = factory.create(
        target_url="https://example.com",
        base_url="https://example.com",
        operation_invoker=SequentialOperationInvoker(),
        scraper=FailingOnceScraper(),
        explored_pages=[],
    )

    assert isinstance(operation, RetryableOperation)


def test_create_wraps_explore_url_operation_in_retryable_operation() -> None:
    scraper = FailingOnceScraper()
    explored_pages: list[Page] = []
    factory = ExploreUrlOperationFactory(
        should_retry=lambda error: isinstance(error, RuntimeError),
        retries=1,
    )

    operation = factory.create(
        target_url="https://example.com",
        base_url="https://example.com",
        operation_invoker=SequentialOperationInvoker(),
        scraper=scraper,
        explored_pages=explored_pages,
    )

    operation.execute("https://example.com")

    assert scraper.calls == 2
    assert [page.url for page in explored_pages] == ["https://example.com"]


def test_create_preserves_failure_when_error_is_not_retryable() -> None:
    factory = ExploreUrlOperationFactory(
        should_retry=lambda error: False,
        retries=1,
    )

    operation = factory.create(
        target_url="https://example.com",
        base_url="https://example.com",
        operation_invoker=SequentialOperationInvoker(),
        scraper=FailingOnceScraper(),
        explored_pages=[],
    )

    with pytest.raises(RuntimeError, match="temporary failure"):
        operation.execute("https://example.com")
