from fastapi import FastAPI

from backend.app.modules.ingestion.router import router as ingestion_router


app = FastAPI(
    title="Customer Intelligence Platform",
    version="1.0.0"
)


app.include_router(ingestion_router)


@app.get("/")
def health_check():
    return {
        "status": "running",
        "service": "Customer Intelligence Platform"
    }