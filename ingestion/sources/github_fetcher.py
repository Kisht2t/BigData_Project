"""GitHub bulk fetcher — searches trending repos and extracts README content."""

from __future__ import annotations

import base64
import json
import logging
import os
import urllib.error
import urllib.parse
import urllib.request

log = logging.getLogger(__name__)


class GitHubFetcher:
    _SEARCH_URL = "https://api.github.com/search/repositories"
    _README_URL = "https://api.github.com/repos/{owner}/{repo}/readme"
    _TOKEN = os.getenv("GITHUB_TOKEN", "")

    def _headers(self) -> dict:
        h = {"Accept": "application/vnd.github+json"}
        if self._TOKEN:
            h["Authorization"] = f"Bearer {self._TOKEN}"
        return h

    def fetch(self, query: str, max_results: int = 6) -> list[dict]:
        params = urllib.parse.urlencode({
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": max_results,
        })
        url = f"{self._SEARCH_URL}?{params}"
        req = urllib.request.Request(url, headers=self._headers())

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            log.warning("GitHub search failed for %r: HTTP %s — skipping", query, exc.code)
            return []

        results = []
        for repo in data.get("items", [])[:max_results]:
            owner = repo["owner"]["login"]
            name = repo["name"]
            readme = self._fetch_readme(owner, name)

            results.append({
                "text": readme or repo.get("description", "No description"),
                "title": f"{owner}/{name}",
                "url": repo["html_url"],
                "source": "github",
                "metadata": {
                    "stars": repo.get("stargazers_count", 0),
                    "language": repo.get("language", ""),
                    "description": repo.get("description", ""),
                },
            })

        return results

    def _fetch_readme(self, owner: str, repo: str) -> str:
        try:
            url = self._README_URL.format(owner=owner, repo=repo)
            req = urllib.request.Request(url, headers=self._headers())
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())
            return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")[:3000]
        except Exception:
            return ""
