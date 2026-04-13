from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Generic, TypeVar


TState = TypeVar("TState")


class Operation(ABC, Generic[TState]):
    @abstractmethod
    def execute(self, state: TState) -> None:
        raise NotImplementedError
