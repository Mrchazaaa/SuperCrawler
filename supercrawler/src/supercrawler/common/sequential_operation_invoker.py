from __future__ import annotations

from collections import deque
from typing import Any

from supercrawler.common.operation import Operation
from supercrawler.common.operation_id import OperationId
from supercrawler.common.operation_invoker import OperationInvoker


class SequentialOperationInvoker(OperationInvoker):
    def __init__(self) -> None:
        self._scheduled_operations: deque[tuple[Operation[Any], Any]] = deque()

    def ScheduleOperation(
        self,
        operation: Operation[Any],
        state: Any,
        operation_id: OperationId | None = None,
    ) -> OperationId | None:
        self._scheduled_operations.append((operation, state))
        return None

    def ExecuteOperations(self) -> None:
        while self._scheduled_operations:
            operation, state = self._scheduled_operations.popleft()
            operation.execute(state)
