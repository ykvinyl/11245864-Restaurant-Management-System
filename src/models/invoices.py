from src.core.db import db_cursor

class Invoice:
    def __init__(self, order_id, payment_method="Cash", tax_rate=0.08, discount_amount=0.0):
        self.order_id = order_id
        self.payment_method = payment_method
        self.tax_rate = tax_rate
        self.discount_amount = discount_amount
        self.invoice_id = None

    def generate(self) -> tuple[int, str]:
        with db_cursor(commit=True, dictionary=False) as cur:
            # Gọi Procedure sp_GenerateInvoice. 
            # Giả định Procedure có 6 tham số: 4 IN (OrderID, PaymentMethod, Tax, Discount) và 2 OUT (InvoiceID, Message)
            results = cur.callproc("sp_GenerateInvoice", [
                self.order_id,
                self.payment_method,
                self.tax_rate,
                self.discount_amount,
                0,  # Biến OUT giữ chỗ cho p_InvoiceID (Vị trí index số 4)
                ""  # Biến OUT giữ chỗ cho p_Message (Vị trí index số 5)
            ])
            
            # Lấy kết quả từ biến OUT
            inv_id = results[4]
            msg = results[5]
            self.invoice_id = inv_id
            
            if inv_id != -1:
                return inv_id, msg
            else:
                return -1, msg