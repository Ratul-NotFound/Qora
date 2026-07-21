"""
Reader Agent — Uses LLMs to deeply analyze papers:
  - Structured summaries (problem, method, results, limitations)
  - Key findings extraction
  - Methods and datasets identification
  - Research gap spotting within individual papers
"""
import asyncio
import json
from typing import List, Optional, Callable
from openai import AsyncOpenAI
from models.schemas import Paper
from sources.pdf_downloader import PDFDownloader


SYSTEM_PROMPT = """You are an expert research analyst AI. Your job is to analyze academic papers
and extract structured, high-quality information. Be precise, factual, and concise.
Always respond with valid JSON only — no markdown, no explanation, just the JSON object."""

ANALYSIS_PROMPT = """Analyze this academic paper and return a JSON object with this exact structure:
{
  "summary": "2-3 sentence plain-English summary of what this paper does and why it matters",
  "key_findings": ["finding 1", "finding 2", "finding 3"],
  "methods": ["method/technique 1", "method/technique 2"],
  "datasets": ["dataset 1", "dataset 2"],
  "research_gaps": ["gap/limitation 1", "gap/limitation 2"],
  "relevance_score": 0.85
}

Paper Title: {title}
Authors: {authors}
Year: {year}
Abstract: {abstract}

Respond ONLY with the JSON object."""


class ReaderAgent:
    def __init__(self, settings):
        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key or "placeholder",
            base_url=settings.llm_base_url,
        )
        self.semaphore = asyncio.Semaphore(settings.max_concurrent_summaries)
        self.pdf_downloader = PDFDownloader()

    async def analyze_papers(
        self,
        papers: List[Paper],
        topic: str,
        on_progress: Optional[Callable] = None,
    ) -> List[Paper]:
        """Analyze all papers concurrently (with semaphore to control rate)."""
        total = len(papers)
        analyzed = []
        tasks = [self._analyze_one(p, topic, i, total, on_progress) for i, p in enumerate(papers)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Paper):
                analyzed.append(result)
            else:
                # Return original paper on failure
                analyzed.append(papers[i])
        return analyzed

    async def _analyze_one(
        self, paper: Paper, topic: str, idx: int, total: int, on_progress: Optional[Callable]
    ) -> Paper:
        if not paper.abstract and not paper.pdf_url:
            return paper

        async with self.semaphore:
            try:
                # Attempt full PDF download if available
                full_text = None
                if paper.pdf_url:
                    full_text = await self.pdf_downloader.download_and_extract_text(paper.pdf_url)

                content_to_analyze = (full_text[:4000] if full_text else paper.abstract[:2000])

                prompt = ANALYSIS_PROMPT.format(
                    title=paper.title[:200],
                    authors=", ".join(paper.authors[:5]),
                    year=paper.year or "Unknown",
                    abstract=content_to_analyze,
                )

                response = await self.client.chat.completions.create(
                    model=self.settings.llm_model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.1,
                    max_tokens=600,
                )

                raw = response.choices[0].message.content.strip()
                # Strip markdown code fences if present
                if raw.startswith("```"):
                    raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]

                data = json.loads(raw)
                paper.summary = data.get("summary", "")
                paper.key_findings = data.get("key_findings", [])
                paper.methods = data.get("methods", [])
                paper.datasets = data.get("datasets", [])
                paper.research_gaps = data.get("research_gaps", [])
                paper.relevance_score = float(data.get("relevance_score", 0.5))

                if on_progress:
                    progress = 0.45 + (0.3 * (idx + 1) / total)
                    await on_progress(
                        f"📄 Analyzed: {paper.title[:60]}...",
                        progress,
                    )

            except Exception as e:
                print(f"[ReaderAgent] Failed to analyze '{paper.title[:40]}': {e}")

        return paper

    async def quick_relevance_filter(
        self, papers: List[Paper], topic: str, threshold: float = 0.3
    ) -> List[Paper]:
        """Fast LLM-based relevance scoring to filter irrelevant papers before deep analysis."""
        if not papers:
            return []

        # Batch titles for quick scoring
        batch_size = 20
        relevant = []

        for i in range(0, len(papers), batch_size):
            batch = papers[i: i + batch_size]
            titles_block = "\n".join(
                f"{j + 1}. {p.title}" for j, p in enumerate(batch)
            )
            prompt = f"""Topic: "{topic}"

Rate each paper's relevance to the topic (0.0 to 1.0). Return JSON array of scores only.
Example: [0.9, 0.2, 0.7, ...]

Papers:
{titles_block}

Return ONLY the JSON array of {len(batch)} float numbers."""

            try:
                response = await self.client.chat.completions.create(
                    model=self.settings.llm_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=200,
                )
                raw = response.choices[0].message.content.strip()
                if raw.startswith("["):
                    scores = json.loads(raw)
                    for paper, score in zip(batch, scores):
                        if float(score) >= threshold:
                            paper.relevance_score = float(score)
                            relevant.append(paper)
                else:
                    relevant.extend(batch)  # Keep all if parsing fails
            except Exception:
                relevant.extend(batch)

        return relevant
