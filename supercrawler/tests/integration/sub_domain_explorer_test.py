from __future__ import annotations

from supercrawler.main import explore_domain

def test_exploring__charlie_howlett_site_explores_site() -> None:
    url = "https://charliehowlett.co.uk/"

    results = explore_domain(url, max_concurrency = 10)

    assert len(results) == 1
    assert results[0].status == "success"

def test_exploring__example_site_explores_site() -> None:
    url = "https://example.com"

    results = explore_domain(url, max_concurrency = 10)

    assert len(results) == 1
    assert results[0].status == "success"

# def test_exploring_monzo_site_explores_site() -> None:
#     explorer = SubDomainExplorer("https://crawlme.monzo.com/")

#     results = explorer.explore()

#     assert len(results) == 42011
