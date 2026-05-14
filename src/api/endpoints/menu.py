from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter()

# ==========================================
# SCHEMAS (Data Structures)
# ==========================================

class MenuItemSchema(BaseModel):
    id: int
    name: str
    price: float
    category: str
    is_available: bool
    image_url: Optional[str] = None

class MenuItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None
    category: Optional[str] = None
    is_available: Optional[int] = None
    IsAvailable: Optional[int] = None 
    description: Optional[str] = None
    prep_time: Optional[int] = None

# ĐÃ FIX: Chuyển category_id (int) thành category (str)
class MenuItemCreate(BaseModel):
    name: str
    price: float
    category: str
    is_available: int
    description: Optional[str] = ""
    prep_time: Optional[int] = 15

# ==========================================
# API ENDPOINTS
# ==========================================

@router.get("/")
async def get_all_menu_items():
    try:
        from src.core.db import db_cursor
        with db_cursor(dictionary=True) as cur:
            sql = """
                SELECT 
                    m.DishID as id, 
                    m.DishName as name, 
                    m.Price as price, 
                    c.CategoryName as category, 
                    m.IsAvailable as is_available,
                    m.Description as description,
                    m.PrepTime as prep_time
                FROM MenuItems m
                LEFT JOIN Categories c ON m.CategoryID = c.CategoryID
                ORDER BY c.CategoryName ASC, m.DishName ASC
            """
            cur.execute(sql)
            raw_items = cur.fetchall()
            
            formatted_items = []
            for item in raw_items:
                formatted_items.append({
                    "id": item.get('id'),
                    "name": item.get('name'),
                    "price": float(item.get('price') or 0),
                    "category": item.get('category') or 'Uncategorized',
                    "description": item.get('description') or '',
                    "prep_time": item.get('prep_time') or 15,
                    "is_available": bool(item.get('is_available')),
                    "image_url": None 
                })
                
        return formatted_items
    except Exception as e:
        print(f"[FETCH MENU ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{item_id}")
async def get_menu_item(item_id: int):
    try:
        from src.core.db import db_cursor
        with db_cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT 
                    m.DishID as id, 
                    m.DishName as name, 
                    m.Price as price, 
                    c.CategoryName as category, 
                    m.IsAvailable as is_available,
                    m.Description as description,
                    m.PrepTime as prep_time
                FROM MenuItems m
                LEFT JOIN Categories c ON m.CategoryID = c.CategoryID
                WHERE m.DishID = %s
            """, (item_id,))
            item = cur.fetchone()
            if not item:
                raise HTTPException(status_code=404, detail="Item not found")
            
            item['is_available'] = bool(item['is_available'])
            item['price'] = float(item['price'])
            item['image_url'] = None
            
        return item
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{item_id}")
async def update_menu_item(item_id: int, item_data: MenuItemUpdate):
    try:
        from src.core.db import db_cursor
        with db_cursor(commit=True, dictionary=True) as cur:
            update_fields = []
            values = []
            
            if item_data.name is not None:
                update_fields.append("DishName = %s")
                values.append(item_data.name)
                
            if item_data.price is not None:
                update_fields.append("Price = %s")
                values.append(item_data.price)
                
            # ĐÃ BỔ SUNG: Xử lý Cập nhật Danh mục (Category)
            if item_data.category is not None:
                cur.execute("SELECT CategoryID FROM Categories WHERE CategoryName = %s LIMIT 1", (item_data.category,))
                cat = cur.fetchone()
                
                if cat:
                    cat_id = cat['CategoryID'] if isinstance(cat, dict) else cat[0]
                else:
                    cur.execute("INSERT INTO Categories (CategoryName) VALUES (%s)", (item_data.category,))
                    cur.execute("SELECT LAST_INSERT_ID() as new_cat_id")
                    res = cur.fetchone()
                    cat_id = res['new_cat_id'] if isinstance(res, dict) else res[0]
                    
                update_fields.append("CategoryID = %s")
                values.append(cat_id)
                
            avail = item_data.is_available if item_data.is_available is not None else item_data.IsAvailable
            if avail is not None:
                update_fields.append("IsAvailable = %s")
                values.append(1 if avail else 0)
                
            if item_data.description is not None:
                update_fields.append("Description = %s")
                values.append(item_data.description)
            
            if item_data.prep_time is not None:
                update_fields.append("PrepTime = %s")
                values.append(item_data.prep_time)

            if not update_fields:
                return {"message": "No changes detected"}
            
            values.append(item_id)
            query = f"UPDATE MenuItems SET {', '.join(update_fields)} WHERE DishID = %s"
            cur.execute(query, tuple(values))
            
        return {"status": "success", "message": f"Item {item_id} updated"}
    except Exception as e:
        print(f"[MENU UPDATE ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/")
async def create_menu_item(item_data: MenuItemCreate):
    """Thêm món mới: Tự động tra cứu ID danh mục bằng tên để tránh lỗi lệch ID"""
    try:
        from src.core.db import db_cursor
        with db_cursor(commit=True, dictionary=True) as cur:
            
            # 1. Tìm CategoryID dựa trên Tên Danh Mục (Tránh lỗi ID cứng)
            cur.execute("SELECT CategoryID FROM Categories WHERE CategoryName = %s LIMIT 1", (item_data.category,))
            cat = cur.fetchone()
            
            if cat:
                cat_id = cat['CategoryID'] if isinstance(cat, dict) else cat[0]
            else:
                # 2. Nếu DB chưa có danh mục này, TỰ ĐỘNG TẠO MỚI!
                cur.execute("INSERT INTO Categories (CategoryName) VALUES (%s)", (item_data.category,))
                cur.execute("SELECT LAST_INSERT_ID() as new_cat_id")
                res = cur.fetchone()
                cat_id = res['new_cat_id'] if isinstance(res, dict) else res[0]

            # 3. Insert món ăn với đúng ID danh mục đã tra cứu
            cur.execute("""
                INSERT INTO MenuItems (DishName, CategoryID, Price, Description, IsAvailable, PrepTime)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                item_data.name, 
                cat_id, 
                item_data.price, 
                item_data.description, 
                item_data.is_available, 
                item_data.prep_time
            ))
            
            cur.execute("SELECT LAST_INSERT_ID() as new_id")
            id_res = cur.fetchone()
            new_id = id_res['new_id'] if isinstance(id_res, dict) else id_res[0]
            
        return {"status": "success", "id": new_id, "message": "Item created successfully"}
    except Exception as e:
        print(f"[MENU CREATE ERROR] {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ĐÃ BỔ SUNG: API XÓA MÓN ĂN
@router.delete("/{item_id}")
async def delete_menu_item(item_id: int):
    """Xóa vĩnh viễn món ăn khỏi kho"""
    try:
        from src.core.db import db_cursor
        with db_cursor(commit=True) as cur:
            # Kiểm tra xem món ăn có tồn tại không
            cur.execute("SELECT DishID FROM MenuItems WHERE DishID = %s", (item_id,))
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail="Item not found")

            # Xóa món ăn
            cur.execute("DELETE FROM MenuItems WHERE DishID = %s", (item_id,))
            
        return {"status": "success", "message": f"Item {item_id} deleted successfully"}
    except Exception as e:
        print(f"[MENU DELETE ERROR] {e}")
        # Bắt lỗi ràng buộc khóa ngoại (ví dụ món ăn đã từng được Order thì không thể xóa)
        if "foreign key constraint" in str(e).lower() or "a foreign key constraint fails" in str(e).lower():
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete this item because it has been ordered in the past. Please mark it as 'Out of Stock' instead."
            )
        raise HTTPException(status_code=500, detail=str(e))