from fastapi import APIRouter, HTTPException
from src.schemas.reservation import ReservationCreate
from src.models.reservations import Reservation 

router = APIRouter()

@router.post("/create")
async def create_reservation(req: ReservationCreate):
    res = Reservation(
        customer_id=req.customer_id,
        table_id=req.table_id,
        staff_id=req.staff_id,
        date_time=req.date_time,
        guest_count=req.guest_count,
        special_requests=req.special_requests
    )
    
    rid, message = res.save()
    
    if rid == -1:
        raise HTTPException(status_code=400, detail=message)
        
    return {"status": "success", "reservation_id": rid, "message": message}