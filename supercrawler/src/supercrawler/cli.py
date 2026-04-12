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
        action="store_true"
    )
    parser.add_argument(
        "--persist-logs",
        action="store_true"
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    configure_logging(
        level=logging.DEBUG if args.debug else logging.INFO,
        save_logs_to_file=True if args.persist_logs else False)

    url = args.url
    sub_domain_explorer = SubDomainExplorer(url)

    try:
        logger.info("Starting crawl for %s", url)
        results = sub_domain_explorer.explore()
        for page in results:
            print(page.url)
    except Exception as e:
        logger.error_with_exception("Crawl failed", e)
        sys.exit(1)
