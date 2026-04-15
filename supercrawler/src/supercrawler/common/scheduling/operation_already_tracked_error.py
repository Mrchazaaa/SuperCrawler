from __future__ import annotations

from supercrawler.common.scheduling.work_id import WorkId


class OperationAlreadyTrackedError(Exception):
    def __init__(self, work_id: WorkId) -> None:
        super().__init__(f"Work with id '{work_id}' has already been scheduled")
        self.work_id = work_id
