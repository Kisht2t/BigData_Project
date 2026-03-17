"""arXiv retriever — fetches paper abstracts and metadata via arXiv API."""

from __future__ import annotations

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


class ArxivRetriever:
    _BASE_URL = "https://export.arxiv.org/api/query"
    _NS = "http://www.w3.org/2005/Atom"

    def fetch(self, query: str, max_results: int = 5) -> list[dict]:
        """Fetch papers matching query. Returns list of {title, abstract, url, authors}."""
        params = urllib.parse.urlencode({
            "search_query": f"all:{query}",
            "max_results": max_results,
            "sortBy": "relevance",
        })
        url = f"{self._BASE_URL}?{params}"

        with urllib.request.urlopen(url, timeout=10) as response:
            xml_data = response.read()

        root = ET.fromstring(xml_data)
        papers = []

        for entry in root.findall(f"{{{self._NS}}}entry"):
            title_el = entry.find(f"{{{self._NS}}}title")
            summary_el = entry.find(f"{{{self._NS}}}summary")
            id_el = entry.find(f"{{{self._NS}}}id")

            if title_el is None or summary_el is None or id_el is None:
                continue

            papers.append({
                "title": title_el.text.strip().replace("\n", " "),
                "text": summary_el.text.strip().replace("\n", " "),
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
