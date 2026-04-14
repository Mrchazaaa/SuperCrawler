from __future__ import annotations

import asyncio

from supercrawler.common.bounded_async_work_scheduler import BoundedAsyncWorkScheduler


def test_wait_for_all_continues_with_work_scheduled_during_execution() -> None:
    async def run_test() -> None:
        execution_log: list[str] = []
        scheduler = BoundedAsyncWorkScheduler[str](max_concurrency=1)

        async def third_work() -> str:
            execution_log.append("work:third")
            return "third"

        async def first_work() -> str:
            execution_log.append("work:first")
            await scheduler.schedule(third_work, work_id="third")
            return "first"

        async def second_work() -> str:
            execution_log.append("work:second")
            return "second"

        first_work_id = await scheduler.schedule(first_work, work_id="first")
        second_work_id = await scheduler.schedule(second_work, work_id="second")

        outcomes_by_id = await scheduler.execute()

        assert execution_log == [
            "work:first",
            "work:second",
            "work:third",
        ]
        assert outcomes_by_id[first_work_id].value == "first"
        assert outcomes_by_id[second_work_id].value == "second"
        assert outcomes_by_id["third"].value == "third"

    asyncio.run(run_test())


def test_wait_for_all_runs_up_to_configured_parallelism() -> None:
    async def run_test() -> None:
        active_counts: list[int] = []
        state_by_task: dict[str, str] = {}
        lock = asyncio.Lock()
        started_event = asyncio.Event()
        release_event = asyncio.Event()
        scheduler = BoundedAsyncWorkScheduler[str](max_concurrency=2)

        async def blocking_work(state: str) -> str:
            task_id = id(asyncio.current_task())

            async with lock:
                state_by_task[str(task_id)] = state
                active_counts.append(len(state_by_task))
                if len(state_by_task) == 2:
                    started_event.set()

            await asyncio.wait_for(release_event.wait(), timeout=1)

            async with lock:
                state_by_task.pop(str(task_id), None)

            return state

        await scheduler.schedule(lambda: blocking_work("first"), work_id="first")
        await scheduler.schedule(lambda: blocking_work("second"), work_id="second")
        await scheduler.schedule(lambda: blocking_work("third"), work_id="third")

        wait_task = asyncio.create_task(scheduler.execute())

        await asyncio.wait_for(started_event.wait(), timeout=1)

        async with lock:
            assert len(state_by_task) == 2
            assert sorted(state_by_task.values()) == ["first", "second"]
            assert max(active_counts) == 2

        release_event.set()
        await asyncio.wait_for(wait_task, timeout=1)

    asyncio.run(run_test())


def test_wait_for_all_records_errors_without_raising() -> None:
    async def run_test() -> None:
        scheduler = BoundedAsyncWorkScheduler[str](max_concurrency=1)

        async def failing_work() -> str:
            raise RuntimeError("failed:first")

        work_id = await scheduler.schedule(failing_work, work_id="first")

        outcomes_by_id = await scheduler.execute()

        assert outcomes_by_id[work_id].value is None
        assert isinstance(outcomes_by_id[work_id].error, RuntimeError)
        assert str(outcomes_by_id[work_id].error) == "failed:first"

    asyncio.run(run_test())

def test_wait_for_all_returns_same_result_when_already_running() -> None:
    async def run_test() -> None:
        scheduler = BoundedAsyncWorkScheduler[str](max_concurrency=1)
        release_event = asyncio.Event()

        async def blocking_work() -> str:
            await asyncio.wait_for(release_event.wait(), timeout=1)
            return "done"

        await scheduler.schedule(blocking_work, work_id="first")

        first_wait_task = asyncio.create_task(scheduler.execute())

        await asyncio.sleep(0)

        second_wait_task = asyncio.create_task(scheduler.execute())

        release_event.set()
        first_result, second_result = await asyncio.wait_for(
            asyncio.gather(first_wait_task, second_wait_task),
            timeout=1,
        )

        assert first_result == second_result
        assert first_result["first"].value == "done"

    asyncio.run(run_test())
