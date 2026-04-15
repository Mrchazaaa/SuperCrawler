from __future__ import annotations

import asyncio

from httpx import ConnectTimeout, ReadTimeout

from supercrawler.common.scheduling.bounded_async_work_scheduler import BoundedAsyncWorkScheduler
from supercrawler.common.logging.logger import get_logger
from supercrawler.crawler.explore_url_operation_factory import ExploreUrlOperationFactory
from supercrawler.crawler.sub_domain_explorer import SubDomainExplorer
from supercrawler.web.scraper import Scraper


logger = get_logger(__name__)


def explore_domain(url: str, max_concurrency = 10) -> None:
    logger.info("Starting crawl for %s", url)
    return asyncio.run(explore_domain_async(url, max_concurrency))


async def explore_domain_async(url: str, max_concurrency = 10) -> None:
    sub_domain_explorer = SubDomainExplorer(
        url,
        BoundedAsyncWorkScheduler(max_concurrency),
        Scraper(),
        ExploreUrlOperationFactory(
            should_retry=lambda error: isinstance(error, ConnectTimeout)
            or isinstance(error, ReadTimeout)
            or isinstance(error, TimeoutError),
            retries=5,
        ))
    logger.info("Starting crawl for %s", url)
    return await sub_domain_explorer.explore()