from __future__ import annotations

import asyncio
from urllib.parse import urlparse

from httpx import ConnectTimeout, ReadTimeout

from supercrawler.common.async_work_scheduler_interface import AsyncWorkSchedulerInterface
from supercrawler.common.bounded_async_work_scheduler import BoundedAsyncWorkScheduler
from supercrawler.common.logger import get_logger
from supercrawler.crawler.explore_url_operation_factory import ExploreUrlOperationFactory
from supercrawler.model.page import Page
from supercrawler.model.page_exploration_result import PageExplorationResult
from supercrawler.web.scraper import Scraper

logger = get_logger(__name__)


class SubDomainExplorer:
    def __init__(
        self,
        url: str,
        scheduler: AsyncWorkSchedulerInterface[None] | None = None,
        scraper: Scraper = Scraper()
    ) -> None:
        self.url = url
        self.base_url = url
        self._base_host = urlparse(url).hostname
        self.explored_pages: list[Page] = []
        self._exploration_results: list[PageExplorationResult] | None = None
        self._tracked_urls: set[str] = {self.base_url}
        self._tracked_urls_lock = asyncio.Lock()
        self.scraper = scraper
        self.scheduler = scheduler or BoundedAsyncWorkScheduler(10)
        self.operation_factory = ExploreUrlOperationFactory(
            should_retry=lambda error: isinstance(error, ConnectTimeout)
            or isinstance(error, ReadTimeout)
            or isinstance(error, TimeoutError),
            retries=5,
        )

    async def explore(self) -> list[PageExplorationResult]:
        if self._exploration_results is None:
            logger.info("Exploring subdomain starting from %s", self.url)

            await self.scheduler.schedule(
                work=self.operation_factory.create(
                    target_url=self.url,
                    base_url=self.base_url,
                    scheduler=self.scheduler,
                    scraper=self.scraper,
                    explored_pages=self.explored_pages,
                    tracked_urls=self._tracked_urls,
                    tracked_urls_lock=self._tracked_urls_lock,
                ),
                work_id=self.base_url,
            )

            work_outcomes_by_id = await self.scheduler.execute()
            pages_by_url = {page.url: page for page in self.explored_pages}
            self._exploration_results = [
                PageExplorationResult(
                    url=url,
                    status="success" if work_outcome.succeeded else "failure",
                    page=pages_by_url.get(url),
                    error=str(work_outcome.error) if work_outcome.error is not None else None,
                )
                for url, work_outcome in work_outcomes_by_id.items()
            ]

            logger.info("Finished exploring %s pages under %s", len(self.explored_pages), self.url)
        else:
            logger.info("Returning cached exploration results for %s", self.url)

        return self._exploration_results
