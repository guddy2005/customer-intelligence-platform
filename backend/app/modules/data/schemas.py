# pyrefly: ignore [missing-import]
from pydantic import BaseModel # type: ignore
from typing import Optional, List, Dict, Any
from datetime import datetime


class TransactionDetailDTO(BaseModel):
    transaction_id: str
    raw_record_id: Optional[int] = None
    batch_id: Optional[str] = None
    customer_id: str
    source_domain: str
    source_name: str
    transaction_type: str
    category: str
    subcategory: Optional[str] = None
    transaction_date: datetime
    amount: float
    currency: str = "INR"
    payment_method: Optional[str] = None
    merchant_or_provider: Optional[str] = None
    location: Optional[str] = None
    status: str = "COMPLETED"
    raw_message: Optional[str] = None
    classification_confidence: Optional[float] = None
    classified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None


class PaginatedTransactionsResponse(BaseModel):
    total_count: int
    limit: int
    offset: int
    records: List[TransactionDetailDTO]
