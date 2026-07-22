from fastapi import APIRouter, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import PlainTextResponse
from typing import Dict, List
import json

from config import settings
from models.schemas import AnalyzeRequest, ResearchSession
from agents.coordinator import CoordinatorAgent

router = APIRouter()
coordinator = CoordinatorAgent(settings)


# Connection manager for real-time updates
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def broadcast_progress(self, session_id: str, message: str, progress: float):
        if session_id in self.active_connections:
            payload = json.dumps({
                "type": "progress",
                "message": message,
                "progress": progress
            })
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_text(payload)
                except Exception:
                    pass

manager = ConnectionManager()


# ───────────────────────── Core Endpoints ─────────────────────────

@router.get("/")
def read_root():
    return {"status": "online", "system": "QORA Research AI", "version": "2.0.0"}


@router.get("/api/health")
def health_check():
    """System health check — reports connectivity status for all services."""
    db_status = "offline"
    try:
        from models.database import SessionLocal
        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db.close()
        db_status = "connected"
    except Exception:
        pass

    return {
        "status": "online",
        "version": "2.0.0",
        "database": db_status,
        "llm": {
            "model": settings.llm_model,
            "heavy_model": settings.llm_heavy_model,
            "base_url": settings.llm_base_url,
            "key_configured": bool(settings.llm_api_key),
        },
        "sources": {
            "semantic_scholar": bool(settings.semantic_scholar_api_key),
            "ncbi_pubmed": bool(settings.ncbi_api_key),
            "core": bool(settings.core_api_key),
            "arxiv": True,
            "openalex": True,
        }
    }


# ───────────────────────── Research Pipeline ─────────────────────────

@router.post("/api/research", response_model=ResearchSession)
async def start_research(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    session_id = coordinator.create_session(request.topic)
    
    async def progress_callback(message: str, progress: float):
        await manager.broadcast_progress(session_id, message, progress)
        
    background_tasks.add_task(
        coordinator.run_full_research_pipeline,
        session_id,
        request,
        progress_callback
    )
    
    return coordinator.get_session(session_id)


@router.get("/api/research/{session_id}", response_model=ResearchSession)
def get_session_status(session_id: str):
    session = coordinator.get_session(session_id)
    if not session:
        return {"error": "Session not found"}
    return session


@router.get("/api/research/{session_id}/results")
def get_session_results(session_id: str):
    session = coordinator.get_session(session_id)
    if not session:
        return {"error": "Session not found"}
        
    data = coordinator.get_session_data(session_id)
    if not data:
        return {"session": session.model_dump(), "papers": [], "intelligence": {}, "report": ""}

    return {
        "session": session.model_dump(),
        "papers": [p.model_dump() for p in data.get("papers", [])],
        "intelligence": data.get("intelligence", {}),
        "report": data.get("report", "")
    }


# ───────────────────────── Session Management ─────────────────────────

@router.get("/api/sessions")
def list_sessions():
    """List all past research sessions."""
    sessions = coordinator.list_sessions()
    return [s.model_dump() for s in sessions]


@router.delete("/api/research/{session_id}")
def delete_session(session_id: str):
    """Delete a research session."""
    success = coordinator.delete_session(session_id)
    if success:
        return {"status": "deleted", "session_id": session_id}
    return {"error": "Session not found"}


# ───────────────────────── Export Endpoints ─────────────────────────

@router.get("/api/research/{session_id}/export/markdown")
def export_markdown(session_id: str):
    """Export the full literature review as plain Markdown text."""
    data = coordinator.get_session_data(session_id)
    if not data:
        return PlainTextResponse("Session not found", status_code=404)
    report = data.get("report", "")
    return PlainTextResponse(report, media_type="text/markdown")


@router.get("/api/research/{session_id}/export/bibtex")
def export_bibtex(session_id: str):
    """Export all session papers as BibTeX entries."""
    data = coordinator.get_session_data(session_id)
    if not data:
        return PlainTextResponse("Session not found", status_code=404)

    papers = data.get("papers", [])
    bibtex_entries = []
    for p in papers:
        first_author = p.authors[0].split()[-1] if p.authors else "Unknown"
        year = p.year or 2024
        cite_key = f"{first_author}{year}_{p.id[:8].replace(':', '_')}"
        entry = f"@article{{{cite_key},\n"
        entry += f"  title = {{{p.title}}},\n"
        entry += f"  author = {{{' and '.join(p.authors[:5])}}},\n"
        entry += f"  year = {{{year}}},\n"
        if p.doi:
            entry += f"  doi = {{{p.doi}}},\n"
        entry += f"  url = {{{p.url or p.pdf_url}}}\n"
        entry += "}\n"
        bibtex_entries.append(entry)

    bibtex_text = "\n".join(bibtex_entries)
    return PlainTextResponse(bibtex_text, media_type="application/x-bibtex")


# ───────────────────────── WebSocket ─────────────────────────

@router.websocket("/ws/research/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
