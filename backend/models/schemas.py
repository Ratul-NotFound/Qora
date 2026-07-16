from pydantic import BaseModel
from typing import Optional, List


class Paper(BaseModel):
    id: str
    title: str
    authors: List[str] = []
    abstract: str = ""
    year: Optional[int] = None
    source: str = ""
    url: str = ""
    pdf_url: str = ""
    citations: int = 0
    doi: str = ""
    keywords: List[str] = []
    # AI-generated fields
    summary: str = ""
    key_findings: List[str] = []
    methods: List[str] = []
    datasets: List[str] = []
    research_gaps: List[str] = []
    relevance_score: float = 0.0


class SearchRequest(BaseModel):
    query: str
    max_results: int = 20
    use_arxiv: bool = True
    use_semantic_scholar: bool = True
    use_pubmed: bool = True
    use_openalex: bool = True
    year_from: Optional[int] = None
    year_to: Optional[int] = None


class AnalyzeRequest(BaseModel):
    topic: str
    depth: int = 2  # citation traversal depth
    max_papers: int = 50
    sources: List[str] = ["arxiv", "semantic_scholar", "pubmed", "openalex"]


class ReviewRequest(BaseModel):
    papers: List[Paper]
    topic: str
    style: str = "academic"  # academic, plain, technical


class ResearchSession(BaseModel):
    id: str
    topic: str
    status: str = "pending"
    papers_found: int = 0
    papers_analyzed: int = 0
    created_at: str = ""
    completed_at: str = ""
    review: str = ""
    hypotheses: List[str] = []
    gaps: List[str] = []


class UpdateMessage(BaseModel):
    type: str  # progress, paper_found, analysis_done, review_ready, error
    session_id: str
    message: str = ""
    data: dict = {}
    progress: float = 0.0  # 0.0 to 1.0
