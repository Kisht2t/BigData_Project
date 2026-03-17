"""Hacker News retriever — searches via Algolia HN Search API."""

from __future__ import annotations

import urllib.parse
import urllib.request
import json


class HackerNewsRetriever:
    _BASE_URL = "https://hn.algolia.com/api/v1/search"

    def fetch(self, query: str, max_results: int = 5) -> list[dict]:
        """Search HN stories matching query. Returns list of {title, text, url}."""
        params = urllib.parse.urlencode({
            "query": query,
            "tags": "story",
            "hitsPerPage": max_results,
        })
        url = f"{self._BASE_URL}?{params}"

        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read())

        results = []
        for hit in data.get("hits", []):
            title = hit.get("title", "")
            story_text = hit.get("story_text") or hit.get("comment_text") or ""
            story_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}"

            if not title:
                continue

            results.append({
                "title": title,
                "text": story_text[:1000] if story_text else title,  # fallback to title
                "url": story_url,
                "source": "hackernews",
                "metadata": {
                    "points": hit.get("points", 0),
                    "num_comments": hit.get("num_comments", 0),
                    "author": hit.get("author", ""),
                },
            })

        return results
