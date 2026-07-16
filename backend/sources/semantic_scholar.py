"""
Semantic Scholar Source — 200M+ papers with citation data.
Free API — optional API key for higher rate limits.
"""
import httpx
from typing import List, Optional
from models.schemas import Paper


SS_API_BASE = "https://api.semanticscholar.org/graph/v1"

FIELDS = (
    "paperId,title,authors,abstract,year,citationCount,"
    "externalIds,url,openAccessPdf,fieldsOfStudy,s2FieldsOfStudy,"
    "references,citations"
)


class SemanticScholarSource:
    name = "semantic_scholar"

    def __init__(self, api_key: str = ""):
        self.headers = {}
        if api_key:
            self.headers["x-api-key"] = api_key

    async def search(
        self,
        query: str,
        max_results: int = 25,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> List[Paper]:
        params = {
            "query": query,
            "limit": min(max_results, 100),
            "fields": "paperId,title,authors,abstract,year,citationCount,externalIds,url,openAccessPdf,fieldsOfStudy",
        }
        if year_from and year_to:
            params["year"] = f"{year_from}-{year_to}"
        elif year_from:
            params["year"] = f"{year_from}-"
        elif year_to:
            params["year"] = f"-{year_to}"

        async with httpx.AsyncClient(timeout=30, headers=self.headers) as client:
            resp = await client.get(f"{SS_API_BASE}/paper/search", params=params)
            if resp.status_code == 429:
                return []  # Rate limited — skip gracefully
            resp.raise_for_status()

        data = resp.json()
        papers = []
        for item in data.get("data", []):
            try:
                papers.append(self._parse_item(item))
            except Exception:
                continue
        return papers

    async def get_citations(self, paper_id: str, limit: int = 20) -> List[Paper]:
        """Fetch papers that CITED this paper (forward citations)."""
        async with httpx.AsyncClient(timeout=30, headers=self.headers) as client:
            resp = await client.get(
                f"{SS_API_BASE}/paper/{paper_id}/citations",
                params={"fields": "paperId,title,authors,abstract,year,citationCount,url", "limit": limit},
            )
            if resp.status_code != 200:
                return []
        data = resp.json()
        papers = []
        for item in data.get("data", []):
            citing = item.get("citingPaper", {})
            try:
                papers.append(self._parse_item(citing))
            except Exception:
                continue
        return papers

    async def get_references(self, paper_id: str, limit: int = 20) -> List[Paper]:
        """Fetch papers this paper REFERENCED (backward citations)."""
        async with httpx.AsyncClient(timeout=30, headers=self.headers) as client:
            resp = await client.get(
                f"{SS_API_BASE}/paper/{paper_id}/references",
                params={"fields": "paperId,title,authors,abstract,year,citationCount,url", "limit": limit},
            )
            if resp.status_code != 200:
                return []
        data = resp.json()
        papers = []
        for item in data.get("data", []):
            ref = item.get("citedPaper", {})
            try:
                papers.append(self._parse_item(ref))
            except Exception:
                continue
        return papers

    def _parse_item(self, item: dict) -> Paper:
        authors = [a.get("name", "") for a in item.get("authors", [])]
        pdf_url = ""
        oap = item.get("openAccessPdf")
        if oap and isinstance(oap, dict):
            pdf_url = oap.get("url", "")

        external = item.get("externalIds", {}) or {}
        doi = external.get("DOI", "")
        arxiv_id = external.get("ArXiv", "")

        keywords = []
        for f in item.get("fieldsOfStudy", []) or []:
            if isinstance(f, str):
                keywords.append(f)
            elif isinstance(f, dict):
                keywords.append(f.get("category", ""))

        return Paper(
            id=f"ss_{item.get('paperId', '')}",
            title=item.get("title", "") or "",
            authors=authors,
            abstract=item.get("abstract", "") or "",
            year=item.get("year"),
            source="Semantic Scholar",
            url=item.get("url", "") or (f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else ""),
            pdf_url=pdf_url,
            citations=item.get("citationCount", 0) or 0,
            doi=doi,
            keywords=keywords[:5],
        )
