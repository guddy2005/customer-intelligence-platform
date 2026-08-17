# pyrefly: ignore [missing-import]
from fastapi import APIRouter, HTTPException, status, Query
from typing import Optional, List, Dict, Any

from backend.app.modules.processing.schemas import (
    ProcessTextRequest,
    ProcessedRecordDTO,
    BatchProcessRequest,
    BatchProcessResponse,
)
from backend.app.modules.processing.service import (
    process_message_text,
    process_batch_records,
    get_processed_data,
)

router = APIRouter(
    prefix="/processing",
    tags=["Data Processing"]
)


@router.post("/process-text", response_model=ProcessedRecordDTO)
def process_single_text(payload: ProcessTextRequest):
    """
    Applies rule-based intelligence extraction on an incoming text message string.
    Extracts transaction detection, transaction type, amount, category, and merchant.
    """
    try:
        result = process_message_text(text=payload.text, sender=payload.sender)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Processing failed: {str(e)}"
        )


@router.post("/process-batch", response_model=BatchProcessResponse)
def trigger_batch_processing(payload: BatchProcessRequest = BatchProcessRequest()):
    """
    Runs batch chunked processing across stored raw records to extract and persist
    intelligence in `processed_data`.
    """
    try:
        result = process_batch_records(batch_size=payload.batch_size, force=payload.force)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch processing failed: {str(e)}"
        )


@router.get("/records")
def list_processed_records(
    customer_id: Optional[str] = Query(None, description="Filter by customer ID"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """
    Returns paginated processed intelligence records.
    """
    try:
        return get_processed_data(customer_id=customer_id, limit=limit, offset=offset)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch processed records: {str(e)}"
        )
