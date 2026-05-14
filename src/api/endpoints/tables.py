from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class TableUpdate(BaseModel):
    status: Optional[str] = None
    capacity: Optional[int] = None
    location: Optional[str] = None

@router.get("/")
async def get_all_tables():
    try:
        from src.core.db import db_cursor
        with db_cursor(dictionary=True) as cur:
            # SQL: Chỉ lấy thông tin của ĐƠN HÀNG MỚI NHẤT đang mở (open, preparing, served)
            cur.execute("""
                SELECT 
                    t.TableID as id, 
                    t.Capacity as capacity, 
                    t.Location as location, 
                    LOWER(t.Status) as status,
                    
                    (SELECT c.CustomerName 
                     FROM Orders o 
                     LEFT JOIN Customers c ON o.CustomerID = c.CustomerID 
                     WHERE o.TableID = t.TableID AND o.Status IN ('open', 'preparing', 'served')
                     ORDER BY o.OrderTime DESC LIMIT 1) as current_customer,
                     
                    (SELECT SUM(od.Quantity * od.UnitPrice) 
                     FROM OrderDetails od 
                     WHERE od.OrderID = (
                         SELECT OrderID FROM Orders 
                         WHERE TableID = t.TableID AND Status IN ('open', 'preparing', 'served')
                         ORDER BY OrderTime DESC LIMIT 1
                     )) as current_total,
                     
                    (SELECT DATE_FORMAT(o3.OrderTime, '%H:%i') 
                     FROM Orders o3
                     WHERE o3.TableID = t.TableID AND o3.Status IN ('open', 'preparing', 'served')
                     ORDER BY o3.OrderTime DESC LIMIT 1) as `current_time`
                     
                FROM Tables t
                ORDER BY t.TableID ASC
                LIMIT 15
            """)
            tables = cur.fetchall()
            
            for t in tables:
                t['current_total'] = float(t['current_total']) if t['current_total'] else 0.0
                
                if t['status'] == 'available':
                    t['current_customer'] = None
                    t['current_time'] = None
                    t['current_total'] = 0.0
                    
                elif t['status'] == 'reserved':
                    t['current_customer'] = t['current_customer'] or "Reserved Guest"
                    t['current_time'] = t['current_time'] or "Upcoming"
                    t['current_total'] = 0.0
                    
                else: 
                    # TRẠNG THÁI OCCUPIED (Đang phục vụ)
                    t['current_customer'] = t['current_customer'] or "Walk-in Guest"
                    t['current_time'] = t['current_time'] or "--:--"
                    
        return list(tables)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{table_id}")
async def update_table_status(table_id: int, table_data: TableUpdate):
    try:
        from src.core.db import db_cursor
        with db_cursor(commit=True) as cur:
            fields = []
            values = []
            
            if table_data.status is not None:
                fields.append("Status = %s")
                values.append(table_data.status)
                
                # ==================================================
                # CHỐT CHẶN BẢO MẬT: DIỆT HỒN MA BILL CŨ
                # Nếu lệnh yêu cầu dọn bàn về "available", 
                # Tự động ĐÓNG tất cả order đang treo của bàn này!
                # ==================================================
                if table_data.status.lower() == 'available':
                    cur.execute("""
                        UPDATE Orders 
                        SET Status = 'closed' 
                        WHERE TableID = %s AND Status != 'closed'
                    """, (table_id,))
            
            if table_data.capacity is not None:
                fields.append("Capacity = %s")
                values.append(table_data.capacity)
            if table_data.location is not None:
                fields.append("Location = %s")
                values.append(table_data.location)
            
            if not fields: 
                return {"status": "success"}
                
            values.append(table_id)
            cur.execute(f"UPDATE Tables SET {', '.join(fields)} WHERE TableID = %s", tuple(values))
            
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))