from __future__ import annotations

from dataclasses import dataclass


@dataclass
class OperationResult:
    result: object | BaseException | None
