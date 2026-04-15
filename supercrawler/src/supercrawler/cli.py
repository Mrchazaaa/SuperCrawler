from __future__ import annotations

import asyncio
import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from supercrawler.common.bounded_async_work_scheduler import BoundedAsyncWorkScheduler
from supercrawler.common.logger import configure_logging, get_logger
from supercrawler.crawler.sub_domain_explorer import SubDomainExplorer
from supercrawler.model.page import Page
from supercrawler.model.page_content import PageContent
from supercrawler.model.page_exploration_result import PageExplorationResult
from supercrawler.web.scraper import Scraper


logger = get_logger(__name__)


def _positive_int(value: str) -> int:
    parsed_value = int(value)
    if parsed_value < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")

    return parsed_value


def _serialize_page_content(content: PageContent) -> dict[str, object]:
    return {
        "links": content.links,
    }


def _serialize_result(result: PageExplorationResult) -> dict[str, object]:
    return {
        "url": result.url,
        "status": result.status,
        "page_content": _serialize_page_content(result.page.content) if result.page is not None else None,
        "error": result.error,
    }


def _serialize_config(args: argparse.Namespace) -> dict[str, object]:
    return {
        "url": args.url,
        "debug": args.debug,
        "persist_logs": args.persist_logs,
        "max_concurrency": args.max_concurrency,
    }


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
    parser.add_argument(
        "--max-concurrency",
        type=_positive_int,
        default=10,
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    started_at_timestamp = datetime.now().astimezone().isoformat()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    project_root = Path(__file__).resolve().parents[2]
    log_path = project_root / "Logs" / f"supercrawler-{timestamp}.logs"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    configure_logging(
        level=logging.DEBUG if args.debug else logging.INFO,
        logs_filepath=log_path)

    url = args.url
    sub_domain_explorer = SubDomainExplorer(url, BoundedAsyncWorkScheduler(args.max_concurrency), Scraper())
    started_at = time.perf_counter()

    try:
        logger.info("Starting crawl for %s", url)
        results = asyncio.run(sub_domain_explorer.explore())
        duration = time.perf_counter() - started_at
        print(
            json.dumps(
                {
                    "configuration": _serialize_config(args),
                    "started_at": started_at_timestamp,
                    "logs_filepath": str(log_path),
                    "duration_seconds": duration,
                    "results": [_serialize_result(result) for result in results],
                }
            )
        )
    except Exception as e:
        logger.error_with_exception("Crawl failed", e)
        sys.exit(1)
