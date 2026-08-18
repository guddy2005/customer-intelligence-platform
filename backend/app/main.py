# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware

from contextlib import asynccontextmanager
from backend.app.modules.ingestion.router import router as ingestion_router
from backend.app.modules.classification.router import router as classification_router
from backend.app.modules.analytics.router import router as analytics_router
from backend.app.modules.audience.router import router as audience_router
from backend.app.database.init_db import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-initialize database tables and schema migrations on server start
    try:
        init_db()
    except Exception as e:
        print(f"Warning: Database initialization on startup encountered: {e}")
    yield


app = FastAPI(
    title="Customer Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan
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
app.include_router(classification_router, prefix="/api/v1")
app.include_router(classification_router)
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(analytics_router)
app.include_router(audience_router, prefix="/api/v1")
app.include_router(audience_router)



@app.get("/")
def health_check():
    return {
        "status": "running",
        "service": "Customer Intelligence Platform"
    }