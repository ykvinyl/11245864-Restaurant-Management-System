from pydantic import BaseModel
from typing import Optional

class InvoiceCreate(BaseModel):
    order_id: int
    payment_method: str = "Cash" 
    tax_rate: Optional[float] = 0.08
    discount_amount: Optional[float] = 0.0

class InvoiceResponse(BaseModel):
    invoice_id: int
    order_id: int
    total_amount: float
    payment_status: str