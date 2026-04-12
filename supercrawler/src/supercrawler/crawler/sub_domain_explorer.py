from __future__ import annotations

from urllib.parse import urljoin, urlparse

from supercrawler.common.logger import get_logger
from supercrawler.model.page import Page
from supercrawler.model.page_id import PageId
from supercrawler.web.scraper import Scraper


logger = get_logger(__name__)


class SubDomainExplorer:
    def __init__(self, url: str, scraper: Scraper | None = None):
        self.url = url
        self.explored_pages: list[Page] = []
        self._explored_page_ids: set[PageId] = set()
        self.scraper: Scraper = scraper or Scraper()
        self._base_host = urlparse(url).hostname

    def explore(self) -> list[Page]:
        if not self.explored_pages:
            logger.info("Exploring subdomain starting from %s", self.url)
            self.__internal_do_explore(self.url)
            logger.info("Finished exploring %s pages under %s", len(self.explored_pages), self.url)
        else:
            logger.info("Returning cached exploration results for %s", self.url)

        return self.explored_pages

    def __internal_do_explore(self, url: str) -> list[Page]:
        normalized_page_url = urljoin(self.url, url)
        page_id = PageId(normalized_page_url)

        logger.debug("Fetching page %s", normalized_page_url)
        found_page_content = self.scraper.fetch_html(normalized_page_url)
        found_page = Page(page_id, url, found_page_content)

        self._explored_page_ids.add(page_id)
        self.explored_pages += [found_page]
        logger.debug("Discovered page %s", normalized_page_url)

        for link in found_page.content.links:
            normalized_link = urljoin(found_page.url, link)

            if urlparse(normalized_link).hostname != self._base_host:
                logger.debug("Skipping external link %s", normalized_link)
                continue

            if PageId(normalized_link) not in self._explored_page_ids:
                logger.debug("Following internal link %s", normalized_link)
                self.__internal_do_explore(normalized_link)
            else:
                logger.debug("Skipping already explored link %s", normalized_link)
