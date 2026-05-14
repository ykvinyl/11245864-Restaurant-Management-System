from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter()

# ==========================================
# SCHEMAS (Định nghĩa cấu trúc dữ liệu)
# ==========================================

class OrderItemSchema(BaseModel):
    dish_id: int
    quantity: int
    unit_price: float
    notes: Optional[str] = ""

class OrderCreateSchema(BaseModel):
    table_id: int
    customer_id: Optional[int] = None 
    staff_id: int = 1  
    items: List[OrderItemSchema]

class PartialPayment(BaseModel):
    method: str  
    amount: float

class CheckoutSchema(BaseModel):
    table_id: int
    customer_id: Optional[int] = None 
    payments: List[PartialPayment]
    discount_amount: float = 0.0
    service_charge: float = 0.0


# ==========================================
# API ENDPOINTS
# ==========================================

@router.post("/kitchen")
async def send_to_kitchen(order_data: OrderCreateSchema):
    """Lưu đơn hàng vào DB: Tạo Orders và OrderDetails"""
    try:
        from src.core.db import db_cursor
        with db_cursor(commit=True, dictionary=True) as cur:
            
            # Kiểm tra trạng thái bàn
            cur.execute("SELECT Status FROM Tables WHERE TableID = %s", (order_data.table_id,))
            table_record = cur.fetchone()
            
            if not table_record:
                raise HTTPException(status_code=404, detail="Table not found.")
                
            if table_record['Status'].lower() != 'occupied':
                raise HTTPException(status_code=400, detail=f"Cannot order! Table is currently {table_record['Status']}.")

            # 1. Kiểm tra Order đang mở
            cur.execute("""
                SELECT OrderID 
                FROM Orders 
                WHERE TableID = %s AND Status IN ('open', 'preparing', 'served')
                ORDER BY OrderTime DESC LIMIT 1
            """, (order_data.table_id,))
            existing_order = cur.fetchone()

            order_id = None

            if existing_order:
                order_id = existing_order['OrderID']
                # Xóa chi tiết cũ để ghi đè giỏ hàng mới
                cur.execute("DELETE FROM OrderDetails WHERE OrderID = %s", (order_id,))
                # Cập nhật ID khách hàng
                cur.execute("UPDATE Orders SET CustomerID = %s WHERE OrderID = %s", (order_data.customer_id, order_id))
            else:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cur.execute("""
                    INSERT INTO Orders (TableID, CustomerID, StaffID, OrderTime, Status)
                    VALUES (%s, %s, %s, %s, 'open')
                """, (order_data.table_id, order_data.customer_id, order_data.staff_id, current_time))
                
                cur.execute("SELECT LAST_INSERT_ID() as new_id")
                order_id = cur.fetchone()['new_id']

            # 2. Lưu chi tiết giỏ hàng
            if order_data.items:
                detail_values = []
                for item in order_data.items:
                    detail_values.append((
                        order_id, item.dish_id, item.quantity, item.unit_price, item.notes
                    ))
                
                cur.executemany("""
                    INSERT INTO OrderDetails (OrderID, DishID, Quantity, UnitPrice, Notes)
                    VALUES (%s, %s, %s, %s, %s)
                """, detail_values)

        return {"status": "success", "message": "Order saved to database", "order_id": order_id}

    except HTTPException:
        raise
    except Exception as e:
        print(f"[KITCHEN ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/checkout")
