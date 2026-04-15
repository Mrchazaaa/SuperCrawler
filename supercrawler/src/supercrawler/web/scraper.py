from __future__ import annotations

import re
import ssl
from urllib.parse import urlparse

import httpx

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
        ".ttf",
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
    def __init__(self) -> None:
        ssl_context = ssl.create_default_context()
        self._client = httpx.AsyncClient(
            follow_redirects=True,
            verify=ssl_context,
        )

    async def fetch_html(self, url: str, timeout: float = 10.0) -> PageContent:
        response = await self._client.get(url, timeout=timeout)
        response.raise_for_status()
        try:
            html = response.text
        except UnicodeDecodeError as exc:
            raise ValueError("Unable to decode response content as text") from exc

        # Extract links from HTML and ignore non-page resources like image/asset links.
        hrefs = re.findall(r'href=["\']([^"\']+)["\']', html)
        links = [href for href in hrefs if _is_page_link(href)]
        return PageContent(links)

    async def close(self) -> None:
        await self._client.aclose()
