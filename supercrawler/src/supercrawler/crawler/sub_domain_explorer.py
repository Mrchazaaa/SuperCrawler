from __future__ import annotations

from urllib.parse import urlparse

from supercrawler.common.logger import get_logger
from supercrawler.common.concurrent_operation_invoker import ConcurrentOperationInvoker
from supercrawler.common.operation_id import OperationId
from supercrawler.common.operation_invoker import OperationInvoker
from supercrawler.crawler.explore_url_operation_factory import ExploreUrlOperationFactory
from supercrawler.model.page import Page
from supercrawler.web.scraper import Scraper

logger = get_logger(__name__)


class SubDomainExplorer:
    def __init__(
        self,
        url: str,
        operation_invoker: OperationInvoker | None = None,
        scraper: Scraper | None = None,
    ) -> None:
        self.url = url
        self.base_url = url
        self._base_host = urlparse(url).hostname
        self.explored_pages: list[Page] = []
        self.scraper: Scraper = scraper or Scraper()
        self.operation_invoker = operation_invoker or ConcurrentOperationInvoker(level_of_parallelism=8)
        self.operation_factory = ExploreUrlOperationFactory(
            should_retry=lambda error: isinstance(error, TimeoutError),
            retries=5,
        )

    def explore(self) -> list[Page]:
        if not self.explored_pages:
            logger.info("Exploring subdomain starting from %s", self.url)

            self.operation_invoker.ScheduleOperation(
                operation=self.operation_factory.create(
                    target_url=self.url,
                    base_url=self.base_url,
                    operation_invoker=self.operation_invoker,
                    scraper=self.scraper,
                    explored_pages=self.explored_pages,
                ),
                state=None,
                operation_id=OperationId(self.base_url),
            )

            self.operation_invoker.ExecuteOperations()
            logger.info("Finished exploring %s pages under %s", len(self.explored_pages), self.url)
        else:
            logger.info("Returning cached exploration results for %s", self.url)

        return self.explored_pages
