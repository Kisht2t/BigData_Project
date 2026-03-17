"""GitHub retriever — searches trending repos and fetches README content."""

from __future__ import annotations

import os
import urllib.parse
import urllib.request
import json
import base64


class GitHubRetriever:
    _SEARCH_URL = "https://api.github.com/search/repositories"
    _README_URL = "https://api.github.com/repos/{owner}/{repo}/readme"
    _TOKEN = os.getenv("GITHUB_TOKEN", "")

    def _headers(self) -> dict:
        headers = {"Accept": "application/vnd.github+json"}
        if self._TOKEN:
            headers["Authorization"] = f"Bearer {self._TOKEN}"
        return headers

    def fetch(self, query: str, max_results: int = 5) -> list[dict]:
        """Search GitHub repos and return README snippets."""
        params = urllib.parse.urlencode({
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": max_results,
        })
        url = f"{self._SEARCH_URL}?{params}"

        req = urllib.request.Request(url, headers=self._headers())
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read())

        results = []
        for repo in data.get("items", [])[:max_results]:
            owner = repo["owner"]["login"]
            name = repo["name"]
            readme_text = self._fetch_readme(owner, name)

            results.append({
                "title": f"{owner}/{name}",
                "text": readme_text[:1200],  # first ~1200 chars of README
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
            with urllib.request.urlopen(req, timeout=8) as response:
                data = json.loads(response.read())
            content = base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            # Strip markdown syntax roughly
            return content[:2000]
        except Exception:
            return ""
