from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from supercrawler.common.bounded_async_work_scheduler import BoundedAsyncWorkScheduler
from supercrawler.common.logger import get_logger
from supercrawler.crawler.explore_url_operation import ExploreUrlOperation
from supercrawler.model.page import Page
from supercrawler.web.scraper import Scraper

logger = get_logger(__name__)


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
        scheduler: BoundedAsyncWorkScheduler[None],
        scraper: Scraper,
        explored_pages: list[Page],
        tracked_urls: set[str],
        tracked_urls_lock: asyncio.Lock,
    ) -> Callable[[], Awaitable[None]]:
        async def run() -> None:
            attempts_remaining = self._retries
            attempt_number = 1

            while True:
                try:
                    logger.debug(
                        "Executing explore work for %s attempt %s",
                        target_url,
                        attempt_number,
                    )
                    await ExploreUrlOperation(
                        target_url=target_url,
                        base_url=base_url,
                        scheduler=scheduler,
                        operation_factory=self,
                        scraper=scraper,
                        explored_pages=explored_pages,
                        tracked_urls=tracked_urls,
                        tracked_urls_lock=tracked_urls_lock,
                    ).run()
                    return
                except BaseException as error:
                    should_retry = attempts_remaining > 0 and self._should_retry(error)

                    if not should_retry:
                        logger.warning(
                            "Explore work for %s failed on attempt %s and will not be retried: %s: %s",
                            target_url,
                            attempt_number,
                            type(error).__name__,
                            error,
                        )
                        raise

                    logger.warning(
                        "Explore work for %s failed on attempt %s and will be retried (%s retries remaining): %s: %s",
                        target_url,
                        attempt_number,
                        attempts_remaining,
                        type(error).__name__,
                        error,
                    )
                    attempts_remaining -= 1
                    attempt_number += 1

        return run
