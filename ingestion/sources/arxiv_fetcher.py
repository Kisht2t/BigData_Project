"""arXiv bulk fetcher for the ingestion pipeline."""

from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


class ArxivFetcher:
    _BASE_URL = "https://export.arxiv.org/api/query"
    _NS = "http://www.w3.org/2005/Atom"

    def fetch(self, query: str, max_results: int = 10) -> list[dict]:
        params = urllib.parse.urlencode({
            "search_query": f"all:{query}",
            "max_results": max_results,
            "sortBy": "relevance",
        })
        url = f"{self._BASE_URL}?{params}"

        with urllib.request.urlopen(url, timeout=15) as response:
            xml_data = response.read()

        return self._parse(xml_data)

    def fetch_by_id(self, arxiv_id: str) -> dict | None:
        """Fetch a single paper by arXiv ID (e.g. '2310.06825')."""
        params = urllib.parse.urlencode({"id_list": arxiv_id})
        url = f"{self._BASE_URL}?{params}"

        with urllib.request.urlopen(url, timeout=15) as response:
            xml_data = response.read()

        results = self._parse(xml_data)
        return results[0] if results else None

    def _parse(self, xml_data: bytes) -> list[dict]:
        root = ET.fromstring(xml_data)
        papers = []

        for entry in root.findall(f"{{{self._NS}}}entry"):
            title_el = entry.find(f"{{{self._NS}}}title")
            summary_el = entry.find(f"{{{self._NS}}}summary")
            id_el = entry.find(f"{{{self._NS}}}id")

            if not (title_el is not None and summary_el is not None and id_el is not None):
                continue

            papers.append({
                "text": summary_el.text.strip().replace("\n", " "),
                "title": title_el.text.strip().replace("\n", " "),
                "url": id_el.text.strip(),
                "source": "arxiv",
                "metadata": {
                    "authors": [
                        a.find(f"{{{self._NS}}}name").text
                        for a in entry.findall(f"{{{self._NS}}}author")
                        if a.find(f"{{{self._NS}}}name") is not None
                    ]
                },
            })

        return papers
