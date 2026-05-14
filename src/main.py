from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.router import api_router
from src.api.endpoints.customers import router as customers_router 
from src.api.endpoints.tables import router as tables_router
from src.api.endpoints.menu import router as menu_router
from src.api.endpoints.orders import router as orders_router
from src.api.endpoints.invoices import router as invoices_router

# 1. Khởi tạo biến "app"
app = FastAPI(
    title="Advanced Restaurant API",
    description="Hệ thống quản lý nhà hàng: FastAPI + MySQL Procedures",
    version="1.0.0"
)

# 2. Cấu hình bảo mật CORS (Luôn phải đặt ngay sau khi khai báo app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Cho phép tất cả giao diện Frontend gọi API
    allow_credentials=True,
    allow_methods=["*"], # Cho phép GET, POST, PUT, DELETE
    allow_headers=["*"], 
)

# 3. Gắn các đường dẫn API vào app
app.include_router(api_router, prefix="/api/v1")
app.include_router(customers_router, prefix="/api/v1/customers", tags=["Customers"])
app.include_router(tables_router, prefix="/api/v1/tables", tags=["Tables"])
app.include_router(menu_router, prefix="/api/v1/menu", tags=["Menu"])
app.include_router(orders_router, prefix="/api/v1/orders", tags=["Orders"])
app.include_router(invoices_router, prefix="/api/v1/invoices", tags=["Invoices"])

# 4. Tạo đường dẫn gốc để test Server
@app.get("/")
async def root():
    return {"message": "Server is running perfectly!"}