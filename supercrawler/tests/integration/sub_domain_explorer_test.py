from __future__ import annotations

from pathlib import Path

from supercrawler.crawler.sub_domain_explorer import SubDomainExplorer

def test_exploring__example_site_explores_site() -> None:
    explorer = SubDomainExplorer("https://example.com")

    results = explorer.explore()

    assert len(results) == 1

# def test_exploring_monzo_site_explores_site() -> None:
#     explorer = SubDomainExplorer("https://crawlme.monzo.com/")

#     results = explorer.explore()

#     assert len(results) == 1