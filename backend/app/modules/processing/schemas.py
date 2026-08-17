# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class ProcessTextRequest(BaseModel):
    text: str = Field(..., description="Raw message or text to extract intelligence from")
    sender: Optional[str] = Field(None, description="Optional sender header or identifier")
    customer_id: Optional[str] = Field(None, description="Optional customer ID or phone number")


class ProcessedRecordDTO(BaseModel):
    transaction_detected: bool
    transaction_type: Optional[str] = None
    amount: float = 0.0
    category: str = "UNKNOWN"
    subcategory: Optional[str] = None
    merchant_or_provider: Optional[str] = None
    confidence: float = 1.0
    raw_message: Optional[str] = None


class BatchProcessRequest(BaseModel):
    batch_size: int = Field(1000, ge=10, le=10000, description="Number of records per processing chunk")
    force: bool = Field(False, description="Whether to reprocess already processed records")


class BatchProcessResponse(BaseModel):
    success: bool
    total_processed: int
    transactions_detected: int
    non_transactions: int
    intelligence_created: int = 0
    intelligence_skipped: int = 0
    intelligence_failed: int = 0
    reconciliation_passed: bool = True
    duration_seconds: float
    batch_size: int

