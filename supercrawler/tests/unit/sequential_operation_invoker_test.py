from __future__ import annotations

import pytest

from supercrawler.common import Operation, SequentialOperationInvoker


class AppendOperation(Operation[str]):
    def __init__(self, execution_log: list[str]) -> None:
        self._execution_log = execution_log

    def execute(self, state: str) -> None:
        self._execution_log.append(f"operation:{state}")


class SchedulingOperation(Operation[str]):
    def __init__(self, execution_log: list[str], invoker: SequentialOperationInvoker) -> None:
        self._execution_log = execution_log
        self._invoker = invoker

    def execute(self, state: str) -> None:
        self._execution_log.append(f"operation:{state}")
        self._invoker.ScheduleOperation(
            operation=AppendOperation(self._execution_log),
            state="third",
        )


class FailingOperation(Operation[str]):
    def execute(self, state: str) -> None:
        raise RuntimeError(f"failed:{state}")


def test_execute_operations_runs_scheduled_operations_sequentially() -> None:
    execution_log: list[str] = []
    invoker = SequentialOperationInvoker()

    invoker.ScheduleOperation(
        operation=AppendOperation(execution_log),
        state="first",
    )
    invoker.ScheduleOperation(
        operation=AppendOperation(execution_log),
        state="second",
    )

    invoker.ExecuteOperations()

    assert execution_log == [
        "operation:first",
        "operation:second",
    ]


def test_execute_operations_continues_with_operations_scheduled_during_execution() -> None:
    execution_log: list[str] = []
    invoker = SequentialOperationInvoker()

    invoker.ScheduleOperation(
        operation=SchedulingOperation(execution_log, invoker),
        state="first",
    )
    invoker.ScheduleOperation(
        operation=AppendOperation(execution_log),
        state="second",
    )

    invoker.ExecuteOperations()

    assert execution_log == [
        "operation:first",
        "operation:second",
        "operation:third",
    ]


def test_execute_operations_surfaces_errors_and_stops_execution() -> None:
    execution_log: list[str] = []
    invoker = SequentialOperationInvoker()

    invoker.ScheduleOperation(
        operation=FailingOperation(),
        state="first",
    )
    invoker.ScheduleOperation(
        operation=AppendOperation(execution_log),
        state="second",
    )

    with pytest.raises(RuntimeError, match="failed:first"):
        invoker.ExecuteOperations()

    assert execution_log == []
