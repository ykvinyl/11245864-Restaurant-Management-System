from src.core.db import db_cursor

class Customer:
    def __init__(self, name, phone, email="", customer_id=None):
        self.customer_id = customer_id
        self.name = name
        self.phone = phone
        self.email = email

    def save(self) -> int:
        with db_cursor(commit=True, dictionary=False) as cur:
            # Nếu khách hàng chưa có ID, tức là tạo mới
            if self.customer_id is None:
                sql = "INSERT INTO Customers (CustomerName, Phone, Email) VALUES (%s, %s, %s)"
                cur.execute(sql, (self.name, self.phone, self.email))
                self.customer_id = cur.lastrowid
                return self.customer_id
            # Nếu có ID rồi, tức là update (nếu cần mở rộng sau này)
            else:
                sql = "UPDATE Customers SET CustomerName=%s, Phone=%s, Email=%s WHERE CustomerID=%s"
                cur.execute(sql, (self.name, self.phone, self.email, self.customer_id))
                return self.customer_id