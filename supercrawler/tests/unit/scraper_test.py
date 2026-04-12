from __future__ import annotations

from unittest.mock import patch

import pytest
from urllib.error import URLError

from supercrawler.model.page_content import PageContent
from supercrawler.web.scraper import Scraper, _is_page_link


class FakeHeaders:
    def __init__(self, charset: str | None = "utf-8"):
        self.charset = charset

    def get_content_charset(self, failobj: str = "utf-8") -> str:
        return self.charset or failobj


class FakeResponse:
    def __init__(self, body: bytes, charset: str | None = "utf-8"):
        self._body = body
        self.headers = FakeHeaders(charset)

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
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
    html = b"""
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
        "supercrawler.web.scraper.urllib.request.urlopen",
        return_value=FakeResponse(html),
    ) as mock_urlopen:
        result = Scraper().fetch_html("https://example.com")

    assert result == PageContent(
        [
            "https://example.com/about",
            "/contact",
        ]
    )
    mock_urlopen.assert_called_once()


def test_fetch_html_raises_value_error_for_invalid_charset() -> None:
    with patch(
        "supercrawler.web.scraper.urllib.request.urlopen",
        return_value=FakeResponse(b"hello", charset="invalid-charset"),
    ):
        with pytest.raises(ValueError, match="Unable to decode response content as text"):
            Scraper().fetch_html("https://example.com")


def test_fetch_html_propagates_url_errors() -> None:
    with patch(
        "supercrawler.web.scraper.urllib.request.urlopen",
        side_effect=URLError("network down"),
    ):
        with pytest.raises(URLError, match="network down"):
            Scraper().fetch_html("https://example.com")
