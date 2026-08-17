# pyrefly: ignore [missing-import]
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class SingleClassificationRequest(BaseModel):
    transaction_id: Optional[str] = None
    customer_id: Optional[str] = None
    source_domain: Optional[str] = None
    source_name: Optional[str] = None
    transaction_type: Optional[str] = None
    merchant_or_provider: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = "INR"
    payment_method: Optional[str] = None
    location: Optional[str] = None


class ClassificationResultDTO(BaseModel):
    transaction_id: Optional[str] = None
    customer_id: Optional[str] = None
    source_domain: str
    source_name: str
    transaction_type: str
    category: str
    subcategory: Optional[str] = None
    confidence: float


class BatchClassificationRequest(BaseModel):
    limit: Optional[int] = Field(default=100, ge=1, le=1000)
    force: Optional[bool] = False  # If True, reclassifies already classified records


class BatchClassificationResponse(BaseModel):
    success: bool
    total_records: int
    classified_records: int
    unknown_records: int
    failed_records: int
