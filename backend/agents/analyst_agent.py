"""
Analyst Agent — High-level intelligence engine:
  - Research timeline construction
  - Research gap synthesis across papers
  - Hypothesis generation
  - Trend analysis
  - Knowledge graph edge extraction
"""
import json
from typing import List, Callable, Optional
from openai import AsyncOpenAI
from models.schemas import Paper
from knowledge.timeline import TimelineBuilder
from utils.llm_utils import llm_call_with_retry, extract_json


class AnalystAgent:
    def __init__(self, settings):
        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key or "placeholder",
            base_url=settings.llm_base_url,
        )
        self.timeline_builder = TimelineBuilder()

    async def analyze(
        self,
        papers: List[Paper],
        topic: str,
        on_progress: Optional[Callable] = None,
    ) -> dict:
        """Run all analysis tasks and return consolidated intelligence report."""
        if on_progress:
            await on_progress("Running deep intelligence analysis...", 0.76)

        gaps_task = self._find_research_gaps(papers, topic)
        trends_task = self._analyze_trends(papers, topic)
        hypo_task = self._generate_hypotheses(papers, topic)
        graph_task = self._build_graph_data(papers)

        gaps, trends, hypotheses, graph_data = await __import__("asyncio").gather(
            gaps_task, trends_task, hypo_task, graph_task
        )

        if on_progress:
            await on_progress("Intelligence analysis complete!", 0.88)

        return {
            "gaps": gaps,
            "trends": trends,
            "hypotheses": hypotheses,
            "graph_data": graph_data,
        }

    async def _find_research_gaps(self, papers: List[Paper], topic: str) -> List[dict]:
        """Synthesize research gaps across all analyzed papers."""
        all_gaps = []
        for p in papers:
            all_gaps.extend(p.research_gaps)

        abstract_block = "\n\n".join(
            f"[{p.year}] {p.title}: {p.abstract[:300]}"
            for p in papers[:30]
            if p.abstract
        )

        prompt = f"""You are analyzing the state of research on: "{topic}"

Based on these papers, identify the most critical UNSOLVED RESEARCH GAPS and OPEN PROBLEMS.
Also consider the individual gaps noted in each paper.

Paper abstracts:
{abstract_block[:6000]}

Individual gaps mentioned:
{json.dumps(all_gaps[:30])}

Return a JSON array of gap objects:
[
  {{
    "gap": "Short title of the gap",
    "description": "2-3 sentences explaining the gap and why it matters",
    "severity": "high|medium|low",
    "related_papers": 3
  }}
]

Return ONLY the JSON array."""

        raw = await llm_call_with_retry(
            client=self.client,
            model=self.settings.llm_heavy_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=2000,
            max_retries=3,
        )

        result = extract_json(raw) if raw else None
        if result and isinstance(result, list):
            return result

        # Fallback: return raw paper gaps
        return [{"gap": g, "description": "", "severity": "medium", "related_papers": 1}
                for g in all_gaps[:10]]

    async def _analyze_trends(self, papers: List[Paper], topic: str) -> dict:
        """Analyze temporal trends in the research area using TimelineBuilder."""
        return self.timeline_builder.build_timeline(papers)

    async def _generate_hypotheses(self, papers: List[Paper], topic: str) -> List[dict]:
        """Generate novel research hypotheses based on gaps and trends."""
        findings_block = "\n".join(
            f"- {f}" for p in papers[:20] for f in p.key_findings[:2]
        )
        gaps_block = "\n".join(
            f"- {g}" for p in papers[:20] for g in p.research_gaps[:1]
        )

        prompt = f"""You are a brilliant research strategist with expertise in "{topic}".

Based on the current state of research (key findings and gaps below), generate 5 NOVEL, FEASIBLE research hypotheses.
Each hypothesis should be specific, testable, and address a real gap.

Key Findings from literature:
{findings_block[:3000]}

Known Research Gaps:
{gaps_block[:2000]}

Return a JSON array:
[
  {{
    "hypothesis": "Clear, specific hypothesis statement",
    "rationale": "2 sentences explaining why this is promising and novel",
    "approach": "Suggested methodology to test this hypothesis",
    "novelty": "high|medium",
    "feasibility": "high|medium|low",
    "impact": "high|medium|low"
  }}
]

Return ONLY the JSON array."""

        raw = await llm_call_with_retry(
            client=self.client,
            model=self.settings.llm_heavy_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
            max_retries=3,
        )

        result = extract_json(raw) if raw else None
        if result and isinstance(result, list):
            return result
        return []

    async def _build_graph_data(self, papers: List[Paper]) -> dict:
        """Build nodes and edges for the knowledge graph visualization."""
        nodes = []
        edges = []

        # Paper nodes
        for p in papers[:50]:
            nodes.append({
                "id": p.id,
                "label": p.title[:60] + ("..." if len(p.title) > 60 else ""),
                "type": "paper",
                "year": p.year,
                "citations": p.citations,
                "source": p.source,
                "size": max(5, min(30, 5 + p.citations / 10)),
            })

        # Method concept nodes
        method_counts = {}
        for p in papers[:50]:
            for m in p.methods:
                if m:
                    method_counts[m] = method_counts.get(m, 0) + 1

        for method, count in list(method_counts.items())[:20]:
            if count > 1:
                method_id = f"method_{method[:30]}"
                nodes.append({
                    "id": method_id,
                    "label": method[:40],
                    "type": "method",
                    "size": 8 + count * 2,
                })
                for p in papers[:50]:
                    if method in p.methods:
                        edges.append({
                            "source": p.id,
                            "target": method_id,
                            "type": "uses_method",
                            "weight": 1,
                        })

        return {"nodes": nodes, "edges": edges}
