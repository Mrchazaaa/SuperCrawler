from __future__ import annotations

import asyncio

import pytest

from supercrawler.common.operation import Operation
from supercrawler.common.retryable_operation import RetryableOperation

class SuccessfulOperation(Operation[str]):
    def __init__(self) -> None:
        self.completed_states: list[str] = []

    async def execute(self, state: str) -> None:
        self.completed_states.append(state)


class FlakyOperation(Operation[str]):
    def __init__(self, failures_before_success: int) -> None:
        self.failures_before_success = failures_before_success
        self.attempts = 0
        self.completed_states: list[str] = []

    async def execute(self, state: str) -> None:
        self.attempts += 1

        if self.attempts <= self.failures_before_success:
            raise RuntimeError("temporary failure")

        self.completed_states.append(state)


class ValueErrorOperation(Operation[str]):
    def __init__(self) -> None:
        self.attempts = 0

    async def execute(self, state: str) -> None:
        self.attempts += 1
        raise ValueError(f"invalid input: {state}")


def test_execute_returns_result_when_operation_succeeds() -> None:
    successful_operation = SuccessfulOperation()
    operation = RetryableOperation(
        operation=successful_operation,
        should_retry=lambda error: True,
        retries=3,
    )

    asyncio.run(operation.execute("work"))

    assert successful_operation.completed_states == ["work"]


def test_execute_retries_until_operation_succeeds() -> None:
    flaky_operation = FlakyOperation(failures_before_success=2)

    operation = RetryableOperation(
        operation=flaky_operation,
        should_retry=lambda error: isinstance(error, RuntimeError),
        retries=2,
    )

    asyncio.run(operation.execute("work"))

    assert flaky_operation.attempts == 3
    assert flaky_operation.completed_states == ["work"]


def test_execute_raises_immediately_when_error_is_not_retryable() -> None:
    failing_operation = ValueErrorOperation()

    operation = RetryableOperation(
        operation=failing_operation,
        should_retry=lambda error: isinstance(error, RuntimeError),
        retries=3,
    )

    with pytest.raises(ValueError, match="invalid input: work"):
        asyncio.run(operation.execute("work"))

    assert failing_operation.attempts == 1


def test_execute_raises_after_retry_limit_is_exhausted() -> None:
    failing_operation = FlakyOperation(failures_before_success=3)

    operation = RetryableOperation(
        operation=failing_operation,
        should_retry=lambda error: isinstance(error, RuntimeError),
        retries=2,
    )

    with pytest.raises(RuntimeError, match="temporary failure"):
        asyncio.run(operation.execute("work"))

    assert failing_operation.attempts == 3


def test_constructor_rejects_negative_retry_count() -> None:
    with pytest.raises(ValueError, match="retries must be greater than or equal to 0"):
        RetryableOperation(
            operation=SuccessfulOperation(),
            should_retry=lambda error: True,
            retries=-1,
        )
