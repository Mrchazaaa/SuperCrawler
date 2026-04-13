from __future__ import annotations

from collections import deque
from threading import Condition, Thread
from typing import Any
from uuid import uuid4

from supercrawler.common.operation_already_tracked_error import OperationAlreadyTrackedError
from supercrawler.common.operation_id import OperationId
from supercrawler.common.operation import Operation
from supercrawler.common.operation_invoker import OperationInvoker
from supercrawler.common.operation_progress_state import OperationProgressState, OperationState


class ConcurrentOperationInvoker(OperationInvoker):
    def __init__(self, level_of_parallelism: int) -> None:
        if level_of_parallelism <= 0:
            raise ValueError("level_of_parallelism must be greater than 0")

        self._level_of_parallelism = level_of_parallelism
        self._scheduled_operations: deque[tuple[OperationId, Operation[Any], Any]] = deque()
        self._condition = Condition()
        self._in_flight_operations = 0
        self._is_executing = False
        self._execution_failed = False
        self._first_error: BaseException | None = None
        self.operation_progress_by_id: dict[OperationId, OperationProgressState] = {}

    def ScheduleOperation(
        self,
        operation: Operation[Any],
        state: Any,
        operation_id: OperationId | None = None,
    ) -> OperationId:
        resolved_operation_id = operation_id or OperationId(str(uuid4()))

        with self._condition:
            if resolved_operation_id in self.operation_progress_by_id:
                raise OperationAlreadyTrackedError(resolved_operation_id)

            self._scheduled_operations.append((resolved_operation_id, operation, state))
            self.operation_progress_by_id[resolved_operation_id] = OperationProgressState(
                state=OperationState.QUED,
                result=None,
            )
            self._condition.notify()

        return resolved_operation_id

    def ExecuteOperations(self) -> None:
        with self._condition:
            if self._is_executing:
                raise RuntimeError("ExecuteOperations is already running")

            self._is_executing = True
            self._execution_failed = False
            self._first_error = None

        workers = [
            Thread(target=self._execute_scheduled_operations, daemon=True)
            for _ in range(self._level_of_parallelism)
        ]

        for worker in workers:
            worker.start()

        for worker in workers:
            worker.join()

        with self._condition:
            self._is_executing = False
            first_error = self._first_error
            self._first_error = None
            self._execution_failed = False

        if first_error is not None:
            raise first_error

    def _execute_scheduled_operations(self) -> None:
        while True:
            with self._condition:
                while not self._scheduled_operations:
                    if self._execution_failed:
                        return

                    if self._in_flight_operations == 0:
                        return

                    self._condition.wait()

                operation_id, operation, state = self._scheduled_operations.popleft()
                self._in_flight_operations += 1
                self.operation_progress_by_id[operation_id] = OperationProgressState(
                    state=OperationState.RUNNING,
                    result=None,
                )

            try:
                operation.execute(state)
                with self._condition:
                    self.operation_progress_by_id[operation_id] = OperationProgressState(
                        state=OperationState.COMPLETE,
                        result=None,
                    )
            except BaseException as error:
                with self._condition:
                    self.operation_progress_by_id[operation_id] = OperationProgressState(
                        state=OperationState.COMPLETE,
                        result=error,
                    )
                    if self._first_error is None:
                        self._first_error = error
                        self._execution_failed = True
                        self._scheduled_operations.clear()
                    self._condition.notify_all()
            finally:
                with self._condition:
                    self._in_flight_operations -= 1
                    if self._in_flight_operations == 0:
                        self._condition.notify_all()
