from dataclasses import dataclass


@dataclass(frozen=True)
class PageId:
    value: str
