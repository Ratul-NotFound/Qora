from fastapi import FastAPI, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, List
import asyncio
import json

from config import settings
from models.schemas import AnalyzeRequest, ResearchSession
from agents.coordinator import CoordinatorAgent

app = FastAPI(title="QORA Research AI API")

# Setup CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/")
def read_root():
    return {"status": "online", "system": "QORA Research AI"}


@app.post("/api/research", response_model=ResearchSession)
async def start_research(request: AnalyzeRequest, background_tasks: BackgroundTasks):
    """Starts an autonomous research session."""
    session_id = coordinator.create_session(request.topic)
    
    # Run the pipeline in the background
    async def progress_callback(message: str, progress: float):
        await manager.broadcast_progress(session_id, message, progress)
        
    background_tasks.add_task(
        coordinator.run_full_research_pipeline,
        session_id,
        request,
        progress_callback
    )
    
    return coordinator.get_session(session_id)


@app.get("/api/research/{session_id}", response_model=ResearchSession)
def get_session_status(session_id: str):
    """Get the current status of a research session."""
    session = coordinator.get_session(session_id)
    if not session:
        return {"error": "Session not found"}
    return session


@app.get("/api/research/{session_id}/results")
def get_session_results(session_id: str):
    """Get the full results of a research session."""
    session = coordinator.get_session(session_id)
    if not session:
        return {"error": "Session not found"}
        
    data = coordinator.get_session_data(session_id)
    return {
        "session": session.model_dump(),
        "papers": [p.model_dump() for p in data.get("papers", [])],
        "intelligence": data.get("intelligence", {}),
        "report": data.get("report", "")
    }


@app.websocket("/ws/research/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket for real-time progress updates."""
    await manager.connect(websocket, session_id)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
