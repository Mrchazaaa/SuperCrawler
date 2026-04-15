from __future__ import annotations

from urllib.parse import urlparse

from supercrawler.common.scheduling.async_work_scheduler_interface import AsyncWorkSchedulerInterface
from supercrawler.common.logging.logger import get_logger
from supercrawler.common.scheduling.work_id import WorkId
from supercrawler.common.scheduling.work_outcome import WorkOutcome
from supercrawler.crawler.explore_url_operation_factory import ExploreUrlOperationFactory
from supercrawler.model.page import Page
from supercrawler.model.page_exploration_result import PageExplorationResult
from supercrawler.web.scraper import Scraper

logger = get_logger(__name__)


class SubDomainExplorer:
    def __init__(
        self,
        url: str,
        scheduler: AsyncWorkSchedulerInterface[Page],
        scraper: Scraper,
        operation_factory: ExploreUrlOperationFactory
    ) -> None:
        self.url = url
        self.base_url = url
        self._base_host = urlparse(url).hostname
        self._exploration_results: list[PageExplorationResult] | None = None
        self.scraper = scraper
        self.scheduler = scheduler
        self.operation_factory = operation_factory

    async def explore(self) -> list[PageExplorationResult]:
        if self._exploration_results is None:
            logger.info("Exploring subdomain starting from %s", self.url)

            await self.scheduler.schedule(
                work=self.operation_factory.create(
                    target_url=self.url,
                    base_url=self.base_url,
                    scheduler=self.scheduler,
                    scraper=self.scraper,
                ),
                work_id=self.base_url,
            )

            work_outcomes_by_id = await self.scheduler.execute()
            self._exploration_results = [
                self._to_exploration_result(work_id, work_outcome)
                for work_id, work_outcome in work_outcomes_by_id.items()
            ]

            logger.info("Finished exploring %s pages under %s", len(self._exploration_results), self.url)
        else:
            logger.info("Returning cached exploration results for %s", self.url)

        return self._exploration_results

    def _to_exploration_result(
        self,
        work_id: WorkId,
        work_outcome: WorkOutcome[Page],
    ) -> PageExplorationResult:
        return PageExplorationResult(
            url=work_id,
            status="success" if work_outcome.succeeded else "failure",
            page=work_outcome.value,
            error=str(work_outcome.error) if work_outcome.error is not None else None,
        )
