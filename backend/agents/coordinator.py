"""
Coordinator Agent — Orchestrates the entire research pipeline from search to report generation.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Callable
from models.schemas import SearchRequest, AnalyzeRequest, ReviewRequest, ResearchSession, Paper
from agents.search_agent import SearchAgent
from agents.reader_agent import ReaderAgent
from agents.analyst_agent import AnalystAgent
from agents.writer_agent import WriterAgent


class CoordinatorAgent:
    def __init__(self, settings):
        self.settings = settings
        self.search_agent = SearchAgent(settings)
        self.reader_agent = ReaderAgent(settings)
        self.analyst_agent = AnalystAgent(settings)
        self.writer_agent = WriterAgent(settings)
        
        # In-memory storage for active sessions (in a real app, use DB/Redis)
        self.active_sessions: Dict[str, ResearchSession] = {}
        self.session_data: Dict[str, dict] = {}

    def create_session(self, topic: str) -> str:
        session_id = str(uuid.uuid4())
        self.active_sessions[session_id] = ResearchSession(
            id=session_id,
            topic=topic,
            created_at=datetime.utcnow().isoformat(),
            status="running"
        )
        self.session_data[session_id] = {
            "papers": [],
            "intelligence": {},
            "report": ""
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[ResearchSession]:
        return self.active_sessions.get(session_id)
        
    def get_session_data(self, session_id: str) -> Optional[dict]:
        return self.session_data.get(session_id)

    async def run_full_research_pipeline(
        self, 
        session_id: str, 
        request: AnalyzeRequest,
        on_progress: Optional[Callable] = None
    ):
        """Runs the complete autonomous research pipeline."""
        session = self.active_sessions.get(session_id)
        if not session:
            return

        try:
            # 1. Search & Discovery
            papers = await self.search_agent.search(
                query=request.topic,
                enabled_sources=request.sources,
                max_per_source=request.max_papers // max(1, len(request.sources)),
                on_progress=on_progress
            )
            
            # Quick relevance filter before heavy analysis
            papers = await self.reader_agent.quick_relevance_filter(papers, request.topic)
            session.papers_found = len(papers)
            self.session_data[session_id]["papers"] = papers
            
            # Optional: Trace citations for depth > 1
            if request.depth > 1:
                papers = await self.search_agent.trace_citations(
                    papers, depth=request.depth-1, on_progress=on_progress
                )
                session.papers_found = len(papers)
                self.session_data[session_id]["papers"] = papers

            # 2. Deep Reading & Analysis
            analyzed_papers = await self.reader_agent.analyze_papers(
                papers, request.topic, on_progress=on_progress
            )
            session.papers_analyzed = len(analyzed_papers)
            self.session_data[session_id]["papers"] = analyzed_papers
            
            # Filter out low relevance after deep analysis
            top_papers = [p for p in analyzed_papers if p.relevance_score >= 0.6]
            if not top_papers:
                top_papers = analyzed_papers[:20]  # Fallback

            # 3. Intelligence Synthesis (Gaps, Trends, Hypotheses)
            intelligence = await self.analyst_agent.analyze(
                top_papers, request.topic, on_progress=on_progress
            )
            self.session_data[session_id]["intelligence"] = intelligence
            session.gaps = [g.get("gap", "") for g in intelligence.get("gaps", [])[:3]]
            session.hypotheses = [h.get("hypothesis", "") for h in intelligence.get("hypotheses", [])[:3]]

            # 4. Report Generation
            report = await self.writer_agent.write_literature_review(
                request.topic, top_papers, intelligence, on_progress=on_progress
            )
            self.session_data[session_id]["report"] = report
            session.review = report

            session.status = "completed"
            session.completed_at = datetime.utcnow().isoformat()

        except Exception as e:
            print(f"[Coordinator] Pipeline failed for session {session_id}: {e}")
            session.status = "failed"
            if on_progress:
                await on_progress(f"❌ Pipeline failed: {str(e)}", 1.0)
