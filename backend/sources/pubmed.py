"""
PubMed / NCBI Source — Medical and life sciences papers.
Uses NCBI E-utilities (free, optional API key for higher rate limits).
"""
import httpx
from typing import List, Optional
from models.schemas import Paper


ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
EFETCH_URL  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


class PubMedSource:
    name = "pubmed"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    async def search(
        self,
        query: str,
        max_results: int = 25,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> List[Paper]:
        # Step 1: Get PMIDs
        search_params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance",
        }
        if self.api_key:
            search_params["api_key"] = self.api_key
        if year_from:
            search_params["mindate"] = str(year_from)
        if year_to:
            search_params["maxdate"] = str(year_to)

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(ESEARCH_URL, params=search_params)
            resp.raise_for_status()

        ids = resp.json().get("esearchresult", {}).get("idlist", [])
        if not ids:
            return []

        # Step 2: Fetch summaries for those PMIDs
        fetch_params = {
            "db": "pubmed",
            "id": ",".join(ids),
            "retmode": "json",
        }
        if self.api_key:
            fetch_params["api_key"] = self.api_key

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(ESUMMARY_URL, params=fetch_params)
            resp.raise_for_status()

        summaries = resp.json().get("result", {})
        papers = []
        for pmid in ids:
            item = summaries.get(str(pmid), {})
            if not item or pmid == "uids":
                continue
            try:
                papers.append(self._parse_item(pmid, item))
            except Exception:
                continue
        return papers

    def _parse_item(self, pmid: str, item: dict) -> Paper:
        authors_raw = item.get("authors", [])
        authors = [a.get("name", "") for a in authors_raw if a.get("authtype") == "Author"]

        pub_date = item.get("pubdate", "")
        year = None
        if pub_date:
            try:
                year = int(pub_date[:4])
            except ValueError:
                pass

        doi = ""
        for artid in item.get("articleids", []):
            if artid.get("idtype") == "doi":
                doi = artid.get("value", "")

        return Paper(
            id=f"pubmed_{pmid}",
            title=item.get("title", ""),
            authors=authors,
            abstract="",  # ESummary doesn't include abstract; fetched separately if needed
            year=year,
            source="PubMed",
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            pdf_url="",
            citations=0,
            doi=doi,
            keywords=[kw.strip() for kw in item.get("meshterms", [])[:5]],
        )

    async def fetch_abstract(self, pmid: str) -> str:
        """Fetch full abstract for a single PMID."""
        params = {
            "db": "pubmed",
            "id": pmid.replace("pubmed_", ""),
            "rettype": "abstract",
            "retmode": "text",
        }
        if self.api_key:
            params["api_key"] = self.api_key

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(EFETCH_URL, params=params)
            if resp.status_code == 200:
                return resp.text[:2000]
        return ""
