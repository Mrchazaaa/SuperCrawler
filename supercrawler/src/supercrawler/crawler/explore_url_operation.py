from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urljoin, urlparse

from supercrawler.common.logger import get_logger
from supercrawler.common.operation import Operation
from supercrawler.common.operation_already_tracked_error import OperationAlreadyTrackedError
from supercrawler.common.operation_id import OperationId
from supercrawler.common.operation_invoker import OperationInvoker
from supercrawler.model.page import Page
from supercrawler.model.page_id import PageId
from supercrawler.web.scraper import Scraper

if TYPE_CHECKING:
    from supercrawler.crawler.explore_url_operation_factory import ExploreUrlOperationFactory


logger = get_logger(__name__)


class ExploreUrlOperation(Operation[str]):

    def __init__(
        self,
        target_url: str,
        base_url: str,
        operation_invoker: OperationInvoker,
        operation_factory: ExploreUrlOperationFactory,
        scraper: Scraper,
        explored_pages: list[Page],
    ) -> None:
        self.target_url = target_url
        self.base_url = base_url
        self.operation_factory = operation_factory
        self.explored_pages = explored_pages
        self.scraper: Scraper = scraper
        self.operation_invoker = operation_invoker

    def execute(self, state: str) -> None:
        normalized_page_url = urljoin(self.base_url, self.target_url)
        page_id = PageId(normalized_page_url)

        logger.debug("Fetching page %s", normalized_page_url)
        found_page_content = self.scraper.fetch_html(normalized_page_url)
        found_page = Page(page_id, self.target_url, found_page_content)

        self.explored_pages += [found_page]
        logger.debug("Discovered page %s", normalized_page_url)

        for link in found_page.content.links:
            normalized_link = urljoin(found_page.url, link)

            if urlparse(normalized_link).hostname != urlparse(self.base_url).hostname:
                logger.debug("Skipping external link %s", normalized_link)
                continue

            try:
                self.operation_invoker.ScheduleOperation(
                    operation=self.operation_factory.create(
                        target_url=normalized_link,
                        base_url=self.base_url,
                        operation_invoker=self.operation_invoker,
                        scraper=self.scraper,
                        explored_pages=self.explored_pages,
                    ),
                    state=normalized_link,
                    operation_id=OperationId(normalized_link)
                )
            except OperationAlreadyTrackedError:
                logger.warning("Skipping already explored link %s", normalized_link)
                continue
