from __future__ import annotations

from collections.abc import Callable

from supercrawler.common.operation_invoker import OperationInvoker
from supercrawler.common.retryable_operation import RetryableOperation
from supercrawler.crawler.explore_url_operation import ExploreUrlOperation
from supercrawler.model.page import Page
from supercrawler.web.scraper import Scraper


class ExploreUrlOperationFactory:
    def __init__(
        self,
        should_retry: Callable[[BaseException], bool],
        retries: int,
    ) -> None:
        self._should_retry = should_retry
        self._retries = retries

    def create(
        self,
        target_url: str,
        base_url: str,
        operation_invoker: OperationInvoker,
        scraper: Scraper,
        explored_pages: list[Page],
    ) -> RetryableOperation[str]:
        return RetryableOperation(
            operation=ExploreUrlOperation(
                target_url=target_url,
                base_url=base_url,
                operation_invoker=operation_invoker,
                operation_factory=self,
                scraper=scraper,
                explored_pages=explored_pages,
            ),
            should_retry=self._should_retry,
            retries=self._retries,
        )
