from __future__ import annotations

from supercrawler.common.operation_id import OperationId


class OperationAlreadyTrackedError(ValueError):
    def __init__(self, operation_id: OperationId) -> None:
        super().__init__(f"Operation id is already being tracked: {operation_id.id}")
        self.operation_id = operation_id
