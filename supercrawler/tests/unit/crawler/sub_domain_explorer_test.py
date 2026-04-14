from __future__ import annotations

import asyncio

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

    async def fetch_html(self, url: str) -> PageContent:
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

    results = asyncio.run(explorer.explore())

    assert len(results) == 1
    assert results[0].url == dummy_url
    assert results[0].status == "success"
    assert results[0].page is not None
    assert results[0].page.content == dummy_page_content
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

    results = asyncio.run(SubDomainExplorer(start_url, scraper=scraper).explore())

    assert [result.url for result in results] == [
        start_url,
        "https://crawlme.monzo.com/about",
    ]
    assert all(result.status == "success" for result in results)
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

    results = asyncio.run(SubDomainExplorer(start_url, scraper=scraper).explore())

    assert [result.url for result in results] == [start_url, child_url]
    assert all(result.status == "success" for result in results)
    assert scraper.requested_urls == [start_url, child_url]


def test_explore_does_not_schedule_same_child_url_twice() -> None:
    start_url = "https://example.com"
    first_child_url = "https://example.com/first"
    second_child_url = "https://example.com/second"
    shared_child_url = "https://example.com/shared"
    scraper = FakeScraper(
        {
            start_url: PageContent([first_child_url, second_child_url]),
            first_child_url: PageContent([shared_child_url]),
            second_child_url: PageContent([shared_child_url]),
            shared_child_url: PageContent([]),
        }
    )

    results = asyncio.run(SubDomainExplorer(start_url, scraper=scraper).explore())

    assert [result.url for result in results] == [
        start_url,
        first_child_url,
        second_child_url,
        shared_child_url,
    ]
    assert all(result.status == "success" for result in results)
    assert scraper.requested_urls.count(shared_child_url) == 1


def test_explore_returns_cached_results_on_second_call() -> None:
    start_url = "https://example.com"
    scraper = FakeScraper({start_url: PageContent([])})
    explorer = SubDomainExplorer(start_url, scraper=scraper)

    first_results = asyncio.run(explorer.explore())
    second_results = asyncio.run(explorer.explore())

    assert first_results is second_results
    assert scraper.calls == 1


def test_explore_returns_failed_result_when_scraper_errors() -> None:
    start_url = "https://example.com"

    class FailingScraper:
        async def fetch_html(self, url: str) -> PageContent:
            raise RuntimeError("boom")

    explorer = SubDomainExplorer(start_url, scraper=FailingScraper())

    results = asyncio.run(explorer.explore())

    assert len(results) == 1
    assert results[0].url == start_url
    assert results[0].status == "failure"
    assert results[0].page is None
    assert results[0].error == "boom"


def test_explore_retries_timeout_errors() -> None:
    start_url = "https://example.com"

    class TimeoutThenSuccessScraper:
        def __init__(self) -> None:
            self.calls = 0

        async def fetch_html(self, url: str) -> PageContent:
            self.calls += 1

            if self.calls < 3:
                raise TimeoutError("timed out")

            return PageContent([])

    scraper = TimeoutThenSuccessScraper()
    explorer = SubDomainExplorer(start_url, scraper=scraper)

    results = asyncio.run(explorer.explore())

    assert [result.url for result in results] == [start_url]
    assert results[0].status == "success"
    assert scraper.calls == 3
