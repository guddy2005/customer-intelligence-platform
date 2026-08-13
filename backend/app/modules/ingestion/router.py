from fastapi import APIRouter
from backend.app.modules.ingestion.schemas import MessageIn
from backend.app.modules.ingestion.service import save_message

router = APIRouter(
    prefix="/ingestion",
    tags=["Data Ingestion"]
)


@router.post("/message")
def ingest_message(data: MessageIn):
    message_id = save_message(data)

    return {
        "success": True,
        "message": "Message ingested successfully",
        "message_id": message_id
    }