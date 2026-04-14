from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from supercrawler.common.operation import Operation
from supercrawler.common.operation_id import OperationId


class OperationInvoker(ABC):
    @abstractmethod
    async def ScheduleOperation(
        self,
        operation: Operation[Any],
        state: Any,
        operation_id: OperationId | None = None,
    ) -> OperationId | None:
        raise NotImplementedError

    @abstractmethod
    async def ExecuteOperations(self) -> None:
        raise NotImplementedError
