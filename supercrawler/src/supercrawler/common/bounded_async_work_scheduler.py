from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar
from uuid import uuid4

from supercrawler.common.async_work_scheduler_interface import AsyncWorkSchedulerInterface
from supercrawler.common.work_id import WorkId
from supercrawler.common.work_outcome import WorkOutcome


TResult = TypeVar("TResult")


class BoundedAsyncWorkScheduler(AsyncWorkSchedulerInterface[TResult], Generic[TResult]):
    def __init__(self, max_concurrency: int) -> None:
        self._max_concurrency = max_concurrency
        self._queue: asyncio.Queue[tuple[WorkId, Callable[[], Awaitable[TResult]]] | None] = asyncio.Queue()
        self._lock = asyncio.Lock()
        self._results_by_id: dict[WorkId, WorkOutcome[TResult]] = {}
        self._wait_task: asyncio.Task[dict[WorkId, WorkOutcome[TResult]]] | None = None

    async def schedule(
        self,
        work: Callable[[], Awaitable[TResult]],
        work_id: WorkId | None = None,
    ) -> WorkId:
        resolved_work_id = work_id or str(uuid4())
        await self._queue.put((resolved_work_id, work))
        return resolved_work_id

    async def execute(self) -> dict[WorkId, WorkOutcome[TResult]]:
        async with self._lock:
            if self._wait_task is None:
                self._results_by_id = {}
                self._wait_task = asyncio.create_task(self._wait_for_all())

        result = await self._wait_task
        self._wait_task = None
        return result

    async def _wait_for_all(self) -> dict[WorkId, WorkOutcome[TResult]]:
        workers = [
            asyncio.create_task(self._worker())
            for _ in range(self._max_concurrency)
        ]

        try:
            await self._queue.join()
            return dict(self._results_by_id)
        finally:
            for _ in workers:
                await self._queue.put(None)

            await asyncio.gather(*workers)

    async def _worker(self) -> None:
        while True:
            queue_item = await self._queue.get()

            try:
                if queue_item is None:
                    return

                work_id, work = queue_item

                try:
                    value = await work()
                    outcome = WorkOutcome(value=value, succeeded=True)
                except BaseException as error:
                    outcome = WorkOutcome(error=error)

                async with self._lock:
                    self._results_by_id[work_id] = outcome
            finally:
                self._queue.task_done()
