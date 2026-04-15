from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from supercrawler.common.logging.logger import configure_logging, get_logger
from supercrawler.crawl_output_serializer import serialize_configuration, serialize_crawl_output
from supercrawler import explore_domain


logger = get_logger(__name__)


def _positive_int(value: str) -> int:
    parsed_value = int(value)
    if parsed_value < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")

    return parsed_value


def _log_level(value: str) -> str:
    normalized_value = value.upper()
    valid_levels = logging.getLevelNamesMapping()

    if normalized_value not in valid_levels:
        raise argparse.ArgumentTypeError(
            f"must be one of: {', '.join(valid_levels)}"
        )

    return normalized_value

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="supercrawler")
    parser.add_argument("url")
    parser.add_argument(
        "--log-level",
        type=_log_level,
        default="ERROR",
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
        level=logging.getLevelNamesMapping()[args.log_level],
        logs_filepath=log_path)

    url = args.url
    started_at = time.perf_counter()

    try:
        logger.info("Starting crawl for %s", url)
        results = explore_domain(url, args.max_concurrency)
        duration = time.perf_counter() - started_at
        print(
            json.dumps(
                serialize_crawl_output(
                    configuration=serialize_configuration(
                        url=args.url,
                        log_level=args.log_level,
                        persist_logs=args.persist_logs,
                        max_concurrency=args.max_concurrency,
                    ),
                    started_at=started_at_timestamp,
                    logs_filepath=str(log_path),
                    duration_seconds=duration,
                    results=results,
                )
            )
        )
    except Exception as e:
        logger.error_with_exception("Crawl failed", e)
        sys.exit(1)
