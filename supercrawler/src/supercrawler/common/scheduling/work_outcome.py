from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, TypeVar


TResult = TypeVar("TResult")


@dataclass(frozen=True)
class WorkOutcome(Generic[TResult]):
    value: TResult | None = None
    error: BaseException | None = None
    succeeded: bool = False

    def __post_init__(self) -> None:
        if self.succeeded and self.error is not None:
            raise ValueError("Successful outcomes cannot include an error")

        if not self.succeeded and self.error is None:
            raise ValueError("Failed outcomes must include an error")
