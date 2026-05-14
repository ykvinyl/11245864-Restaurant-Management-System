from fastapi import APIRouter
from src.api.endpoints.reservations import router as reservation_router
from src.api.endpoints.auth import router as auth_router
from src.api.endpoints.analytics import router as analytics_router

api_router = APIRouter()

api_router.include_router(reservation_router, prefix="/reservations", tags=["Reservations"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])