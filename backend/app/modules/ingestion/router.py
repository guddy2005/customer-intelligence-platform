from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional, List
from backend.app.modules.ingestion.schemas import MessageIn, IngestionResponse, BatchHistoryDTO
from backend.app.modules.ingestion.service import (
    save_message,
    process_csv_ingestion,
    get_all_batches,
    get_batch_details,
)

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


@router.post("/upload", response_model=IngestionResponse)
async def upload_csv_dataset(
    file: UploadFile = File(...),
    domain_hint: Optional[str] = Form("AUTO_DETECT")
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported for data ingestion.")

    content = await file.read()
    try:
        file_text = content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            file_text = content.decode("latin-1")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read CSV encoding: {str(e)}")

    result = process_csv_ingestion(file_text, file.filename, domain_hint=domain_hint or "AUTO_DETECT")
    return result


@router.get("/batches", response_model=List[BatchHistoryDTO])
def list_batches():
    return get_all_batches()


@router.get("/batches/{batch_id}")
def get_batch(batch_id: str):
    batch = get_batch_details(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch execution record not found.")
    return batch