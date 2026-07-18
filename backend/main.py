from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from models.database import engine, Base
import models.models # Ensure models are loaded for create_all

Base.metadata.create_all(bind=engine)

app = FastAPI(title="QORA Research AI API")

# Setup CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
