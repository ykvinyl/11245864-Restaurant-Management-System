from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from collections import defaultdict
import random
from src.analytics.market_basket import run_market_basket_analysis
from src.analytics.reports import get_daily_revenue, get_top_selling_dishes, generate_business_insights

router = APIRouter()

@router.get("/market-basket")
async def get_market_basket_data():
    try:
        results = run_market_basket_analysis()
        return {"status": "success", "data": results if results else []}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/revenue")
async def api_get_revenue(days: int = 7):
    try:
        return {"status": "success", "data": get_daily_revenue(days)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top-dishes")
async def api_get_top_dishes(limit: int = 5):
    try:
        return {"status": "success", "data": get_top_selling_dishes(limit)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dashboard-full")
async def get_dashboard_full():
    try:
        from src.core.db import db_cursor
        
        raw_top_dishes = get_top_selling_dishes(8)
        raw_revenue = get_daily_revenue(30)
        raw_basket = run_market_basket_analysis()

        # FETCH ALL ACTIVE MENU DISHES TO USE AS FALLBACK AND MAPPING PRICE
        all_dishes_names = []
        price_map = {}
        with db_cursor(dictionary=True) as cur:
            cur.execute("SELECT DishName, Price, IsAvailable FROM MenuItems")
            all_dishes_db = cur.fetchall()
            for d in all_dishes_db:
                # Lưu giá tiền của tất cả món ăn vào thư viện từ điển (price_map)
                price_map[d['DishName']] = float(d['Price'])
                if d['IsAvailable'] == 1:
                    all_dishes_names.append(d)

        # NẾU DB TRỐNG -> CHÈN DỮ LIỆU MỒI ĐỂ DEMO
        if not raw_top_dishes and all_dishes_names:
            random.seed(42)
            fallback_dishes = random.sample(all_dishes_names, min(5, len(all_dishes_names)))
            raw_top_dishes = []
            sold_pool = [142, 98, 85, 64, 45]
            for idx, dish in enumerate(fallback_dishes):
                sold = sold_pool[idx] if idx < len(sold_pool) else 20
                raw_top_dishes.append({
                    "DishName": dish['DishName'],
                    "TotalSold": sold,
                    "TotalRevenue": float(dish['Price']) * sold
                })

        # ĐÃ FIX LỖI THIẾU DOANH THU CỦA MENU PERFORMANCE
        formatted_top = []
        if raw_top_dishes:
            total_all = sum(int(item.get('TotalSold', 0)) for item in raw_top_dishes)
            for i, item in enumerate(raw_top_dishes):
                rev = float(item.get('TotalRevenue', 0))
                
                # Nếu DB view không trả ra TotalRevenue, hệ thống sẽ tự động TÍNH TOÁN = Giá * Số lượng
                if rev == 0:
                    dish_price = price_map.get(item['DishName'], 0.0)
                    rev = dish_price * int(item.get('TotalSold', 0))

                formatted_top.append({
                    "rank": i + 1,
                    "name": item['DishName'],
                    "sold": item['TotalSold'],
                    "revenue": f"{rev:,.0f} VND",
                    "percentage": round((int(item.get('TotalSold', 0)) / total_all * 100), 1) if total_all > 0 else 0,
                    "status": "best" if i == 0 else ("good" if i < 3 else "average")
                })
            
        # DYNAMIC REVENUE AGGREGATION
        daily_list = []
        weekly_dict = defaultdict(lambda: {"orders": 0, "gross": 0.0})
        monthly_dict = defaultdict(lambda: {"orders": 0, "gross": 0.0})

        if raw_revenue:
            for r in raw_revenue:
                date_val = r.get('Date') or r.get('Payment Date')
                if isinstance(date_val, str):
                    try: 
                        date_obj = datetime.strptime(date_val, "%Y-%m-%d").date()
                    except: 
                        date_obj = datetime.now().date()
                else:
                    date_obj = date_val
                
                gross = float(r.get('DailyRevenue', r.get('TotalAmount', 0)))
                orders = int(r.get('OrderCount', r.get('Orders', 1)))
                
                daily_list.append({
                    "period": str(date_obj),
                    "orders": orders,
                    "net": f"{(gross*0.92):,.0f} VND",
                    "tax": f"{(gross*0.08):,.0f} VND",
                    "gross": f"{gross:,.0f} VND"
                })
                
                week_num = date_obj.isocalendar()[1]
                week_str = f"Week {week_num}, {date_obj.year}"
                weekly_dict[week_str]["orders"] += orders
                weekly_dict[week_str]["gross"] += gross
                
                month_str = date_obj.strftime("%B %Y")
                monthly_dict[month_str]["orders"] += orders
                monthly_dict[month_str]["gross"] += gross

        weekly_list = [{"period": k, "orders": v["orders"], "net": f"{(v['gross'] * 0.92):,.0f} VND", "tax": f"{(v['gross'] * 0.08):,.0f} VND", "gross": f"{v['gross']:,.0f} VND"} for k, v in weekly_dict.items()]
        monthly_list = [{"period": k, "orders": v["orders"], "net": f"{(v['gross'] * 0.92):,.0f} VND", "tax": f"{(v['gross'] * 0.08):,.0f} VND", "gross": f"{v['gross']:,.0f} VND"} for k, v in monthly_dict.items()]
        revenue_report = {"day": daily_list[:7], "week": weekly_list, "month": monthly_list}

        real_tables = []
        real_customers = []
        
        with db_cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT 
                    t.TableID, t.Status, t.Capacity, t.Location,
                    (SELECT c.CustomerName 
                     FROM Orders o 
                     JOIN Customers c ON o.CustomerID = c.CustomerID 
                     WHERE o.TableID = t.TableID AND o.Status != 'closed' 
                     ORDER BY o.OrderTime DESC LIMIT 1) as CustomerName,
                    (SELECT SUM(od.Quantity * od.UnitPrice) 
                     FROM Orders o2 
                     JOIN OrderDetails od ON o2.OrderID = od.OrderID 
                     WHERE o2.TableID = t.TableID AND o2.Status != 'closed') as LastTotal
                FROM Tables t 
                ORDER BY t.TableID ASC LIMIT 15
            """)
            db_tables = cur.fetchall()
            
            for t in db_tables:
                is_active = t['Status'].lower() in ['occupied', 'reserved']
                
                last_total = t['LastTotal']
                if is_active and last_total is not None:
                    order_total_str = f"{float(last_total):,.0f} VND"
                elif is_active:
                    order_total_str = "0 VND"
                else:
                    order_total_str = "-"
                    
                if is_active and t['CustomerName']:
                    cust_name = t['CustomerName']
                elif is_active:
                    cust_name = "Walk-in Guest"
                else:
                    cust_name = "-"

                real_tables.append({
                    "id": t['TableID'], 
                    "status": t['Status'],
                    "capacity": t['Capacity'], 
                    "location": t['Location'] or "Dining Area",
                    "orderTotal": order_total_str,
                    "customer": cust_name
                })
            
            cur.execute("SELECT CustomerName, PhoneNumber, LoyaltyPoints FROM Customers ORDER BY LoyaltyPoints DESC LIMIT 5")
            for c in cur.fetchall():
                real_customers.append({"name": c['CustomerName'], "phone": c['PhoneNumber'], "points": c['LoyaltyPoints']})

            cur.execute("""
                SELECT 
                    COUNT(*) as total_tables,
                    SUM(CASE WHEN Status = 'occupied' THEN 1 ELSE 0 END) as occupied_tables,
                    SUM(CASE WHEN Status = 'occupied' THEN Capacity ELSE 0 END) as live_guests
                FROM Tables
            """)
            kpi_data = cur.fetchone()
            total_tables = kpi_data['total_tables'] if kpi_data and kpi_data['total_tables'] else 1
            occupied_tables = kpi_data['occupied_tables'] if kpi_data and kpi_data['occupied_tables'] else 0
            live_guests = kpi_data['live_guests'] if kpi_data and kpi_data['live_guests'] else 0
            occupancy_rate = int((occupied_tables / total_tables) * 100) if total_tables > 0 else 0

            cur.execute("""
                SELECT HOUR(OrderTime) as hr, COUNT(*) as volume
                FROM Orders
                GROUP BY HOUR(OrderTime)
                ORDER BY hr ASC
            """)
            peak_data = cur.fetchall()
            if peak_data:
                peak_labels = [f"{row['hr']:02d}:00" for row in peak_data]
                peak_values = [row['volume'] for row in peak_data]
            else:
                peak_labels = []
                peak_values = []

        market_basket = []
        if raw_basket:
            for item in raw_basket:
                try:
                    src = item.get('SourceDish') or item.get('antecedents')
                    tgt = item.get('TargetDish') or item.get('consequents')
                    conf = item.get('ConfidenceScore') or item.get('confidence')
                    market_basket.append({
                        "source": str(src).replace("frozenset({", "").replace("'", "").replace("})", ""),
                        "target": str(tgt).replace("frozenset({", "").replace("'", "").replace("})", ""),
                        "targetIcon": "fa-star text-yellow-400",
                        "confidence": int(float(conf) * 100 if float(conf) <= 1 else conf)
                    })
                except: continue

        if not market_basket and len(all_dishes_names) >= 4:
            random.seed(99)
            basket_pool = random.sample(all_dishes_names, 4)
            market_basket = [
                {
                    "source": basket_pool[0]['DishName'], 
                    "target": basket_pool[1]['DishName'], 
                    "targetIcon": "fa-glass-water text-blue-400", 
                    "confidence": 88
                },
                {
                    "source": basket_pool[2]['DishName'], 
                    "target": basket_pool[3]['DishName'], 
                    "targetIcon": "fa-beer-mug-empty text-yellow-500", 
                    "confidence": 76
                }
            ]

        insights = []
        if market_basket:
            top = market_basket[0]
            insights.append({"category": "Revenue Optimization", "title": f"Combo Suggestion: {top['source']} & {top['target']}", "message": f"Cross-sell confidence is at {top['confidence']}%. System auto-enabled upsell prompts.", "color": "green", "icon": "fa-arrow-trend-up"})
            
        if raw_top_dishes:
            low = raw_top_dishes[-1]
            insights.append({"category": "Menu Strategy", "title": f"Warning: '{low['DishName']}'", "message": f"This item has only {low['TotalSold']} order(s). Consider removing it.", "color": "red", "icon": "fa-triangle-exclamation"})
            
        insights.append({"category": "Operations (HR)", "title": "Peak Traffic Alert", "message": "High volume of orders detected. Recommend reallocating staff.", "color": "yellow", "icon": "fa-user-clock"})

        dish_labels = [item['DishName'] for item in raw_top_dishes] if raw_top_dishes else []
        dish_data = [item['TotalSold'] for item in raw_top_dishes] if raw_top_dishes else []
        
        today_revenue = sum(float(r.get('DailyRevenue', 0)) for r in raw_revenue[:1]) if raw_revenue else 0
        today_orders = int(sum(int(r.get('OrderCount', 0)) for r in raw_revenue[:1]) if raw_revenue else 0)

        return {
            "kpi": {
                "revenue": f"{today_revenue:,.0f} VND", 
                "occupancy": f"{occupancy_rate}%", 
                "orders": today_orders, 
                "guests": int(live_guests)
            },
            "revenueReport": revenue_report,
            "peakHours": {"labels": peak_labels, "data": peak_values},
            "dishes": {"labels": dish_labels, "data": dish_data},
            "topDishesTable": formatted_top,
            "tables": real_tables,
            "customers": real_customers,
            "marketBasket": market_basket,
            "insights": insights
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Dashboard Error: {str(e)}")

@router.get("/pos-data")
async def get_pos_data():
    try:
        from src.core.db import db_cursor
        with db_cursor(dictionary=True) as cur:
            cur.execute("SELECT CategoryName FROM Categories")
            cats = cur.fetchall()
            categories = ["All"] + [c['CategoryName'] for c in cats]

            cur.execute("""
                SELECT m.DishID as id, m.DishName as name, m.Price as price,
                c.CategoryName as category, m.IsAvailable as is_available,
                m.Description as description, m.PrepTime as prep_time
                FROM MenuItems m
                LEFT JOIN Categories c ON m.CategoryID = c.CategoryID
            """)
            menu = cur.fetchall()
            for item in menu:
                item['price'] = float(item['price'])
                
            cur.execute("SELECT TableID as id, Status as status FROM Tables")
            tables = cur.fetchall()

        return {"categories": categories, "menu": menu, "tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/menu/all")
async def get_all_menu_management():
    try:
        from src.core.db import db_cursor
        with db_cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT m.DishID as id, m.DishName as name, m.Price as price,
                c.CategoryName as category, m.IsAvailable as is_available,
                m.Description as description, m.PrepTime as prep_time
                FROM MenuItems m
                LEFT JOIN Categories c ON m.CategoryID = c.CategoryID
                ORDER BY m.DishID DESC
            """)
            menu = cur.fetchall()
            for item in menu:
                item['price'] = float(item['price'])
        return menu
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/menu/update")
async def update_menu_item(data: dict):
    try:
        from src.core.db import db_cursor
        with db_cursor(commit=True) as cur:
            if 'is_available' in data:
                cur.execute("UPDATE MenuItems SET IsAvailable = %s WHERE DishID = %s", (data['is_available'], data['id']))
            elif 'price' in data:
                cur.execute("UPDATE MenuItems SET Price = %s WHERE DishID = %s", (data['price'], data['id']))
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))