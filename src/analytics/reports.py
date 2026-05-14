from src.core.db import db_cursor

def get_daily_revenue(days: int = 30) -> list[dict]:
    """Lấy doanh thu và đếm số đơn hàng theo từng ngày"""
    from src.core.db import db_cursor
    
    sql = """
        SELECT 
            DATE(PaymentDate) AS Date, 
            COUNT(InvoiceID) AS OrderCount, 
            SUM(TotalAmount) AS DailyRevenue
        FROM Invoices
        WHERE Status = 'paid'
        GROUP BY DATE(PaymentDate)
        ORDER BY DATE(PaymentDate) DESC
        LIMIT %s
    """
    with db_cursor(dictionary=True) as cur:
        cur.execute(sql, (days,))
        return cur.fetchall()

def get_top_selling_dishes(limit: int = 5):
    with db_cursor(dictionary=True) as cur:
        sql = """
            SELECT m.DishName, SUM(od.Quantity) as TotalSold
            FROM OrderDetails od
            JOIN MenuItems m ON od.DishID = m.DishID
            GROUP BY m.DishID, m.DishName
            ORDER BY TotalSold DESC
            LIMIT %s
        """
        cur.execute(sql, (limit,))
        return cur.fetchall()

def generate_business_insights(parsed_basket=None):
    """HỆ THỐNG ĐỀ XUẤT TỰ ĐỘNG"""
    insights = []
    
    try:
        with db_cursor(dictionary=True) as cur:
            # 1. Phân tích Giờ cao điểm
            cur.execute("""
                SELECT HOUR(OrderTime) as PeakHour, COUNT(*) as TotalOrders
                FROM Orders 
                WHERE DATE(OrderTime) = CURDATE()
                GROUP BY HOUR(OrderTime)
                ORDER BY TotalOrders DESC LIMIT 1
            """)
            peak_data = cur.fetchone()
            
            if peak_data and peak_data['TotalOrders'] > 0:
                total_orders = peak_data['TotalOrders']
                status = "Bình thường" if total_orders < 30 else "Quá tải"
                color = "blue" if total_orders < 30 else "yellow"
                
                insights.append({
                    "category": "Vận hành (HR)",
                    "title": f"Đỉnh điểm lúc {peak_data['PeakHour']}h00",
                    "message": f"Hệ thống ghi nhận {total_orders} đơn hàng. Trạng thái: {status}. Khuyến nghị điều phối nhân sự phù hợp.",
                    "color": color,
                    "icon": "fa-user-clock"
                })

            # 2. Phân tích Món ế
            cur.execute("""
                SELECT m.DishName, SUM(od.Quantity) as TotalSold
                FROM OrderDetails od
                JOIN MenuItems m ON od.DishID = m.DishID
                GROUP BY m.DishID, m.DishName
                ORDER BY TotalSold ASC LIMIT 1
            """)
            low_data = cur.fetchone()
            if low_data:
                insights.append({
                    "category": "Thực đơn (Menu)",
                    "title": f"Cảnh báo món '{low_data['DishName']}'",
                    "message": f"Món này chỉ có {low_data['TotalSold']} lượt gọi. Cân nhắc gỡ bỏ để giảm tải cho Bếp.",
                    "color": "red",
                    "icon": "fa-triangle-exclamation"
                })
    except Exception as e:
        print(f"Lỗi SQL Insights: {e}")

    # 3. Market Basket Insights (Sử dụng dữ liệu đã làm sạch từ API truyền vào)
    if parsed_basket:
        # Lấy tối đa 2 rule nổi bật nhất để tránh dài dòng
        for rule in parsed_basket[:2]:
            conf = rule.get("confidence", 0)
            src = rule.get("source", "")
            tgt = rule.get("target", "")
            
            if conf >= 80:
                insights.append({
                    "category": "Tối ưu Doanh thu",
                    "title": f"Combo {src} & {tgt}",
                    "message": f"Độ tin cậy mua kèm đạt {conf}%. Hệ thống đã tự động bật nhắc nhở Upsell trên máy POS của Waiter.",
                    "color": "green",
                    "icon": "fa-arrow-trend-up"
                })
            elif conf <= 20:
                insights.append({
                    "category": "Kiểm soát rủi ro",
                    "title": f"Món '{src}' bán kèm kém",
                    "message": f"Chỉ số liên kết chỉ đạt {conf}%. Khuyến nghị đánh giá lại combo này.",
                    "color": "red",
                    "icon": "fa-triangle-exclamation"
                })

    return insights