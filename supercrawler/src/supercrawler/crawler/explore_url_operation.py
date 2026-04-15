from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse

from supercrawler.common.operation import Operation
from supercrawler.common.scheduling.bounded_async_work_scheduler import BoundedAsyncWorkScheduler
from supercrawler.common.logging.logger import get_logger
from supercrawler.common.scheduling.operation_already_tracked_error import OperationAlreadyTrackedError
from supercrawler.model.page import Page
from supercrawler.model.page_id import PageId
from supercrawler.web.scraper import Scraper

if TYPE_CHECKING:
    from supercrawler.crawler.explore_url_operation_factory import ExploreUrlOperationFactory


logger = get_logger(__name__)


class ExploreUrlOperation(Operation[None]):
    def __init__(
        self,
        target_url: str,
        base_url: str,
        scheduler: BoundedAsyncWorkScheduler[Page],
        operation_factory: ExploreUrlOperationFactory,
        scraper: Scraper,
    ) -> None:
        self.target_url = target_url
        self.base_url = base_url
        self.operation_factory = operation_factory
        self.scraper = scraper
        self.scheduler = scheduler

    async def execute(self, state: None) -> Page:
        normalized_page_url = urljoin(self.base_url, self.target_url)
        page_id = PageId(normalized_page_url)

        logger.debug("Fetching page %s", normalized_page_url)
        found_page_content = await self.scraper.fetch_html(normalized_page_url)
        found_page = Page(page_id, normalized_page_url, found_page_content)

        for link in found_page.content.links:
            normalized_link = urljoin(found_page.url, link)

            if urlparse(normalized_link).hostname != urlparse(self.base_url).hostname:
                logger.debug("Skipping external link %s", normalized_link)
                continue

            try:
                await self.scheduler.schedule(
                    work=self.operation_factory.create(
                        target_url=normalized_link,
                        base_url=self.base_url,
                        scheduler=self.scheduler,
                        scraper=self.scraper,
                    ),
                    work_id=normalized_link,
                )
            except OperationAlreadyTrackedError:
                logger.debug("Skipping already tracked link %s", normalized_link)
                continue

        return found_page
