"""
Literature Review Generator Engine — Handles the creation of full structured literature reviews.
"""
from typing import List
from openai import AsyncOpenAI
from models.schemas import Paper
from utils.llm_utils import llm_call_with_retry


class LiteratureReviewGenerator:
    def __init__(self, settings):
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key or "placeholder",
            base_url=settings.llm_base_url,
        )
        self.model = settings.llm_heavy_model

    async def generate_review(self, topic: str, papers: List[Paper], gaps: list = None) -> str:
        """Generate a structured, publication-grade literature review."""
        paper_context = ""
        sorted_papers = sorted(papers, key=lambda p: p.citations, reverse=True)[:25]
        
        for i, p in enumerate(sorted_papers):
            paper_context += f"[{i+1}] {p.title} ({p.year})\n"
            paper_context += f"    Authors: {', '.join(p.authors[:3])}\n"
            if p.summary:
                paper_context += f"    Summary: {p.summary}\n"
            if p.key_findings:
                paper_context += f"    Findings: {'; '.join(p.key_findings[:3])}\n"
            paper_context += "\n"

        gaps_text = ""
        if gaps:
            gaps_text = "\n".join(
                f"- {g.get('gap', g) if isinstance(g, dict) else g}"
                for g in gaps[:8]
            )

        prompt = f"""Write a comprehensive, publication-ready literature review on "{topic}" based on these papers.

Structure:
1. Introduction (problem definition, scope, significance)
2. Methodological Landscape (key approaches, techniques, frameworks)
3. Major Findings & Breakthroughs (synthesize by theme, not paper-by-paper)
4. Open Problems & Research Gaps
5. Future Directions & Conclusion

Use [1], [2] style citations. Synthesize across papers thematically.
Academic tone, 1500-2500 words.

Papers:
{paper_context}

Known Gaps:
{gaps_text}

Write the full review in Markdown:"""

        review = await llm_call_with_retry(
            client=self.client,
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000,
            max_retries=3,
        )

        if review:
            return review
        return f"# Literature Review: {topic}\n\nReview generation failed. Please retry."
