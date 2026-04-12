from __future__ import annotations

import pytest

from supercrawler.model.page_content import PageContent

from supercrawler.crawler.sub_domain_explorer import SubDomainExplorer


class UnexpectedRecursionError(AssertionError):
    pass

class FakeScraper:
    def __init__(self, pages_by_url: dict[str, PageContent], max_calls: int | None = None):
        self.pages_by_url = pages_by_url
        self.calls = 0
        self.max_calls = max_calls
        self.requested_urls: list[str] = []

    def fetch_html(self, url: str) -> PageContent:
        self.calls += 1
        self.requested_urls.append(url)

        if self.max_calls is not None and self.calls > self.max_calls:
            raise UnexpectedRecursionError(
                f"fetch_html called {self.calls} times for {url}"
            )

        try:
            return self.pages_by_url[url]
        except KeyError as exc:
            raise AssertionError(f"Unexpected URL fetched: {url}") from exc


def test_explore_does_not_revisit_page_when_it_links_to_itself() -> None:
    dummy_url = "https://example.com"
    dummy_page_content = PageContent([dummy_url])
    scraper = FakeScraper({dummy_url: dummy_page_content}, max_calls=1)
    explorer = SubDomainExplorer(dummy_url, scraper=scraper)

    results = explorer.explore()

    assert len(results) == 1
    assert results[0].content == dummy_page_content
    assert results[0].url == dummy_url
    assert scraper.calls == 1


def test_explore_ignores_links_outside_starting_subdomain() -> None:
    start_url = "https://crawlme.monzo.com"
    scraper = FakeScraper(
        {
            start_url: PageContent(
                [
                    "https://crawlme.monzo.com/about",
                    "https://monzo.com",
                    "https://www.monzo.com/help",
                ]
            ),
            "https://crawlme.monzo.com/about": PageContent([]),
        }
    )

    results = SubDomainExplorer(start_url, scraper=scraper).explore()

    assert [page.url for page in results] == [
        start_url,
        "https://crawlme.monzo.com/about",
    ]
    assert scraper.requested_urls == [
        start_url,
        "https://crawlme.monzo.com/about",
    ]


def test_explore_normalizes_relative_links_against_current_page() -> None:
    start_url = "https://example.com/root"
    child_url = "https://example.com/child"
    scraper = FakeScraper(
        {
            start_url: PageContent(["/child"]),
            child_url: PageContent([]),
        }
    )

    results = SubDomainExplorer(start_url, scraper=scraper).explore()

    assert [page.url for page in results] == [start_url, child_url]
    assert scraper.requested_urls == [start_url, child_url]


def test_explore_returns_cached_results_on_second_call() -> None:
    start_url = "https://example.com"
    scraper = FakeScraper({start_url: PageContent([])})
    explorer = SubDomainExplorer(start_url, scraper=scraper)

    first_results = explorer.explore()
    second_results = explorer.explore()

    assert first_results is second_results
    assert scraper.calls == 1


def test_explore_surfaces_scraper_errors() -> None:
    start_url = "https://example.com"

    class FailingScraper:
        def fetch_html(self, url: str) -> PageContent:
            raise RuntimeError("boom")

    explorer = SubDomainExplorer(start_url, scraper=FailingScraper())

    with pytest.raises(RuntimeError, match="boom"):
        explorer.explore()
