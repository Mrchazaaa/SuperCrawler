from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse

from supercrawler.common.bounded_async_work_scheduler import BoundedAsyncWorkScheduler
from supercrawler.common.logger import get_logger
from supercrawler.model.page import Page
from supercrawler.model.page_id import PageId
from supercrawler.web.scraper import Scraper

if TYPE_CHECKING:
    from supercrawler.crawler.explore_url_operation_factory import ExploreUrlOperationFactory


logger = get_logger(__name__)


class ExploreUrlOperation:
    def __init__(
        self,
        target_url: str,
        base_url: str,
        scheduler: BoundedAsyncWorkScheduler[None],
        operation_factory: ExploreUrlOperationFactory,
        scraper: Scraper,
        explored_pages: list[Page],
        tracked_urls: set[str],
        tracked_urls_lock: asyncio.Lock,
    ) -> None:
        self.target_url = target_url
        self.base_url = base_url
        self.operation_factory = operation_factory
        self.explored_pages = explored_pages
        self.scraper: Scraper = scraper
        self.scheduler = scheduler
        self.tracked_urls = tracked_urls
        self.tracked_urls_lock = tracked_urls_lock

    async def run(self) -> None:
        normalized_page_url = urljoin(self.base_url, self.target_url)
        page_id = PageId(normalized_page_url)

        logger.debug("Fetching page %s", normalized_page_url)
        found_page_content = await self.scraper.fetch_html(normalized_page_url)
        found_page = Page(page_id, self.target_url, found_page_content)

        self.explored_pages += [found_page]
        logger.debug("Discovered page %s", normalized_page_url)

        for link in found_page.content.links:
            normalized_link = urljoin(found_page.url, link)

            if urlparse(normalized_link).hostname != urlparse(self.base_url).hostname:
                logger.debug("Skipping external link %s", normalized_link)
                continue

            async with self.tracked_urls_lock:
                if normalized_link in self.tracked_urls:
                    logger.debug("Skipping already tracked link %s", normalized_link)
                    continue

                self.tracked_urls.add(normalized_link)

            await self.scheduler.schedule(
                work=self.operation_factory.create(
                    target_url=normalized_link,
                    base_url=self.base_url,
                    scheduler=self.scheduler,
                    scraper=self.scraper,
                    explored_pages=self.explored_pages,
                    tracked_urls=self.tracked_urls,
                    tracked_urls_lock=self.tracked_urls_lock,
                ),
                work_id=normalized_link,
            )
