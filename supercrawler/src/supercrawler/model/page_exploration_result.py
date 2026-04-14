from __future__ import annotations

from dataclasses import dataclass

from supercrawler.model.page import Page


@dataclass
class PageExplorationResult:
    url: str
    status: str
    page: Page | None = None
    error: str | None = None
