from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# Schema kiểm tra dữ liệu đầu vào khi Thêm mới Khách hàng
class CustomerCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    points: int = 0
    is_active: bool = True

# Schema kiểm tra dữ liệu đầu vào khi Cập nhật Khách hàng
class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    points: Optional[int] = None
    is_active: Optional[bool] = None

@router.get("/")
async def get_all_customers():
    """API lấy toàn bộ danh sách Khách hàng từ Database"""
    try:
        from src.core.db import db_cursor
        with db_cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT 
                    CustomerID as id, 
                    CustomerName as name, 
                    PhoneNumber as phone, 
                    Email as email, 
                    Address as address, 
                    JoinDate as joinDate, 
                    LoyaltyPoints as points, 
                    IsActive as is_active 
                FROM Customers
                ORDER BY CustomerID DESC
            """)
            customers = cur.fetchall()
            # Xử lý định dạng ngày tháng để Frontend dễ đọc
            for c in customers:
                c['joinDate'] = str(c['joinDate']) if c['joinDate'] else "N/A"
        return customers
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def create_customer(customer: CustomerCreate):
    """API Thêm mới Khách hàng"""
    try:
        from src.core.db import db_cursor
        with db_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO Customers (CustomerName, PhoneNumber, Email, Address, LoyaltyPoints, IsActive)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (customer.name, customer.phone, customer.email, customer.address, customer.points, customer.is_active))
        return {"status": "success", "message": "Customer created successfully"}
    except Exception as e:
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=400, detail="Phone number or Email already exists!")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{customer_id}")
async def update_customer(customer_id: int, customer: CustomerUpdate):
    """API Cập nhật thông tin hoặc Khóa/Mở Khách hàng"""
    try:
        from src.core.db import db_cursor
        with db_cursor(commit=True) as cur:
            fields = []
            values = []
            
            if customer.name is not None:
                fields.append("CustomerName = %s")
                values.append(customer.name)
            if customer.phone is not None:
                fields.append("PhoneNumber = %s")
                values.append(customer.phone)
            if customer.email is not None:
                fields.append("Email = %s")
                values.append(customer.email)
            if customer.address is not None:
                fields.append("Address = %s")
                values.append(customer.address)
            if customer.points is not None:
                fields.append("LoyaltyPoints = %s")
                values.append(customer.points)
            if customer.is_active is not None:
                fields.append("IsActive = %s")
                values.append(customer.is_active)
            
            if not fields:
                return {"status": "success", "message": "No changes requested"}
            
            values.append(customer_id)
            query = f"UPDATE Customers SET {', '.join(fields)} WHERE CustomerID = %s"
            cur.execute(query, tuple(values))
            
        return {"status": "success", "message": "Customer updated successfully"}
    except Exception as e:
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=400, detail="Phone number or Email already exists in another account!")
        raise HTTPException(status_code=500, detail=str(e))