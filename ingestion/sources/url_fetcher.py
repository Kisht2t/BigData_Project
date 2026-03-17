"""Generic URL fetcher for user-triggered ingestion."""

from __future__ import annotations

import urllib.request
import html
import re


def fetch_url(url: str) -> dict:
    """Fetch a URL and return a document dict for chunking."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "MARS-Ingestion/1.0"},
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        content = response.read().decode("utf-8", errors="ignore")

    text = _strip_html(content)
    title = _extract_title(content) or url

    return {
        "text": text[:10000],  # cap at 10k chars
        "title": title,
        "url": url,
        "source": "github" if "github.com" in url else "hackernews",
        "metadata": {},
    }


def _strip_html(html_content: str) -> str:
    text = re.sub(r"<script[^>]*>.*?</script>", "", html_content, flags=re.DOTALL)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _extract_title(html_content: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL)
    if match:
        return html.unescape(match.group(1).strip())
    return ""
