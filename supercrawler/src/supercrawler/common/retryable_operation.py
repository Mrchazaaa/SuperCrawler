from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar

from supercrawler.common.logging.logger import get_logger
from supercrawler.common.operation import Operation


TState = TypeVar("TState")
logger = get_logger(__name__)


class RetryableOperation(Operation[TState]):
    def __init__(
        self,
        operation: Operation[TState],
        should_retry: Callable[[BaseException], bool],
        retries: int,
    ) -> None:
        if retries < 0:
            raise ValueError("retries must be greater than or equal to 0")

        self._operation = operation
        self._should_retry = should_retry
        self._retries = retries

    async def execute(self, state: TState) -> Any:
        attempts_remaining = self._retries
        attempt_number = 1

        while True:
            try:
                logger.debug(
                    "Executing retryable operation %s attempt %s",
                    type(self._operation).__name__,
                    attempt_number,
                )
                result = await self._operation.execute(state)
                logger.debug(
                    "Retryable operation %s succeeded on attempt %s",
                    type(self._operation).__name__,
                    attempt_number,
                )
                return result
            except BaseException as error:
                should_retry = attempts_remaining > 0 and self._should_retry(error)

                if not should_retry:
                    logger.warning(
                        "Retryable operation %s failed on attempt %s and will not be retried: %s: %s",
                        type(self._operation).__name__,
                        attempt_number,
                        type(error).__name__,
                        error,
                    )
                    raise

                logger.warning(
                    "Retryable operation %s failed on attempt %s and will be retried (%s retries remaining): %s: %s",
                    type(self._operation).__name__,
                    attempt_number,
                    attempts_remaining,
                    type(error).__name__,
                    error,
                )
                attempts_remaining -= 1
                attempt_number += 1
