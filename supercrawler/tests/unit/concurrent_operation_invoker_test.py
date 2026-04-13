from __future__ import annotations

import threading

import pytest

from supercrawler.common import (
    ConcurrentOperationInvoker,
    Operation,
    OperationAlreadyTrackedError,
    OperationId,
    OperationState,
)


class AppendOperation(Operation[str]):
    def __init__(self, execution_log: list[str]) -> None:
        self._execution_log = execution_log

    def execute(self, state: str) -> None:
        self._execution_log.append(f"operation:{state}")


class SchedulingOperation(Operation[str]):
    def __init__(self, execution_log: list[str], invoker: ConcurrentOperationInvoker) -> None:
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


class BlockingOperation(Operation[str]):
    def __init__(
        self,
        active_counts: list[int],
        state_by_thread: dict[str, str],
        lock: threading.Lock,
        started_event: threading.Event,
        release_event: threading.Event,
    ) -> None:
        self._active_counts = active_counts
        self._state_by_thread = state_by_thread
        self._lock = lock
        self._started_event = started_event
        self._release_event = release_event

    def execute(self, state: str) -> None:
        thread_name = threading.current_thread().name

        with self._lock:
            self._state_by_thread[thread_name] = state
            self._active_counts.append(len(self._state_by_thread))
            if len(self._state_by_thread) == 2:
                self._started_event.set()

        self._release_event.wait(timeout=1)

        with self._lock:
            self._state_by_thread.pop(thread_name, None)


class SignallingOperation(Operation[str]):
    def __init__(self, running_event: threading.Event, release_event: threading.Event) -> None:
        self._running_event = running_event
        self._release_event = release_event

    def execute(self, state: str) -> None:
        self._running_event.set()
        self._release_event.wait(timeout=1)


def test_execute_operations_continues_with_operations_scheduled_during_execution() -> None:
    execution_log: list[str] = []
    invoker = ConcurrentOperationInvoker(level_of_parallelism=1)

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
    invoker = ConcurrentOperationInvoker(level_of_parallelism=1)

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


def test_execute_operations_runs_up_to_configured_parallelism() -> None:
    active_counts: list[int] = []
    state_by_thread: dict[str, str] = {}
    lock = threading.Lock()
    started_event = threading.Event()
    release_event = threading.Event()
    invoker = ConcurrentOperationInvoker(level_of_parallelism=2)

    blocking_operation = BlockingOperation(
        active_counts=active_counts,
        state_by_thread=state_by_thread,
        lock=lock,
        started_event=started_event,
        release_event=release_event,
    )

    invoker.ScheduleOperation(operation=blocking_operation, state="first")
    invoker.ScheduleOperation(operation=blocking_operation, state="second")
    invoker.ScheduleOperation(operation=blocking_operation, state="third")

    execute_thread = threading.Thread(target=invoker.ExecuteOperations)
    execute_thread.start()

    assert started_event.wait(timeout=1)

    with lock:
        assert len(state_by_thread) == 2
        assert sorted(state_by_thread.values()) == ["first", "second"]
        assert max(active_counts) == 2

    release_event.set()
    execute_thread.join(timeout=1)

    assert not execute_thread.is_alive()


def test_schedule_operation_tracks_queued_running_and_complete_states() -> None:
    running_event = threading.Event()
    release_event = threading.Event()
    invoker = ConcurrentOperationInvoker(level_of_parallelism=1)

    operation_id = invoker.ScheduleOperation(
        operation=SignallingOperation(running_event, release_event),
        state="first",
    )

    assert invoker.operation_progress_by_id[operation_id].state is OperationState.QUED
    assert invoker.operation_progress_by_id[operation_id].result is None

    execute_thread = threading.Thread(target=invoker.ExecuteOperations)
    execute_thread.start()

    assert running_event.wait(timeout=1)
    assert invoker.operation_progress_by_id[operation_id].state is OperationState.RUNNING
    assert invoker.operation_progress_by_id[operation_id].result is None

    release_event.set()
    execute_thread.join(timeout=1)

    assert not execute_thread.is_alive()
    assert invoker.operation_progress_by_id[operation_id].state is OperationState.COMPLETE
    assert invoker.operation_progress_by_id[operation_id].result is None


def test_execute_operations_records_failure_result() -> None:
    invoker = ConcurrentOperationInvoker(level_of_parallelism=1)
    operation_id = invoker.ScheduleOperation(
        operation=FailingOperation(),
        state="first",
    )

    with pytest.raises(RuntimeError, match="failed:first"):
        invoker.ExecuteOperations()

    progress_state = invoker.operation_progress_by_id[operation_id]
    assert progress_state.state is OperationState.COMPLETE
    assert isinstance(progress_state.result, RuntimeError)
    assert str(progress_state.result) == "failed:first"


def test_schedule_operation_raises_when_operation_id_is_already_tracked() -> None:
    invoker = ConcurrentOperationInvoker(level_of_parallelism=1)
    operation_id = OperationId("duplicate-id")

    invoker.ScheduleOperation(
        operation=AppendOperation([]),
        state="first",
        operation_id=operation_id,
    )

    with pytest.raises(OperationAlreadyTrackedError, match="duplicate-id"):
        invoker.ScheduleOperation(
            operation=AppendOperation([]),
            state="second",
            operation_id=operation_id,
        )


def test_constructor_rejects_non_positive_parallelism() -> None:
    with pytest.raises(ValueError, match="level_of_parallelism must be greater than 0"):
        ConcurrentOperationInvoker(level_of_parallelism=0)
