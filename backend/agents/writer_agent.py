"""
Writer Agent — Generates comprehensive, academic-grade literature reviews
and research reports with proper citations.
"""
from typing import List, Callable, Optional
from openai import AsyncOpenAI
from models.schemas import Paper


class WriterAgent:
    def __init__(self, settings):
        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key or "placeholder",
            base_url=settings.llm_base_url,
        )

    async def write_literature_review(
        self,
        topic: str,
        papers: List[Paper],
        intelligence_data: dict,
        on_progress: Optional[Callable] = None,
    ) -> str:
        """Generates a full literature review in Markdown format."""
        
        if on_progress:
            await on_progress("✍️ Drafting literature review...", 0.90)

        # Sort papers by relevance and citations
        top_papers = sorted(
            papers, 
            key=lambda x: (x.relevance_score * 10) + min(x.citations, 100), 
            reverse=True
        )[:30]

        paper_context = ""
        for i, p in enumerate(top_papers):
            paper_context += f"[{i+1}] {p.title} ({p.year})\n"
            paper_context += f"    Authors: {', '.join(p.authors[:3])}\n"
            paper_context += f"    Key Findings: {'; '.join(p.key_findings)}\n"
            paper_context += f"    Methods: {', '.join(p.methods)}\n\n"

        gaps = intelligence_data.get("gaps", [])
        trends = intelligence_data.get("trends", {})
        
        gaps_context = "\n".join(f"- {g['gap']}: {g.get('description', '')}" for g in gaps[:5])
        
        prompt = f"""You are an expert academic researcher writing a comprehensive literature review on: "{topic}".

Based on the provided top papers, trends, and research gaps, write a detailed, publication-ready literature review in Markdown.

Use this structure:
# Literature Review: {topic.title()}

## 1. Introduction
(Define the problem, its importance, and scope of this review)

## 2. Evolution of the Field (Trends)
(Discuss how the field has evolved temporally and methodologically)

## 3. Key Methodologies and Approaches
(Synthesize the main methods used across the papers)

## 4. Current State of the Art (Key Findings)
(What are the most significant recent breakthroughs?)

## 5. Open Challenges and Research Gaps
(Detail the unsolved problems)

## 6. Conclusion
(Summary and future outlook)

## References
(List the papers cited)

Guidelines:
- Use in-text citations like [1], [2] referencing the provided paper list.
- Synthesize ideas, do not just list paper summaries sequentially. Group by themes.
- Maintain an objective, academic tone.
- Length: Detailed, approx 1500-2500 words.

DATA:
---
Top Papers:
{paper_context}

Identified Gaps:
{gaps_context}
---

Write the full literature review in Markdown format below:"""

        try:
            response = await self.client.chat.completions.create(
                model=self.settings.llm_heavy_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4000,
            )
            report = response.choices[0].message.content.strip()
            
            if on_progress:
                await on_progress("✅ Literature review generated successfully!", 1.0)
                
            return report
        except Exception as e:
            print(f"[WriterAgent] Failed to generate review: {e}")
            return f"# Literature Review: {topic}\n\nError generating review: {str(e)}"
