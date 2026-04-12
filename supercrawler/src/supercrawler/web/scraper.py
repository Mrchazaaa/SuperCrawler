from __future__ import annotations

import re
import urllib.request
import http.client
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse

from supercrawler.model.page_content import PageContent


def _is_page_link(href: str) -> bool:
    if not href:
        return False

    href = href.strip()
    if href.startswith(("#", "mailto:", "tel:", "javascript:", "data:")):
        return False

    parsed = urlparse(href)
    if parsed.scheme and parsed.scheme not in {"http", "https", ""}:
        return False

    path = parsed.path.lower()
    excluded_extensions = (
        ".jpg",
        ".jpeg",
        ".png",
        ".gif",
        ".svg",
        ".webp",
        ".bmp",
        ".ico",
        ".avif",
        ".css",
        ".js",
        ".pdf",
        ".zip",
        ".tar",
        ".gz",
        ".mp3",
        ".mp4",
        ".mov",
        ".avi",
        ".wav",
        ".ogg",
        ".m3u8",
        ".json",
        ".xml",
    )

    if any(path.endswith(ext) for ext in excluded_extensions):
        return False

    return True


class Scraper:
    def fetch_html(self, url: str, timeout: float = 10.0) -> PageContent:
        request = urllib.request.Request(url)

        try:
            response: http.client.HTTPResponse
            with urllib.request.urlopen(request, timeout=timeout) as response:
                content_bytes = response.read()
        except HTTPError:
            raise
        except URLError:
            raise

        try:
            html = content_bytes.decode(response.headers.get_content_charset(failobj="utf-8"))
        except (LookupError, UnicodeDecodeError) as exc:
            raise ValueError("Unable to decode response content as text") from exc

        # Extract links from HTML and ignore non-page resources like image/asset links.
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', html)
        links = [href for href in hrefs if _is_page_link(href)]
        return PageContent(links)
