import sys
import os
import random
from datetime import datetime, timedelta
from faker import Faker

# Thiết lập đường dẫn để Python nhận diện được thư mục src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.db import db_cursor
from src.core.security import get_password_hash

# 1. Khai báo thư viện tạo dữ liệu giả với locale Tiếng Việt
fake = Faker('vi_VN')

def run_smart_seed():
    print("🌱 BẮT ĐẦU KHỞI TẠO DỮ LIỆU HẠT GIỐNG (SMART SEED)...")
    
    with db_cursor(commit=True, dictionary=True) as cur:
        # ==========================================
        # 1. TẠO TÀI KHOẢN ADMIN
        # ==========================================
        cur.execute("SELECT StaffID FROM Staff WHERE StaffName = 'Admin'")
        staff = cur.fetchone()
        if not staff:
            hashed_pw = get_password_hash("admin123")
            cur.execute("INSERT INTO Staff (StaffName, Role, PhoneNumber, HashedPassword) VALUES (%s, %s, %s, %s)",
                        ("Admin", "admin", "0199999999", hashed_pw))
            staff_id = cur.lastrowid
            print("✅ Đã tạo tài khoản Admin (admin123)")
        else:
            staff_id = staff['StaffID']

        # ==========================================
        # 2. TẠO DANH MỤC & MÓN ĂN 
        # ==========================================
        cats = ['Main Course', 'Appetizer', 'Beverage', 'Side Dish']
        cat_ids = {}
        for c in cats:
            cur.execute("SELECT CategoryID FROM Categories WHERE CategoryName = %s", (c,))
            row = cur.fetchone()
            if not row:
                cur.execute("INSERT INTO Categories (CategoryName) VALUES (%s)", (c,))
                cat_ids[c] = cur.lastrowid
            else:
                cat_ids[c] = row['CategoryID']

        dishes = [
            ("Kobe Beef Pho", 300000, cat_ids['Main Course']),
            ("Fried Dough Sticks", 15000, cat_ids['Side Dish']),
            ("Fried Spring Rolls", 65000, cat_ids['Appetizer']),
            ("Hanoi Beer", 45000, cat_ids['Beverage']),
            ("Grilled Pork Noodle", 90000, cat_ids['Main Course']),
            ("Iced Tea", 10000, cat_ids['Beverage']),
            ("Salmon Salad", 150000, cat_ids['Appetizer']),
            ("Salted Coffee", 55000, cat_ids['Beverage'])
        ]
        dish_ids = {}
        for d, p, cid in dishes:
            cur.execute("SELECT DishID FROM MenuItems WHERE DishName = %s", (d,))
            row = cur.fetchone()
            if not row:
                cur.execute("INSERT INTO MenuItems (DishName, Price, CategoryID, IsAvailable) VALUES (%s, %s, %s, 1)", (d, p, cid))
                dish_ids[d] = {"id": cur.lastrowid, "price": p}
            else:
                cur.execute("SELECT DishID, Price FROM MenuItems WHERE DishName = %s", (d,))
                r2 = cur.fetchone()
                dish_ids[d] = {"id": r2['DishID'], "price": float(r2['Price'])}
        print("✅ Đã nạp Thực đơn Tiếng Anh chuẩn.")

        # ==========================================
        # 3. TẠO ĐÚNG 15 BÀN (TABLES)
        # ==========================================
        cur.execute("SELECT COUNT(*) as c FROM Tables")
        if cur.fetchone()['c'] < 15:
            locations = ["Window", "Main Hall", "VIP Room", "Outdoor", "Balcony"]
            for i in range(1, 16):
                cap = random.choice([2, 4, 6, 8])
                loc = random.choice(locations)
                stat = random.choice(['available', 'available', 'occupied', 'reserved'])
                try:
                    cur.execute("INSERT INTO Tables (TableNumber, Capacity, Location, Status) VALUES (%s, %s, %s, %s)",
                                (i, cap, loc, stat))
                except: pass
            print("✅ Đã thiết lập Sơ đồ 15 Bàn.")

        # ==========================================
        # 4. TẠO VÀ CẬP NHẬT KHÁCH HÀNG
        # ==========================================
        cur.execute("SELECT CustomerID FROM Customers")
        existing_custs = cur.fetchall()
        
        # 4.1. "Chữa bệnh" cho khách hàng cũ: Gắn lại tên Tiếng Việt và cấp điểm
        for c in existing_custs:
            new_name = fake.name()
            pts = random.choice([random.randint(10, 150), random.randint(200, 400), random.randint(600, 900), random.randint(1100, 1500)])
            try:
                cur.execute("UPDATE Customers SET CustomerName = %s, LoyaltyPoints = %s WHERE CustomerID = %s", 
                            (new_name, pts, c['CustomerID']))
            except: pass

        # 4.2. Thêm mới cho đủ 30 khách hàng nếu đang thiếu
        customers_needed = 30 - len(existing_custs)
        if customers_needed > 0:
            for _ in range(customers_needed):
                phone = fake.phone_number()[:15]
                pts = random.choice([random.randint(10, 150), random.randint(200, 400), random.randint(600, 900), random.randint(1100, 1500)])
                try:
                    cur.execute("INSERT INTO Customers (CustomerName, PhoneNumber, Email, LoyaltyPoints) VALUES (%s, %s, %s, %s)",
                                (fake.name(), phone, fake.email(), pts))
                except: pass
        
        cur.execute("SELECT CustomerID FROM Customers LIMIT 50")
        customer_ids = [r['CustomerID'] for r in cur.fetchall()]
        print(f"✅ Đã chuẩn bị {len(customer_ids)} Khách hàng (100% tên Tiếng Việt & Đã cấp điểm).")

        # ==========================================
        # 5. TẠO 150 ĐƠN HÀNG
        # ==========================================
        cur.execute("SELECT TableID FROM Tables")
        table_ids = [r['TableID'] for r in cur.fetchall()]
        
        if not table_ids:
            print("Lỗi: Không tìm thấy Bàn nào trong DB.")
            return

        print("🔄 Đang sinh ra 150 Đơn hàng giao dịch rải rác trong 30 ngày...")
        inserted_orders = 0
        for _ in range(150):
            days_ago = random.randint(0, 30)
            order_time = datetime.now() - timedelta(days=days_ago, minutes=random.randint(10, 600))
            
            t_id = random.choice(table_ids)
            c_id = random.choice(customer_ids) if random.random() > 0.4 else None

            # Tạo Order
            cur.execute("INSERT INTO Orders (TableID, CustomerID, StaffID, OrderTime, Status) VALUES (%s, %s, %s, %s, 'closed')",
                        (t_id, c_id, staff_id, order_time))
            o_id = cur.lastrowid

            # THUẬT TOÁN BƠM QUY LUẬT MUA KÈM (MARKET BASKET AI)
            basket = []
            rand_val = random.random()
            
            # Khách thích ăn Phở bò
            if rand_val < 0.45:
                basket.append("Kobe Beef Pho")
                if random.random() < 0.95: 
                    basket.append("Fried Dough Sticks")
                if random.random() < 0.3:
                    basket.append("Iced Tea")
                    
            # Khách thích ăn Nem rán
            elif rand_val < 0.80:
                basket.append("Fried Spring Rolls")
                if random.random() < 0.88: 
                    basket.append("Hanoi Beer")
                    
            # Khách gọi linh tinh
            else:
                basket.append(random.choice(list(dish_ids.keys())))
                basket.append(random.choice(list(dish_ids.keys())))

            basket = list(set(basket))

            # Thêm vào OrderDetails và tính tiền
            subtotal = 0
            for dish_name in basket:
                d_info = dish_ids[dish_name]
                qty = random.randint(1, 3)
                price = d_info['price']
                subtotal += qty * price
                cur.execute("INSERT INTO OrderDetails (OrderID, DishID, Quantity, UnitPrice) VALUES (%s, %s, %s, %s)",
                            (o_id, d_info['id'], qty, price))

            tax = subtotal * 0.08
            svc = subtotal * 0.05
            total = subtotal + tax + svc
            payment_time = order_time + timedelta(minutes=45)

            # Xuất Hóa đơn (Invoices)
            cur.execute("""INSERT INTO Invoices 
                        (OrderID, CustomerID, SubTotal, DiscountAmount, ServiceCharge, TaxAmount, TotalAmount, PaymentMethod, PaymentDate, Status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'paid')""",
                        (o_id, c_id, subtotal, 0, svc, tax, total, 'card', payment_time))
            
            inserted_orders += 1

        print(f"✅ Thành công! Đã chèn {inserted_orders} giao dịch để AI học.")

if __name__ == "__main__":
    run_smart_seed()
    print("🎉 TẤT CẢ ĐÃ HOÀN TẤT! Bạn hãy chạy lại server: uvicorn src.main:app --reload")