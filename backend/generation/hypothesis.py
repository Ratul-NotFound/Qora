"""
Hypothesis Generator Engine — Suggests new research directions based on gaps and trends.
"""
from typing import List
from openai import AsyncOpenAI
from utils.llm_utils import llm_call_with_retry, extract_json


class HypothesisGenerator:
    def __init__(self, settings):
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key or "placeholder",
            base_url=settings.llm_base_url,
        )
        self.model = settings.llm_heavy_model

    async def generate_hypotheses(self, topic: str, gaps: list, findings: list = None) -> List[dict]:
        """Generate novel, testable research hypotheses from identified gaps and findings."""
        gaps_text = "\n".join(
            f"- {g.get('gap', g) if isinstance(g, dict) else g}: {g.get('description', '') if isinstance(g, dict) else ''}"
            for g in gaps[:10]
        )
        findings_text = "\n".join(f"- {f}" for f in (findings or [])[:15])

        prompt = f"""You are a brilliant research strategist analyzing the field of "{topic}".

Given these research gaps and key findings, generate 5 creative, testable hypotheses.

Research Gaps:
{gaps_text}

Key Findings:
{findings_text}

Return a JSON array:
[
  {{
    "hypothesis": "A clear, specific, testable hypothesis statement",
    "rationale": "Why this hypothesis is promising and novel (2-3 sentences)",
    "approach": "Suggested experimental or computational methodology",
    "novelty": "high|medium",
    "feasibility": "high|medium|low",
    "impact": "high|medium|low"
  }}
]

Return ONLY the JSON array."""

        raw = await llm_call_with_retry(
            client=self.client,
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=2000,
            max_retries=3,
        )

        result = extract_json(raw) if raw else None
        if result and isinstance(result, list):
            return result
        return []
