from src.core.db import db_cursor

class Reservation:
    def __init__(self, customer_id, table_id, staff_id, date_time, guest_count, special_requests=""):
        self.customer_id = customer_id
        self.table_id = table_id
        self.staff_id = staff_id
        self.date_time = date_time
        self.guest_count = guest_count
        self.special_requests = special_requests
        self.reservation_id = None

    def save(self) -> tuple[int, str]:
        with db_cursor(commit=True, dictionary=False) as cur:
            results = cur.callproc("sp_MakeReservation", [
                self.customer_id,
                self.table_id,
                self.staff_id,
                self.date_time,
                self.guest_count,
                self.special_requests,
                0,
                ""
            ])
            
            rid = results[6]
            msg = results[7]
            self.reservation_id = rid
            
            if rid != -1:
                return rid, msg
            else:
                return -1, msg