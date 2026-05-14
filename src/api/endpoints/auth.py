from fastapi import APIRouter, HTTPException, status
from src.core.db import db_cursor
from src.core.security import create_access_token, verify_password
from src.schemas.user import UserLogin, Token

router = APIRouter()

@router.post("/login", response_model=Token)
async def login(data: UserLogin):
    try:
        with db_cursor(dictionary=True) as cur:
            # Tìm nhân viên trong cơ sở dữ liệu dựa vào tên đăng nhập
            cur.execute(
                "SELECT StaffID, Role, HashedPassword FROM Staff WHERE StaffName = %s", 
                (data.username,)
            )
            user = cur.fetchone()

        # Kiểm tra xem tài khoản có tồn tại không và mật khẩu có khớp không
        if not user or not verify_password(data.password, user['HashedPassword']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Sai tai khoan hoac mat khau",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Tạo JWT Token chứa ID và Role của nhân viên
        access_token = create_access_token(
            subject=user['StaffID'], 
            role=user['Role']
        )
        
        # Trả về token theo đúng khuôn mẫu Token đã định nghĩa trong Schema
        return {
            "access_token": access_token, 
            "token_type": "bearer", 
            "role": user['Role']
        }

    except Exception as e:
        # Nếu lỗi là do đăng nhập sai (HTTPException), ném lỗi đó lên
        if isinstance(e, HTTPException):
            raise e
        # Nếu là lỗi do sập Database hoặc lỗi hệ thống khác, báo lỗi 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Loi he thong: {str(e)}"
        )