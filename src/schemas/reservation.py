from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ReservationCreate(BaseModel):
    customer_id: int
    table_id: int
    staff_id: int
    date_time: datetime
    guest_count: int
    special_requests: Optional[str] = ""