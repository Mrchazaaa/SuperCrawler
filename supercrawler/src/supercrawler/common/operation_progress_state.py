from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OperationState(Enum):
    QUED = "Qued"
    RUNNING = "Running"
    COMPLETE = "Complete"


@dataclass
class OperationProgressState:
    state: OperationState
    result: object | None
