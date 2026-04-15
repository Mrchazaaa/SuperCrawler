from __future__ import annotations

import logging

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


def configure_logging(level: int = logging.INFO, logs_filepath: str | None = None) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if logs_filepath is not None:
        handlers.append(logging.FileHandler(logs_filepath))

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )


def get_logger(name: str) -> SuperCrawlerLogger:
    return SuperCrawlerLogger(logging.getLogger(name))
