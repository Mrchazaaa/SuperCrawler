from __future__ import annotations

import argparse
import logging
import sys

from supercrawler.common.logger import configure_logging, get_logger
from supercrawler.crawler.sub_domain_explorer import SubDomainExplorer


logger = get_logger(__name__)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="supercrawler")
    parser.add_argument("url")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging.",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    configure_logging(level=logging.DEBUG if args.debug else logging.INFO)

    url = args.url
    sub_domain_explorer = SubDomainExplorer(url)

    try:
        logger.info("Starting crawl for %s", url)
        results = sub_domain_explorer.explore()
        for page in results:
            print(page.url)
    except Exception as e:
        logger.error("Crawl failed: %s", e)
        sys.exit(1)
