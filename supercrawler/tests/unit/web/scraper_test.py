from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from supercrawler.model.page_content import PageContent
from supercrawler.web.scraper import Scraper, _is_page_link


class FakeResponse:
    def __init__(self, body: str):
        self.text = body

    def raise_for_status(self) -> None:
        return None


@pytest.mark.parametrize(
    ("href", "expected"),
    [
        ("https://example.com/page", True),
        ("/relative-page", True),
        ("#section", False),
        ("mailto:test@example.com", False),
        ("javascript:void(0)", False),
        ("https://example.com/image.png", False),
        ("https://example.com/script.js", False),
    ],
)
def test_is_page_link_filters_supported_links(href: str, expected: bool) -> None:
    assert _is_page_link(href) is expected


def test_fetch_html_extracts_only_page_links() -> None:
    html = """
    <html>
      <body>
        <a href="https://example.com/about">About</a>
        <a href="/contact">Contact</a>
        <a href="#hero">Hero</a>
        <a href="mailto:test@example.com">Mail</a>
        <a href="https://example.com/logo.png">Logo</a>
      </body>
    </html>
    """

    with patch(
        "supercrawler.web.scraper.httpx.AsyncClient"
    ) as mock_async_client:
        mock_client = AsyncMock()
        mock_client.get.return_value = FakeResponse(html)
        mock_async_client.return_value = mock_client

        result = asyncio.run(Scraper().fetch_html("https://example.com"))

    assert result == PageContent(
        [
            "https://example.com/about",
            "/contact",
        ]
    )
    mock_client.get.assert_awaited_once_with("https://example.com", timeout=10.0)


def test_fetch_html_reuses_long_lived_http_client_across_calls() -> None:
    with patch(
        "supercrawler.web.scraper.httpx.AsyncClient"
    ) as mock_async_client:
        mock_client = AsyncMock()
        mock_client.get.side_effect = [
            FakeResponse('<a href="/first">First</a>'),
            FakeResponse('<a href="/second">Second</a>'),
        ]
        mock_async_client.return_value = mock_client

        scraper = Scraper()

        first_result = asyncio.run(scraper.fetch_html("https://example.com/one"))
        second_result = asyncio.run(scraper.fetch_html("https://example.com/two"))

    assert first_result == PageContent(["/first"])
    assert second_result == PageContent(["/second"])
    mock_async_client.assert_called_once()
    assert mock_client.get.await_args_list == [
        (( "https://example.com/one",), {"timeout": 10.0}),
        (( "https://example.com/two",), {"timeout": 10.0}),
    ]


def test_fetch_html_raises_value_error_for_invalid_charset() -> None:
    with patch(
        "supercrawler.web.scraper.httpx.AsyncClient"
    ) as mock_async_client:
        mock_client = AsyncMock()
        mock_response = Mock()
        type(mock_response).text = property(lambda self: (_ for _ in ()).throw(UnicodeDecodeError("utf-8", b"", 0, 1, "bad")))
        mock_response.raise_for_status.return_value = None
        mock_client.get.return_value = mock_response
        mock_async_client.return_value = mock_client

        with pytest.raises(ValueError, match="Unable to decode response content as text"):
            asyncio.run(Scraper().fetch_html("https://example.com"))


def test_fetch_html_propagates_httpx_errors() -> None:
    with patch(
        "supercrawler.web.scraper.httpx.AsyncClient"
    ) as mock_async_client:
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.ConnectError("network down")
        mock_async_client.return_value = mock_client

        with pytest.raises(httpx.ConnectError, match="network down"):
            asyncio.run(Scraper().fetch_html("https://example.com"))


def test_close_closes_long_lived_http_client() -> None:
    with patch(
        "supercrawler.web.scraper.httpx.AsyncClient"
    ) as mock_async_client:
        mock_client = AsyncMock()
        mock_async_client.return_value = mock_client

        scraper = Scraper()
        asyncio.run(scraper.close())

    mock_client.aclose.assert_awaited_once_with()
