from fastapi import APIRouter, HTTPException
from typing import List, Optional

router = APIRouter()

@router.get("/")
async def get_all_invoices():
    """Lấy danh sách tất cả hóa đơn để hiển thị trên bảng"""
    try:
        from src.core.db import db_cursor
        with db_cursor(dictionary=True) as cur:
            # Lấy tất cả thông tin, bao gồm cả 3 cột Amount mới tạo
            cur.execute("""
                SELECT 
                    i.InvoiceID as id,
                    DATE_FORMAT(i.PaymentDate, '%Y-%m-%d') as date,
                    c.CustomerName as customer,
                    o.TableID as table_id,
                    i.TotalAmount as total,
                    i.Status as status,
                    i.CashAmount,
                    i.CardAmount,
                    i.TransferAmount
                FROM Invoices i
                JOIN Orders o ON i.OrderID = o.OrderID
                LEFT JOIN Customers c ON i.CustomerID = c.CustomerID
                ORDER BY i.InvoiceID DESC
                LIMIT 50
            """)
            invoices = cur.fetchall()

            for inv in invoices:
                inv['total'] = float(inv['total']) if inv['total'] else 0.0
                inv['payments'] = []
                
                try:
                    # Đọc trực tiếp từ 3 cột trong Invoices thay vì bảng Payments
                    cash = float(inv.get('CashAmount') or 0.0)
                    card = float(inv.get('CardAmount') or 0.0)
                    trans = float(inv.get('TransferAmount') or 0.0)
                    
                    if cash > 0:
                        inv['payments'].append({"PaymentMethod": "Cash", "Amount": cash})
                    if card > 0:
                        inv['payments'].append({"PaymentMethod": "Card", "Amount": card})
                    if trans > 0:
                        inv['payments'].append({"PaymentMethod": "Transfer", "Amount": trans})
                        
                    # FALLBACK: Nếu hóa đơn cũ không có dữ liệu 3 cột này
                    if len(inv['payments']) == 0:
                        inv['payments'] = [{"PaymentMethod": "Cash", "Amount": inv['total']}]
                        
                except Exception as ex:
                    print(f"[CẢNH BÁO DB] Lỗi đọc chi tiết Amount hóa đơn {inv['id']}: {ex}")
                    inv['payments'] = [{"PaymentMethod": "Cash", "Amount": inv['total']}]
                
                if not inv['customer']:
                    inv['customer'] = "Walk-in Guest"

        return invoices
    except Exception as e:
        print(f"[LỖI CRITICAL GET /invoices/]: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{invoice_id}")
async def get_invoice_details(invoice_id: int):
    """Lấy chi tiết hóa đơn khi ấn vào hình con mắt (Mở Modal Bill)"""
    try:
        from src.core.db import db_cursor
        with db_cursor(dictionary=True) as cur:
            # 1. Lấy thông tin chung kèm 3 cột thanh toán
            cur.execute("""
                SELECT 
                    i.InvoiceID,
                    o.TableID,
                    DATE_FORMAT(i.PaymentDate, '%Y-%m-%d') as PaymentDate,
                    c.CustomerName,
                    i.SubTotal,
                    i.DiscountAmount,
                    i.ServiceCharge,
                    i.TaxAmount,
                    i.TotalAmount,
                    i.Status,
                    i.CashAmount,
                    i.CardAmount,
                    i.TransferAmount
                FROM Invoices i
                JOIN Orders o ON i.OrderID = o.OrderID
                LEFT JOIN Customers c ON i.CustomerID = c.CustomerID
                WHERE i.InvoiceID = %s
            """, (invoice_id,))
            info = cur.fetchone()
            
            if not info:
                raise HTTPException(status_code=404, detail="Invoice not found")

            if not info['CustomerName']:
                info['CustomerName'] = "Walk-in Guest"
                
            info['SubTotal'] = float(info['SubTotal']) if info['SubTotal'] else 0.0
            info['DiscountAmount'] = float(info['DiscountAmount']) if info['DiscountAmount'] else 0.0
            info['ServiceCharge'] = float(info['ServiceCharge']) if info['ServiceCharge'] else 0.0
            info['TaxAmount'] = float(info['TaxAmount']) if info['TaxAmount'] else 0.0
            info['TotalAmount'] = float(info['TotalAmount']) if info['TotalAmount'] else 0.0

            # 2. Lấy danh sách món ăn
            cur.execute("""
                SELECT 
                    mi.DishName as name,
                    od.Quantity as qty,
                    (od.Quantity * od.UnitPrice) as line_total
                FROM OrderDetails od
                JOIN Invoices i ON od.OrderID = i.OrderID
                JOIN MenuItems mi ON od.DishID = mi.DishID
                WHERE i.InvoiceID = %s
            """, (invoice_id,))
            items = cur.fetchall()
            for item in items:
                item['line_total'] = float(item['line_total'])

            # 3. Lấy chi tiết Split Payments từ 3 cột của bảng Invoices
            payments = []
            try:
                cash = float(info.get('CashAmount') or 0.0)
                card = float(info.get('CardAmount') or 0.0)
                trans = float(info.get('TransferAmount') or 0.0)

                if cash > 0: payments.append({"PaymentMethod": "Cash", "Amount": cash})
                if card > 0: payments.append({"PaymentMethod": "Card", "Amount": card})
                if trans > 0: payments.append({"PaymentMethod": "Transfer", "Amount": trans})
                
                # BẢO VỆ GIAO DIỆN: Nếu cả 3 bằng 0 (hóa đơn cũ), tự gán Cash
                if len(payments) == 0:
                    payments = [{"PaymentMethod": "Cash", "Amount": info['TotalAmount']}]
            except Exception as ex:
                print(f"[CẢNH BÁO DB] Lỗi khởi tạo mảng Payments chi tiết: {ex}")
                payments = [{"PaymentMethod": "Cash", "Amount": info['TotalAmount']}]

        return {
            "info": info,
            "items": items,
            "payments": payments
        }
    except Exception as e:
        print(f"[LỖI CRITICAL GET /invoices/{invoice_id}]: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))