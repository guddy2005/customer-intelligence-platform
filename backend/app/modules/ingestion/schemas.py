# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class MessageIn(BaseModel):
    customer_id: str
    source: str
    message: str
    received_at: Optional[datetime] = None


class IngestionErrorDTO(BaseModel):
    row: int
    field: Optional[str] = None
    error: str
    raw_value: Optional[str] = None


class IngestionSummary(BaseModel):
    total_records: int
    valid_records: int
    rejected_records: int
    duplicate_records: int
    inserted_records: int


class IngestionResponse(BaseModel):
    """
    Response returned immediately when a file is submitted for ingestion.
    For large files the pipeline runs as a background task.
    Poll GET /batches/{batch_id} for live status.
    """
    success: bool
    batch_id: str
    filename: str
    input_type: Optional[str] = "AUTO_DETECT"
    status: str = "PROCESSING"
    domain: Optional[str] = None
    domain_breakdown: Optional[Dict[str, int]] = None
    summary: Optional[IngestionSummary] = None
    errors: Optional[List[IngestionErrorDTO]] = []


class BatchHistoryDTO(BaseModel):
    """
    Represents a single ingestion batch run summary.
    source_domain is the computed aggregate (MULTI_SOURCE, BANKING, etc.)
    input_type is HOW the data entered (SMS, CSV, API, etc.)
    """
    batch_id: str
    filename: str
    input_type: Optional[str] = "UNKNOWN"
    source_domain: Optional[str] = "UNKNOWN"
    total_records: int
    valid_records: int
    rejected_records: int
    duplicate_records: int
    inserted_records: int
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        # Allow extra fields from DB that are not in the schema
        extra = "ignore"


class APIIngestionRequest(BaseModel):
    url: str
    source_name: Optional[str] = "EXTERNAL_API"
    domain_hint: Optional[str] = "AUTO_DETECT"
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    results_key: Optional[str] = None
    timeout: Optional[int] = 15


class DBIngestionRequest(BaseModel):
    host: str
    port: Optional[int] = 3306
    user: str
    password: Optional[str] = ""
    database: str
    query: str
    source_name: Optional[str] = "EXTERNAL_DB"
    domain_hint: Optional[str] = "AUTO_DETECT"


class CDMRecordDTO(BaseModel):
    transaction_id: str
    customer_id: str
    source_domain: str
    source_name: str
    transaction_type: str
    category: str
    subcategory: Optional[str] = None
    transaction_date: str
    amount: float
    currency: str = "INR"
    payment_method: Optional[str] = None
    merchant_or_provider: Optional[str] = None
    location: Optional[str] = None
    status: str = "COMPLETED"
    raw_message: Optional[str] = None
    record_hash: str