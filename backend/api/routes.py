from fastapi import APIRouter, BackgroundTasks, WebSocket, WebSocketDisconnect
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

@router.get("/")
def read_root():
    return {"status": "online", "system": "QORA Research AI"}

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
    return {
        "session": session.model_dump(),
        "papers": [p.model_dump() for p in data.get("papers", [])],
        "intelligence": data.get("intelligence", {}),
        "report": data.get("report", "")
    }

@router.websocket("/ws/research/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