async def checkout_table(data: CheckoutSchema):
    """Tính tiền, tạo Hóa đơn, TÍNH ĐIỂM LOYALTY, và giải phóng Bàn"""
    try:
        from src.core.db import db_cursor
        with db_cursor(commit=True, dictionary=True) as cur:
            
            cur.execute("""
                SELECT OrderID, CustomerID FROM Orders 
                WHERE TableID = %s AND Status != 'closed' ORDER BY OrderTime DESC LIMIT 1
            """, (data.table_id,))
            order = cur.fetchone()
            if not order:
                raise HTTPException(status_code=404, detail="No active order found.")
            
            order_id = order['OrderID']
            # Ưu tiên lấy CustomerID từ giao diện đẩy xuống, nếu không thì lấy từ Order cũ
            final_customer_id = data.customer_id if data.customer_id else order['CustomerID']

            cur.execute("SELECT SUM(Quantity * UnitPrice) as subtotal FROM OrderDetails WHERE OrderID = %s", (order_id,))
            subtotal_dict = cur.fetchone()
            subtotal = float(subtotal_dict['subtotal']) if subtotal_dict['subtotal'] else 0.0

            if subtotal == 0:
                raise HTTPException(status_code=400, detail="Order is empty.")

            tax_amount = subtotal * 0.08
            total_amount = subtotal + tax_amount + data.service_charge - data.discount_amount

            total_paid = sum(p.amount for p in data.payments)
            if total_paid < total_amount - 0.01:
                raise HTTPException(status_code=400, detail=f"Not enough payment amount. Paid: {total_paid}, Required: {total_amount}")

            primary_method = max(data.payments, key=lambda p: p.amount).method.lower() if data.payments else 'cash'

            cur.execute("UPDATE Orders SET CustomerID = %s WHERE OrderID = %s", (final_customer_id, order_id))

            # 1. TẠO INVOICE
            cur.execute("""
                INSERT INTO Invoices (
                    OrderID, CustomerID, SubTotal, DiscountAmount,
                    ServiceCharge, TaxAmount, TotalAmount, 
                    PaymentMethod, PaymentDate, Status
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURRENT_DATE(), 'paid')
            """, (order_id, final_customer_id, subtotal, data.discount_amount, data.service_charge, tax_amount, total_amount, primary_method))
            
            cur.execute("SELECT LAST_INSERT_ID() as new_inv_id")
            invoice_id = cur.fetchone()['new_inv_id']

            # 2. LƯU TIỀN VÀO 3 CỘT TRONG BẢNG INVOICES
            cash_amt = sum(p.amount for p in data.payments if p.method.lower() == 'cash')
            card_amt = sum(p.amount for p in data.payments if p.method.lower() == 'card')
            transfer_amt = sum(p.amount for p in data.payments if p.method.lower() in ['bank_transfer', 'transfer'])

            try:
                cur.execute("""
                    UPDATE Invoices 
                    SET CashAmount = %s, CardAmount = %s, TransferAmount = %s
                    WHERE InvoiceID = %s
                """, (cash_amt, card_amt, transfer_amt, invoice_id))
            except Exception as ex_col:
                print(f"[THÔNG BÁO] Chưa thể lưu cột Split Payment: {ex_col}")

            # ==========================================
            # 3. TÍNH VÀ CỘNG ĐIỂM LOYALTY CHO KHÁCH HÀNG
            # ==========================================
            if final_customer_id:
                # Tỉ lệ quy đổi: Cứ 100.000 VNĐ chi tiêu = 50 Điểm tích lũy
                points_earned = int((total_amount / 100000) * 50)
                
                if points_earned > 0:
                    try:
                        cur.execute("""
                            UPDATE Customers 
                            SET LoyaltyPoints = LoyaltyPoints + %s 
                            WHERE CustomerID = %s
                        """, (points_earned, final_customer_id))
                        print(f"🎉 Đã cộng thành công {points_earned} điểm cho Khách hàng ID: {final_customer_id}")
                    except Exception as e_points:
                        print(f"[LỖI CỘNG ĐIỂM] Không thể cập nhật điểm Loyalty: {e_points}")

            # 4. Đóng Order & Trả Bàn
            cur.execute("UPDATE Orders SET Status = 'closed' WHERE OrderID = %s", (order_id,))
            cur.execute("UPDATE Tables SET Status = 'available' WHERE TableID = %s", (data.table_id,))

        return {"status": "success", "message": "Checkout successful, points added!"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"\n[CRITICAL CHECKOUT ERROR]: {str(e)}\n")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/table/{table_id}")
async def get_active_order(table_id: int):
    """Lấy danh sách món ăn đang được phục vụ tại bàn để nạp lại vào giao diện POS"""
    try:
        from src.core.db import db_cursor
        with db_cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT OrderID, CustomerID FROM Orders 
                WHERE TableID = %s AND Status IN ('open', 'preparing', 'served')
                ORDER BY OrderTime DESC LIMIT 1
            """, (table_id,))
            order = cur.fetchone()
            
            if not order:
                return {"items": [], "customer_id": None}
            
            cur.execute("""
                SELECT 
                    od.DishID as id, 
                    mi.DishName as name, 
                    od.UnitPrice as price, 
                    od.Quantity as qty, 
                    od.Notes as note
                FROM OrderDetails od
                JOIN MenuItems mi ON od.DishID = mi.DishID
                WHERE od.OrderID = %s
            """, (order['OrderID'],))
            items = cur.fetchall()
            
            for item in items:
                item['price'] = float(item['price'])
                item['isEditing'] = False
                
            return {"items": items, "customer_id": order['CustomerID']}
    except Exception as e:
        print(f"[GET ORDER ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))