from src.core.db import db_cursor

class Order:
    def __init__(self, reservation_id, staff_id, order_id=None, status="Pending"):
        self.order_id = order_id
        self.reservation_id = reservation_id
        self.staff_id = staff_id
        self.status = status

    def save(self) -> int:
        with db_cursor(commit=True, dictionary=False) as cur:
            if self.order_id is None:
                sql = "INSERT INTO Orders (ReservationID, StaffID, Status) VALUES (%s, %s, %s)"
                cur.execute(sql, (self.reservation_id, self.staff_id, self.status))
                self.order_id = cur.lastrowid
                return self.order_id
            else:
                sql = "UPDATE Orders SET Status=%s WHERE OrderID=%s"
                cur.execute(sql, (self.status, self.order_id))
                return self.order_id