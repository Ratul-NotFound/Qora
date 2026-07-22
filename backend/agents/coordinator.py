"""
Coordinator Agent — Orchestrates the entire research pipeline from search to report generation.
Saves session state and papers to PostgreSQL database, with seamless in-memory fallback if DB is offline.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Callable

from models.schemas import AnalyzeRequest, ResearchSession, Paper
from models.database import SessionLocal
from models.models import DbResearchSession, DbPaper
from knowledge.graph import Neo4jGraphHandler
from knowledge.embeddings import EmbeddingsManager
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
        self.graph_handler = Neo4jGraphHandler()
        self.embeddings_manager = EmbeddingsManager()
        
        # In-memory fallback dictionary
        self.in_memory_sessions: Dict[str, ResearchSession] = {}
        self.in_memory_data: Dict[str, dict] = {}

    def create_session(self, topic: str) -> str:
        session_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        # Always populate in-memory fallback
        self.in_memory_sessions[session_id] = ResearchSession(
            id=session_id,
            topic=topic,
            created_at=created_at,
            status="running"
        )
        self.in_memory_data[session_id] = {"papers": [], "intelligence": {}, "report": ""}

        # Attempt PostgreSQL write
        try:
            db = SessionLocal()
            db_session = DbResearchSession(
                id=session_id,
                topic=topic,
                created_at=created_at,
                status="running",
                papers_found=0,
                papers_analyzed=0,
                paper_ids=[]
            )
            db.add(db_session)
            db.commit()
            db.close()
        except Exception as e:
            print(f"[Coordinator] DB Session save fallback to in-memory: {e}")

        return session_id

    def get_session(self, session_id: str) -> Optional[ResearchSession]:
        try:
            db = SessionLocal()
            db_session = db.query(DbResearchSession).filter(DbResearchSession.id == session_id).first()
            if db_session:
                res = ResearchSession(
                    id=db_session.id,
                    topic=db_session.topic,
                    status=db_session.status,
                    papers_found=db_session.papers_found,
                    papers_analyzed=db_session.papers_analyzed,
                    created_at=db_session.created_at,
                    completed_at=db_session.completed_at,
                    review=db_session.review,
                    hypotheses=db_session.hypotheses or [],
                    gaps=db_session.gaps or []
                )
                db.close()
                return res
            db.close()
        except Exception:
            pass

        return self.in_memory_sessions.get(session_id)

    def get_session_data(self, session_id: str) -> Optional[dict]:
        try:
            db = SessionLocal()
            db_session = db.query(DbResearchSession).filter(DbResearchSession.id == session_id).first()
            if db_session:
                paper_ids = db_session.paper_ids or []
                db_papers = db.query(DbPaper).filter(DbPaper.id.in_(paper_ids)).all() if paper_ids else []
                
                papers = [
                    Paper(
                        id=p.id,
                        title=p.title,
                        authors=p.authors or [],
                        abstract=p.abstract or "",
                        year=p.year,
                        source=p.source,
                        url=p.url,
                        pdf_url=p.pdf_url,
                        citations=p.citations,
                        doi=p.doi,
                        keywords=p.keywords or [],
                        summary=p.summary or "",
                        key_findings=p.key_findings or [],
                        methods=p.methods or [],
                        datasets=p.datasets or [],
                        research_gaps=p.research_gaps or [],
                        relevance_score=p.relevance_score or 0.0
                    )
                    for p in db_papers
                ]
                
                res = {
                    "papers": papers,
                    "report": db_session.review,
                    "intelligence": {
                        "gaps": [{"gap": g, "description": "", "severity": "medium", "related_papers": 1} for g in (db_session.gaps or [])] 
                                if isinstance(db_session.gaps, list) and db_session.gaps and isinstance(db_session.gaps[0], str) 
                                else (db_session.gaps or []),
                        "hypotheses": [{"hypothesis": h, "rationale": "", "approach": "", "novelty": "medium", "feasibility": "medium", "impact": "medium"} for h in (db_session.hypotheses or [])]
                                if isinstance(db_session.hypotheses, list) and db_session.hypotheses and isinstance(db_session.hypotheses[0], str)
                                else (db_session.hypotheses or [])
                    }
                }
                db.close()
                return res
            db.close()
        except Exception:
            pass

        return self.in_memory_data.get(session_id)

    async def run_full_research_pipeline(
        self, 
        session_id: str, 
        request: AnalyzeRequest,
        on_progress: Optional[Callable] = None
    ):
        """Runs the complete autonomous research pipeline."""
        session = self.in_memory_sessions.get(session_id)

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
            
            # Optional: Trace citations for depth > 1
            if request.depth > 1:
                papers = await self.search_agent.trace_citations(
                    papers, depth=request.depth-1, on_progress=on_progress
                )

            if session:
                session.papers_found = len(papers)
            if session_id in self.in_memory_data:
                self.in_memory_data[session_id]["papers"] = papers

            # Attempt DB write for discovered papers
            try:
                db = SessionLocal()
                db_session = db.query(DbResearchSession).filter(DbResearchSession.id == session_id).first()
                if db_session:
                    paper_ids = []
                    for paper in papers:
                        paper_ids.append(paper.id)
                        db_paper = db.query(DbPaper).filter(DbPaper.id == paper.id).first()
                        if not db_paper:
                            db_paper = DbPaper(
                                id=paper.id,
                                title=paper.title,
                                authors=paper.authors,
                                abstract=paper.abstract,
                                year=paper.year,
                                source=paper.source,
                                url=paper.url,
                                pdf_url=paper.pdf_url,
                                citations=paper.citations,
                                doi=paper.doi,
                                keywords=paper.keywords
                            )
                            db.add(db_paper)
                    db_session.papers_found = len(papers)
                    db_session.paper_ids = paper_ids
                    db.commit()
                db.close()
            except Exception as dbe:
                print(f"[Coordinator] DB save papers error: {dbe}")

            # 2. Deep Reading & Analysis
            analyzed_papers = await self.reader_agent.analyze_papers(
                papers, request.topic, on_progress=on_progress
            )
            
            if session:
                session.papers_analyzed = len(analyzed_papers)
            if session_id in self.in_memory_data:
                self.in_memory_data[session_id]["papers"] = analyzed_papers

            try:
                db = SessionLocal()
                db_session = db.query(DbResearchSession).filter(DbResearchSession.id == session_id).first()
                if db_session:
                    for paper in analyzed_papers:
                        db_paper = db.query(DbPaper).filter(DbPaper.id == paper.id).first()
                        if db_paper:
                            db_paper.summary = paper.summary
                            db_paper.key_findings = paper.key_findings
                            db_paper.methods = paper.methods
                            db_paper.datasets = paper.datasets
                            db_paper.research_gaps = paper.research_gaps
                            db_paper.relevance_score = paper.relevance_score
                    db_session.papers_analyzed = len(analyzed_papers)
                    db.commit()
                db.close()
            except Exception as dbe:
                print(f"[Coordinator] DB save analysis error: {dbe}")
            
            top_papers = [p for p in analyzed_papers if p.relevance_score >= 0.6]
            if not top_papers:
                top_papers = analyzed_papers[:20]  # Fallback

            # 3. Intelligence Synthesis (Gaps, Trends, Hypotheses)
            intelligence = await self.analyst_agent.analyze(
                top_papers, request.topic, on_progress=on_progress
            )
            
            if session_id in self.in_memory_data:
                self.in_memory_data[session_id]["intelligence"] = intelligence

            if session:
                session.gaps = [g.get("gap", "") for g in intelligence.get("gaps", [])[:3]]
                session.hypotheses = [h.get("hypothesis", "") for h in intelligence.get("hypotheses", [])[:3]]

            # Save graph to Neo4j
            try:
                self.graph_handler.save_session_graph(session_id, top_papers, intelligence)
            except Exception as ge:
                print(f"[Coordinator] Neo4j graph save failed: {ge}")

            # Save vectors to Weaviate
            try:
                self.embeddings_manager.index_papers(top_papers)
            except Exception as ve:
                print(f"[Coordinator] Weaviate vector indexing failed: {ve}")

            # 4. Report Generation
            report = await self.writer_agent.write_literature_review(
                request.topic, top_papers, intelligence, on_progress=on_progress
            )
            
            if session_id in self.in_memory_data:
                self.in_memory_data[session_id]["report"] = report

            if session:
                session.review = report
                session.status = "completed"
                session.completed_at = datetime.utcnow().isoformat()

            try:
                db = SessionLocal()
                db_session = db.query(DbResearchSession).filter(DbResearchSession.id == session_id).first()
                if db_session:
                    db_session.review = report
                    db_session.status = "completed"
                    db_session.completed_at = datetime.utcnow().isoformat()
                    db.commit()
                db.close()
            except Exception as dbe:
                print(f"[Coordinator] DB save report error: {dbe}")

            if on_progress:
                await on_progress("Analysis complete", 1.0)

        except Exception as e:
            print(f"[Coordinator] Pipeline failed for session {session_id}: {e}")
            if session:
                session.status = "failed"
            if on_progress:
                await on_progress(f"Pipeline failed: {str(e)}", 1.0)

    def list_sessions(self) -> List[ResearchSession]:
        """Return all sessions from DB + in-memory."""
        sessions = []
        seen_ids = set()

        # Try DB first
        try:
            db = SessionLocal()
            db_sessions = db.query(DbResearchSession).order_by(DbResearchSession.created_at.desc()).limit(50).all()
            for ds in db_sessions:
                seen_ids.add(ds.id)
                sessions.append(ResearchSession(
                    id=ds.id,
                    topic=ds.topic,
                    status=ds.status,
                    papers_found=ds.papers_found,
                    papers_analyzed=ds.papers_analyzed,
                    created_at=ds.created_at,
                    completed_at=ds.completed_at or "",
                ))
            db.close()
        except Exception:
            pass

        # Add in-memory sessions not in DB
        for sid, s in self.in_memory_sessions.items():
            if sid not in seen_ids:
                sessions.append(s)

        return sessions

    def delete_session(self, session_id: str) -> bool:
        """Delete a session from DB and in-memory."""
        deleted = False

        if session_id in self.in_memory_sessions:
            del self.in_memory_sessions[session_id]
            deleted = True
        if session_id in self.in_memory_data:
            del self.in_memory_data[session_id]

        try:
            db = SessionLocal()
            db_session = db.query(DbResearchSession).filter(DbResearchSession.id == session_id).first()
            if db_session:
                db.delete(db_session)
                db.commit()
                deleted = True
            db.close()
        except Exception:
            pass

        return deleted

