from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar

from supercrawler.common.scheduling.work_id import WorkId
from supercrawler.common.scheduling.work_outcome import WorkOutcome


TResult = TypeVar("TResult")


class AsyncWorkSchedulerInterface(ABC, Generic[TResult]):
    @abstractmethod
    async def schedule(
        self,
        work: Callable[[], Awaitable[TResult]],
        work_id: WorkId | None = None,
    ) -> WorkId:
        raise NotImplementedError

    @abstractmethod
    async def execute(self) -> dict[WorkId, WorkOutcome[TResult]]:
        raise NotImplementedError
