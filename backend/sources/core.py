"""
CORE Source — Fetches open access research works and PDFs from CORE (core.ac.uk).
Requires a CORE API Key.
"""
import httpx
from typing import List, Optional
from models.schemas import Paper


CORE_API_BASE = "https://api.core.ac.uk/v3"


class CoreSource:
    name = "core"

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    async def search(
        self,
        query: str,
        max_results: int = 25,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
    ) -> List[Paper]:
        if not self.api_key:
            # CORE v3 requires an API key. Return empty if missing.
            print("[CoreSource] Missing API key. Skipping search.")
            return []

        # Construct Elasticsearch-compatible query
        q_parts = [query]
        if year_from or year_to:
            y_from = year_from or 2000
            y_to = year_to or 2026
            q_parts.append(f"yearPublished:[{y_from} TO {y_to}]")

        q_str = " AND ".join(q_parts) if len(q_parts) > 1 else query

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "QORA Research AI (research@qora.ai)"
        }
        params = {
            "q": q_str,
            "limit": min(max_results, 100),
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(
                    f"{CORE_API_BASE}/search/works", 
                    params=params, 
                    headers=headers
                )
                
                if resp.status_code != 200:
                    print(f"[CoreSource] Error response: {resp.status_code} - {resp.text}")
                    return []
                    
                data = resp.json()
        except Exception as e:
            print(f"[CoreSource] Network request failed: {e}")
            return []

        papers = []
        for item in data.get("results", []):
            try:
                papers.append(self._parse_item(item))
            except Exception as ex:
                print(f"[CoreSource] Failed to parse item: {ex}")
                continue
        return papers

    def _parse_item(self, item: dict) -> Paper:
        # Reconstruct authors
        authors = []
        for author in item.get("authors", []):
            if isinstance(author, dict) and author.get("name"):
                authors.append(author["name"])
            elif isinstance(author, str):
                authors.append(author)

        # Parse year
        year = None
        published_date = item.get("publishedDate") or item.get("published_date") or item.get("datePublished")
        if published_date and isinstance(published_date, str):
            try:
                year = int(published_date.split("-")[0])
            except ValueError:
                pass
        
        if not year:
            year = item.get("yearPublished") or item.get("year_published")

        # Links
        core_id = item.get("id")
        doi = item.get("doi") or ""
        
        # Determine URLs
        download_url = item.get("downloadUrl") or item.get("download_url")
        url = download_url or f"https://core.ac.uk/works/{core_id}"
        pdf_url = download_url or ""

        # Keywords
        keywords = []
        subjects = item.get("subjects", []) or []
        for sub in subjects:
            if isinstance(sub, str):
                keywords.append(sub)
            elif isinstance(sub, dict) and sub.get("name"):
                keywords.append(sub["name"])

        return Paper(
            id=f"core_{core_id}",
            title=item.get("title", "") or "",
            authors=authors,
            abstract=item.get("abstract", "") or "",
            year=year,
            source="CORE",
            url=url,
            pdf_url=pdf_url,
            citations=0,  # CORE v3 doesn't natively expose citations directly in work searches
            doi=doi,
            keywords=keywords[:5],
        )
