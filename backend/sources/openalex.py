"""
OpenAlex Source — 250M+ scholarly works, 100% free & open.
No API key required.
"""
import httpx
from typing import List, Optional
from models.schemas import Paper


OA_API_BASE = "https://api.openalex.org"


class OpenAlexSource:
    name = "openalex"

    HEADERS = {"User-Agent": "QORA Research AI (research@qora.ai)"}

    async def search(
        self,
        query: str,
        max_results: int = 25,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> List[Paper]:
        params = {
            "search": query,
            "per-page": min(max_results, 200),
            "sort": "cited_by_count:desc",
            "select": "id,title,authorships,abstract_inverted_index,publication_year,"
                      "cited_by_count,doi,open_access,primary_location,concepts,keywords",
        }
        if year_from or year_to:
            y_from = year_from or 2000
            y_to = year_to or 2025
            params["filter"] = f"publication_year:{y_from}-{y_to}"

        async with httpx.AsyncClient(timeout=30, headers=self.HEADERS) as client:
            resp = await client.get(f"{OA_API_BASE}/works", params=params)
            if resp.status_code != 200:
                return []
            data = resp.json()

        papers = []
        for item in data.get("results", []):
            try:
                papers.append(self._parse_item(item))
            except Exception:
                continue
        return papers

    def _parse_item(self, item: dict) -> Paper:
        # Reconstruct abstract from inverted index
        abstract = self._reconstruct_abstract(item.get("abstract_inverted_index"))

        # Authors
        authors = []
        for authorship in item.get("authorships", []):
            author = authorship.get("author", {})
            if author and author.get("display_name"):
                authors.append(author["display_name"])

        # DOI & URLs
        doi = item.get("doi", "") or ""
        if doi.startswith("https://doi.org/"):
            doi = doi[len("https://doi.org/"):]

        primary = item.get("primary_location", {}) or {}
        url = primary.get("landing_page_url", "") or (f"https://doi.org/{doi}" if doi else "")
        pdf_url = ""
        oa = item.get("open_access", {}) or {}
        if oa.get("oa_url"):
            pdf_url = oa["oa_url"]

        # Keywords / concepts
        keywords = []
        for kw in item.get("keywords", []) or []:
            if isinstance(kw, dict):
                keywords.append(kw.get("keyword", ""))
            elif isinstance(kw, str):
                keywords.append(kw)
        if not keywords:
            for c in item.get("concepts", []) or []:
                if c.get("score", 0) > 0.5:
                    keywords.append(c.get("display_name", ""))

        oa_id = item.get("id", "").split("/")[-1]

        return Paper(
            id=f"oa_{oa_id}",
            title=item.get("title", "") or "",
            authors=authors,
            abstract=abstract,
            year=item.get("publication_year"),
            source="OpenAlex",
            url=url,
            pdf_url=pdf_url,
            citations=item.get("cited_by_count", 0) or 0,
            doi=doi,
            keywords=keywords[:5],
        )

    def _reconstruct_abstract(self, inverted_index: Optional[dict]) -> str:
        """OpenAlex stores abstracts as inverted word-position index."""
        if not inverted_index:
            return ""
        positions = {}
        for word, pos_list in inverted_index.items():
            for pos in pos_list:
                positions[pos] = word
        if not positions:
            return ""
        return " ".join(positions[i] for i in sorted(positions.keys()))
