"""
Research Timeline Builder — Builds chronological evolution of ideas and detects paradigm shifts.
"""
from typing import List, Dict, Any
from models.schemas import Paper


class TimelineBuilder:
    def __init__(self):
        pass

    def build_timeline(self, papers: List[Paper]) -> Dict[str, Any]:
        """Group papers chronologically, extract milestone breakthroughs, and trace methodology shifts."""
        if not papers:
            return {"eras": [], "milestones": [], "year_range": [0, 0]}

        # 1. Filter and sort papers by year
        valid_papers = [p for p in papers if p.year and p.year > 1900]
        if not valid_papers:
            valid_papers = papers

        sorted_papers = sorted(valid_papers, key=lambda p: (p.year or 0, p.citations), reverse=False)

        # 2. Group by year
        by_year: Dict[int, List[Paper]] = {}
        for p in sorted_papers:
            year = p.year or 2024
            by_year.setdefault(year, []).append(p)

        # 3. Identify milestones (top cited paper per year/era)
        milestones = []
        eras = []

        years = sorted(by_year.keys())
        for year in years:
            year_papers = by_year[year]
            top_paper = max(year_papers, key=lambda x: x.citations)

            if top_paper.citations > 5 or len(milestones) < 5:
                milestones.append({
                    "year": year,
                    "paper_id": top_paper.id,
                    "title": top_paper.title,
                    "authors": top_paper.authors[:2],
                    "citations": top_paper.citations,
                    "key_breakthrough": top_paper.key_findings[0] if top_paper.key_findings else top_paper.summary[:150]
                })

            all_methods = list(set(m for p in year_papers for m in p.methods if m))
            eras.append({
                "year": year,
                "paper_count": len(year_papers),
                "top_methods": all_methods[:4],
                "lead_paper": top_paper.title[:60]
            })

        return {
            "eras": eras,
            "milestones": milestones[:10],
            "year_range": [min(years) if years else 0, max(years) if years else 0],
            "total_analyzed": len(valid_papers)
        }
