from __future__ import annotations

import asyncio
from pathlib import Path

from supercrawler.crawler.sub_domain_explorer import SubDomainExplorer

def test_exploring__charlie_howlett_site_explores_site() -> None:
    explorer = SubDomainExplorer("https://charliehowlett.co.uk/")

    results = asyncio.run(explorer.explore())

    assert len(results) == 1
    assert results[0].status == "success"

def test_exploring__example_site_explores_site() -> None:
    explorer = SubDomainExplorer("https://example.com")

    results = asyncio.run(explorer.explore())

    assert len(results) == 1
    assert results[0].status == "success"

# def test_exploring_monzo_site_explores_site() -> None:
#     explorer = SubDomainExplorer("https://crawlme.monzo.com/")

#     results = explorer.explore()

#     assert len(results) == 42011
