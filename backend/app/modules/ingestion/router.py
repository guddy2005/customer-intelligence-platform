# pyrefly: ignore [missing-import]
from fastapi import APIRouter, BackgroundTasks, UploadFile, File, Form, HTTPException, status
from typing import Optional, List
import os
import tempfile

from backend.app.modules.ingestion.schemas import (
    MessageIn,
    IngestionResponse,
    BatchHistoryDTO,
    APIIngestionRequest,
    DBIngestionRequest,
)
from backend.app.modules.ingestion.service import (
    save_message,
    process_csv_ingestion,
    run_streaming_pipeline,
    process_api_ingestion,
    process_db_ingestion,
    get_all_batches,
    get_batch_details,
    DEFAULT_BATCH_SIZE,
)
from backend.app.modules.ingestion.connectors.base import (
    ConnectorError,
    ConnectorConnectionError,
    ConnectorFetchError,
    ConnectorDataError,
)

router = APIRouter(
    prefix="/ingestion",
    tags=["Data Ingestion"]
)


@router.post("/message")
def ingest_message(data: MessageIn):
    """
    Ingests a single raw text event message (legacy compatibility).
    """
    message_id = save_message(data)
    return {
        "success": True,
        "message": "Message ingested successfully",
        "message_id": message_id
    }


@router.post("/upload", response_model=IngestionResponse)
async def upload_csv_dataset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    input_type: Optional[str] = Form("AUTO_DETECT"),
    batch_size: Optional[int] = Form(DEFAULT_BATCH_SIZE),
    domain_hint: Optional[str] = Form(None)
):
    """
    Ingests a CSV dataset file using streaming batch processing.

    Pipeline:
        Upload → Save to temp file → Background task:
            CSV Connector (streaming) → SMS Parser / Structured Parser
            → Record-Level Classification → CDM Validation → Deduplication → MySQL

    For large files (SMS-Data.csv, 100k+ records):
    - Returns batch_id immediately (status=PROCESSING)
    - Pipeline runs as a background task
    - Poll GET /batches/{batch_id} for live progress

    input_type options:
        AUTO_DETECT  — system decides (default)
        SMS          — SMS / communication logs (record-level domain classification)
        TRANSACTIONS — structured transaction CSV
        CUSTOMERS    — customer master profile CSV
        JSON         — JSON event stream
        API          — external API data
        DATABASE     — external database query

    batch_size: number of records per processing chunk (default=1000, configurable)
    """
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported for data ingestion."
        )

    # Save uploaded file to a temporary path
    # This allows true streaming — we never hold the full CSV in RAM as a string
    try:
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".csv", prefix="ingestion_upload_")
        try:
            with os.fdopen(tmp_fd, "wb") as tmp_file:
                # Stream file content in chunks to avoid loading 30MB into RAM
                while True:
                    chunk = await file.read(65536)  # 64KB chunks
                    if not chunk:
                        break
                    tmp_file.write(chunk)
        except Exception as write_err:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save uploaded file: {str(write_err)}"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"File upload handling failed: {str(e)}"
        )

    # Resolve batch_id and prepare pipeline
    resolved_batch_size = max(100, min(batch_size or DEFAULT_BATCH_SIZE, 10000))
    resolved_input_type = (input_type or "AUTO_DETECT").upper()

    try:
        batch_id, file_path = process_csv_ingestion(
            file_path=tmp_path,
            filename=file.filename,
            input_type=resolved_input_type,
            batch_size=resolved_batch_size,
            domain_hint=domain_hint
        )
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize ingestion pipeline: {str(e)}"
        )

    # Launch streaming pipeline as a background task
    # The HTTP response returns immediately with batch_id + PROCESSING status
    background_tasks.add_task(
        run_streaming_pipeline,
        file_path=file_path,
        filename=file.filename,
        batch_id=batch_id,
        input_type=resolved_input_type,
        batch_size=resolved_batch_size,
        domain_hint=domain_hint,
        cleanup_file=True,  # Temp file will be deleted after processing
    )

    return IngestionResponse(
        success=True,
        batch_id=batch_id,
        filename=file.filename,
        input_type=resolved_input_type,
        status="PROCESSING",
        domain=None,
        domain_breakdown=None,
        summary=None,
        errors=[]
    )


@router.post("/api-fetch", response_model=IngestionResponse)
def ingest_from_api(payload: APIIngestionRequest):
    """
    Triggers ingestion from an external REST API endpoint using APIConnector.
    """
    try:
        result = process_api_ingestion(
            url=payload.url,
            source_name=payload.source_name or "EXTERNAL_API",
            headers=payload.headers,
            params=payload.params,
            results_key=payload.results_key,
            timeout=payload.timeout or 15,
            domain_hint=payload.domain_hint or "AUTO_DETECT"
        )
        return IngestionResponse(
            success=result.get("success", False),
            batch_id=result["batch_id"],
            filename=result["filename"],
            input_type=result.get("input_type", "API"),
            status=result.get("status", "COMPLETED"),
            domain=result.get("domain"),
            domain_breakdown=result.get("domain_breakdown"),
            summary=result.get("summary"),
            errors=result.get("errors", [])
        )
    except ConnectorConnectionError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to connect to API source: {e.message}")
    except ConnectorFetchError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Failed to fetch data from API endpoint: {e.message}")
    except ConnectorDataError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid API response payload: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"API ingestion failed: {str(e)}")


@router.post("/db-fetch", response_model=IngestionResponse)
def ingest_from_database(payload: DBIngestionRequest):
    """
    Triggers ingestion by querying an external MySQL database using DBConnector.
    """
    try:
        result = process_db_ingestion(
            host=payload.host,
            port=payload.port or 3306,
            user=payload.user,
            password=payload.password,
            database=payload.database,
            query=payload.query,
            source_name=payload.source_name or "EXTERNAL_DB",
            domain_hint=payload.domain_hint or "AUTO_DETECT"
        )
        return IngestionResponse(
            success=result.get("success", False),
            batch_id=result["batch_id"],
            filename=result["filename"],
            input_type=result.get("input_type", "DATABASE"),
            status=result.get("status", "COMPLETED"),
            domain=result.get("domain"),
            domain_breakdown=result.get("domain_breakdown"),
            summary=result.get("summary"),
            errors=result.get("errors", [])
        )
    except ConnectorConnectionError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Database connection error: {e.message}")
    except ConnectorFetchError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database query execution error: {e.message}")
    except ConnectorDataError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=f"Invalid query or data format: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database ingestion failed: {str(e)}")


@router.get("/batches", response_model=List[BatchHistoryDTO])
def list_batches():
    """
    Returns latest ingestion batch runs and summary statistics.
    """
    return get_all_batches()


@router.get("/batches/{batch_id}")
def get_batch(batch_id: str):
    """
    Returns detailed batch execution info including live progress and row-level validation errors.
    Poll this endpoint while status=PROCESSING to get live progress updates.
    """
    batch = get_batch_details(batch_id)
    if not batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch execution record not found."
        )
    return batch