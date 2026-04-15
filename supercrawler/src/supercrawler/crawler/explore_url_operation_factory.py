from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from supercrawler.common.operation import Operation
from supercrawler.common.retryable_operation import RetryableOperation
from supercrawler.common.scheduling.bounded_async_work_scheduler import BoundedAsyncWorkScheduler
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
        scheduler: BoundedAsyncWorkScheduler[Page],
        scraper: Scraper,
    ) -> Callable[[], Awaitable[Page]]:
        operation: Operation[None] = RetryableOperation(
            operation=ExploreUrlOperation(
                target_url=target_url,
                base_url=base_url,
                scheduler=scheduler,
                operation_factory=self,
                scraper=scraper,
            ),
            should_retry=self._should_retry,
            retries=self._retries,
        )

        async def work() -> Page:
            return await operation.execute(None)

        return work
