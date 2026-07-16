"""
ArXiv Source — Fetches papers from arxiv.org using their public API.
Covers: CS, Physics, Math, Biology, Economics, Quantitative Finance.
"""
import httpx
import xmltodict
import re
from datetime import datetime
from typing import List, Optional
from models.schemas import Paper


ARXIV_API_URL = "http://export.arxiv.org/api/query"


class ArxivSource:
    name = "arxiv"

    async def search(
        self,
        query: str,
        max_results: int = 25,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> List[Paper]:
        params = {
            "search_query": f"all:{query}",
            "start": 0,
            "max_results": max_results,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        if year_from or year_to:
            y_from = year_from or 2000
            y_to = year_to or datetime.now().year
            params["search_query"] += f" AND submittedDate:[{y_from}0101 TO {y_to}1231]"

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(ARXIV_API_URL, params=params)
            resp.raise_for_status()

        data = xmltodict.parse(resp.text)
        feed = data.get("feed", {})
        entries = feed.get("entry", [])

        if isinstance(entries, dict):
            entries = [entries]

        papers = []
        for entry in entries:
            try:
                paper = self._parse_entry(entry)
                papers.append(paper)
            except Exception:
                continue

        return papers

    def _parse_entry(self, entry: dict) -> Paper:
        arxiv_id = entry.get("id", "").split("/abs/")[-1].strip()

        # Authors
        authors_raw = entry.get("author", [])
        if isinstance(authors_raw, dict):
            authors_raw = [authors_raw]
        authors = [a.get("name", "") for a in authors_raw if isinstance(a, dict)]

        # Year
        published = entry.get("published", "")
        year = int(published[:4]) if published else None

        # PDF URL
        links = entry.get("link", [])
        if isinstance(links, dict):
            links = [links]
        pdf_url = ""
        for link in links:
            if isinstance(link, dict) and link.get("@title") == "pdf":
                pdf_url = link.get("@href", "")

        # Categories / keywords
        categories = entry.get("category", [])
        if isinstance(categories, dict):
            categories = [categories]
        keywords = [c.get("@term", "") for c in categories if isinstance(c, dict)]

        return Paper(
            id=f"arxiv_{arxiv_id}",
            title=entry.get("title", "").replace("\n", " ").strip(),
            authors=authors,
            abstract=entry.get("summary", "").replace("\n", " ").strip(),
            year=year,
            source="ArXiv",
            url=f"https://arxiv.org/abs/{arxiv_id}",
            pdf_url=pdf_url or f"https://arxiv.org/pdf/{arxiv_id}",
            doi=entry.get("arxiv:doi", {}).get("#text", "") if isinstance(entry.get("arxiv:doi"), dict) else "",
            keywords=keywords[:5],
        )

    async def get_by_id(self, arxiv_id: str) -> Optional[Paper]:
        params = {"id_list": arxiv_id, "max_results": 1}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(ARXIV_API_URL, params=params)
            resp.raise_for_status()
        data = xmltodict.parse(resp.text)
        entry = data.get("feed", {}).get("entry")
        if not entry:
            return None
        if isinstance(entry, list):
            entry = entry[0]
        return self._parse_entry(entry)
