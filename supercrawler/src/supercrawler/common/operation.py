from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar


TState = TypeVar("TState")


class Operation(ABC, Generic[TState]):
    @abstractmethod
    async def execute(self, state: TState) -> Any:
        raise NotImplementedError
