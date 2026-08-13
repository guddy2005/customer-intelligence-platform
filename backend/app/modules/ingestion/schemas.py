from pydantic import BaseModel
from datetime import datetime


class MessageIn(BaseModel):
    customer_id: str
    source: str
    message: str
    received_at: datetime | None = None