from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.modules.ingestion.router import router as ingestion_router

app = FastAPI(
    title="Customer Intelligence Platform",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion_router, prefix="/api/v1")
app.include_router(ingestion_router)  # Keep legacy /ingestion path as well


@app.get("/")
def health_check():
    return {
        "status": "running",
        "service": "Customer Intelligence Platform"
    }