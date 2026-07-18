from sqlalchemy import Column, String, Integer, Float, Text, JSON
from models.database import Base

class DbPaper(Base):
    __tablename__ = "papers"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    authors = Column(JSON, default=[])
    abstract = Column(Text, default="")
    year = Column(Integer, nullable=True)
    source = Column(String, default="")
    url = Column(String, default="")
    pdf_url = Column(String, default="")
    citations = Column(Integer, default=0)
    doi = Column(String, default="")
    keywords = Column(JSON, default=[])
    
    # AI Analysis Fields
    summary = Column(Text, default="")
    key_findings = Column(JSON, default=[])
    methods = Column(JSON, default=[])
    datasets = Column(JSON, default=[])
    research_gaps = Column(JSON, default=[])
    relevance_score = Column(Float, default=0.0)

class DbResearchSession(Base):
    __tablename__ = "research_sessions"

    id = Column(String, primary_key=True, index=True)
    topic = Column(String, nullable=False)
    status = Column(String, default="pending")
    papers_found = Column(Integer, default=0)
    papers_analyzed = Column(Integer, default=0)
    created_at = Column(String, default="")
    completed_at = Column(String, default="")
    review = Column(Text, default="")
    hypotheses = Column(JSON, default=[])
    gaps = Column(JSON, default=[])
    paper_ids = Column(JSON, default=[])
