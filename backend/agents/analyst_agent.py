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


class AnalystAgent:
    def __init__(self, settings):
        self.settings = settings
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
        )

    async def analyze(
        self,
        papers: List[Paper],
        topic: str,
        on_progress: Optional[Callable] = None,
    ) -> dict:
        """Run all analysis tasks and return consolidated intelligence report."""
        if on_progress:
            await on_progress("🔬 Running deep intelligence analysis...", 0.76)

        gaps_task = self._find_research_gaps(papers, topic)
        trends_task = self._analyze_trends(papers, topic)
        hypo_task = self._generate_hypotheses(papers, topic)
        graph_task = self._build_graph_data(papers)

        gaps, trends, hypotheses, graph_data = await __import__("asyncio").gather(
            gaps_task, trends_task, hypo_task, graph_task
        )

        if on_progress:
            await on_progress("✅ Intelligence analysis complete!", 0.88)

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

        try:
            response = await self.client.chat.completions.create(
                model=self.settings.llm_heavy_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
            return json.loads(raw)
        except Exception as e:
            print(f"[AnalystAgent] Gap detection failed: {e}")
            return [{"gap": g, "description": "", "severity": "medium", "related_papers": 1}
                    for g in all_gaps[:10]]

    async def _analyze_trends(self, papers: List[Paper], topic: str) -> dict:
        """Analyze temporal trends in the research area."""
        # Group papers by year
        by_year = {}
        for p in papers:
            if p.year:
                by_year.setdefault(p.year, []).append(p)

        timeline = {
            year: {
                "count": len(plist),
                "top_papers": [p.title for p in sorted(plist, key=lambda x: x.citations, reverse=True)[:3]],
                "methods": list(set(m for p in plist for m in p.methods[:2])),
            }
            for year, plist in sorted(by_year.items())
        }

        methods_count = {}
        for p in papers:
            for m in p.methods:
                if m:
                    methods_count[m] = methods_count.get(m, 0) + 1

        top_methods = sorted(methods_count.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "timeline": timeline,
            "top_methods": [{"method": m, "count": c} for m, c in top_methods],
            "total_papers": len(papers),
            "year_range": [min(by_year.keys(), default=0), max(by_year.keys(), default=0)],
        }

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

        try:
            response = await self.client.chat.completions.create(
                model=self.settings.llm_heavy_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2500,
            )
            raw = response.choices[0].message.content.strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
            return json.loads(raw)
        except Exception as e:
            print(f"[AnalystAgent] Hypothesis generation failed: {e}")
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
        paper_methods = {}
        for p in papers[:50]:
            paper_methods[p.id] = p.methods
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
