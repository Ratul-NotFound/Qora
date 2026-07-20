"""
Report Builder — Constructs multi-format reports (Markdown, LaTeX) from generated intelligence.
"""
from typing import List, Dict, Any
from models.schemas import Paper


class ReportBuilder:
    def __init__(self):
        pass

    def build_markdown_report(self, topic: str, review_text: str, papers: List[Paper], intelligence: Dict[str, Any]) -> str:
        """Constructs a complete, publication-ready Markdown dossier."""
        header = f"# QORA Research Intelligence Dossier: {topic.title()}\n\n"
        header += f"**Generated on:** {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}\n"
        header += f"**Total Papers Analyzed:** {len(papers)}\n\n"

        # Executive Summary / Gaps Matrix
        gaps_section = "## Executive Research Gaps Matrix\n\n"
        gaps = intelligence.get("gaps", [])
        if gaps:
            gaps_section += "| Gap Title | Severity | Impact Description |\n"
            gaps_section += "| :--- | :---: | :--- |\n"
            for g in gaps[:5]:
                title = g.get("gap", "") if isinstance(g, dict) else str(g)
                sev = g.get("severity", "medium") if isinstance(g, dict) else "medium"
                desc = g.get("description", "") if isinstance(g, dict) else ""
                gaps_section += f"| **{title}** | `{sev}` | {desc[:100]} |\n"
            gaps_section += "\n"

        # Hypotheses Section
        hypo_section = "## AI-Generated Novel Hypotheses\n\n"
        hypotheses = intelligence.get("hypotheses", [])
        if hypotheses:
            for i, h in enumerate(hypotheses[:3], 1):
                statement = h.get("hypothesis", "") if isinstance(h, dict) else str(h)
                rationale = h.get("rationale", "") if isinstance(h, dict) else ""
                approach = h.get("approach", "") if isinstance(h, dict) else ""
                hypo_section += f"### Hypothesis {i}: {statement}\n"
                if rationale:
                    hypo_section += f"**Rationale:** {rationale}\n\n"
                if approach:
                    hypo_section += f"**Suggested Methodology:** {approach}\n\n"

        # BibTeX Appendix
        bibtex_section = "## Appendix: BibTeX References\n\n```bibtex\n"
        for p in papers[:20]:
            cite_key = f"paper_{p.id.replace(':', '_')}"
            first_author = p.authors[0].split()[-1] if p.authors else "Unknown"
            year = p.year or 2024
            bibtex_section += f"@article{{{first_author}{year}_{p.id[:6]},\n"
            bibtex_section += f"  title = {{{p.title}}},\n"
            bibtex_section += f"  author = {{{' and '.join(p.authors[:3])}}},\n"
            bibtex_section += f"  year = {{{year}}},\n"
            bibtex_section += f"  url = {{{p.url or p.pdf_url}}}\n"
            bibtex_section += "}\n\n"
        bibtex_section += "```\n"

        return f"{header}\n{review_text}\n\n{gaps_section}\n{hypo_section}\n{bibtex_section}"

    def build_latex_report(self, topic: str, review_text: str, papers: List[Paper]) -> str:
        """Converts generated literature review into clean, compile-ready LaTeX."""
        latex = (
            "\\documentclass[11pt,a4paper]{article}\n"
            "\\usepackage[utf8]{inputenc}\n"
            "\\usepackage{hyperref}\n"
            "\\usepackage{booktabs}\n\n"
            f"\\title{{Literature Review: {topic.title()}}}\n"
            "\\author{QORA Autonomous Research Platform}\n"
            "\\date{\\today}\n\n"
            "\\begin{document}\n"
            "\\maketitle\n\n"
        )
        
        # Strip markdown headings for simple latex conversion
        clean_text = review_text.replace("# ", "\\section{").replace("## ", "\\subsection{")
        latex += clean_text + "\n\n"
        latex += "\\end{document}"
        return latex
