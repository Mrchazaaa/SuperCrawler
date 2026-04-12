from __future__ import annotations

from datetime import datetime
import logging
from pathlib import Path


class SuperCrawlerLogger:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def debug(self, msg: str, *args: object, **kwargs: object) -> None:
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg: str, *args: object, **kwargs: object) -> None:
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args: object, **kwargs: object) -> None:
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg: str, *args: object, **kwargs: object) -> None:
        self._logger.error(msg, *args, **kwargs)

    def error_with_exception(self, msg: str, error: BaseException) -> None:
        self._logger.error(
            "%s: %s: %s",
            msg,
            type(error).__name__,
            error,
            exc_info=(type(error), error, error.__traceback__),
        )


def configure_logging(level: int = logging.INFO, save_logs_to_file: bool | None = False) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if save_logs_to_file:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        project_root = Path(__file__).resolve().parents[3]
        log_path = project_root / "Logs" / f"supercrawler-{timestamp}.logs"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path))

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )


def get_logger(name: str) -> SuperCrawlerLogger:
    return SuperCrawlerLogger(logging.getLogger(name))
