# pyrefly: ignore [missing-import]
from pydantic import BaseModel
from typing import List, Optional
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
    success: bool
    batch_id: str
    filename: str
    domain: str
    summary: IngestionSummary
    errors: List[IngestionErrorDTO]


class BatchHistoryDTO(BaseModel):
    batch_id: str
    filename: str
    source_domain: str
    total_records: int
    valid_records: int
    rejected_records: int
    duplicate_records: int
    inserted_records: int
    status: str
    created_at: datetime