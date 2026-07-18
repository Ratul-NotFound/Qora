"""
Search Agent — Orchestrates parallel multi-source paper discovery.
Deduplicates results and scores relevance.
"""
import asyncio
import hashlib
from typing import List, Callable, Optional
from models.schemas import Paper
from sources.arxiv import ArxivSource
from sources.semantic_scholar import SemanticScholarSource
from sources.pubmed import PubMedSource
from sources.openalex import OpenAlexSource
from sources.core import CoreSource


class SearchAgent:
    def __init__(self, settings):
        self.settings = settings
        self.sources = {
            "arxiv": ArxivSource(),
            "semantic_scholar": SemanticScholarSource(api_key=settings.semantic_scholar_api_key),
            "pubmed": PubMedSource(api_key=settings.ncbi_api_key),
            "openalex": OpenAlexSource(),
            "core": CoreSource(api_key=settings.core_api_key),
        }

    async def search(
        self,
        query: str,
        enabled_sources: List[str] = None,
        max_per_source: int = 25,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        on_progress: Optional[Callable] = None,
    ) -> List[Paper]:
        """Search all enabled sources in parallel and return deduplicated results."""
        if enabled_sources is None:
            enabled_sources = list(self.sources.keys())

        if on_progress:
            await on_progress("Launching parallel search across all sources...", 0.05)

        tasks = []
        for source_name in enabled_sources:
            source = self.sources.get(source_name)
            if source:
                tasks.append(self._safe_search(source, query, max_per_source, year_from, year_to))

        all_results = await asyncio.gather(*tasks)

        merged = []
        for i, (source_name, results) in enumerate(zip(enabled_sources, all_results)):
            merged.extend(results)
            if on_progress:
                progress = 0.05 + (0.35 * (i + 1) / len(enabled_sources))
                await on_progress(
                    f"✓ {source_name.replace('_', ' ').title()}: {len(results)} papers found",
                    progress,
                )

        # Deduplicate by title similarity
        unique = self._deduplicate(merged)

        if on_progress:
            await on_progress(f"Deduplication complete. {len(unique)} unique papers.", 0.42)

        return unique

    async def trace_citations(
        self,
        papers: List[Paper],
        depth: int = 1,
        on_progress: Optional[Callable] = None,
    ) -> List[Paper]:
        """Recursively trace citations to find related foundational work."""
        all_papers = list(papers)
        seen_ids = {p.id for p in papers}
        ss_source = self.sources["semantic_scholar"]

        current_level = [p for p in papers if p.id.startswith("ss_")]

        for level in range(depth):
            if not current_level:
                break

            if on_progress:
                await on_progress(
                    f"Tracing citation network — depth {level + 1}/{depth}...",
                    0.55 + (0.1 * level),
                )

            tasks = []
            for paper in current_level[:10]:  # Limit to avoid rate limiting
                ss_id = paper.id.replace("ss_", "")
                tasks.append(ss_source.get_references(ss_id, limit=10))

            ref_lists = await asyncio.gather(*tasks, return_exceptions=True)
            new_papers = []
            for refs in ref_lists:
                if isinstance(refs, list):
                    for ref in refs:
                        if ref.id not in seen_ids and ref.title:
                            seen_ids.add(ref.id)
                            new_papers.append(ref)

            all_papers.extend(new_papers)
            current_level = new_papers

        return all_papers

    async def _safe_search(self, source, query, max_results, year_from, year_to) -> List[Paper]:
        try:
            return await source.search(query, max_results, year_from, year_to)
        except Exception as e:
            print(f"[SearchAgent] {source.name} failed: {e}")
            return []

    def _deduplicate(self, papers: List[Paper]) -> List[Paper]:
        """Remove duplicates by normalized title fingerprint."""
        seen = {}
        unique = []
        for paper in papers:
            if not paper.title:
                continue
            key = self._title_key(paper.title)
            if key not in seen:
                seen[key] = paper
                unique.append(paper)
            else:
                # Keep the one with more info (citations, abstract, etc.)
                existing = seen[key]
                if (paper.citations > existing.citations or
                        (len(paper.abstract) > len(existing.abstract))):
                    seen[key] = paper
                    # Replace in list
                    idx = unique.index(existing)
                    unique[idx] = paper
        return unique

    def _title_key(self, title: str) -> str:
        normalized = "".join(c.lower() for c in title if c.isalnum())
        return hashlib.md5(normalized.encode()).hexdigest()
