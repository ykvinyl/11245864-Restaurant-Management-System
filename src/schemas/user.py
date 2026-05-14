from pydantic import BaseModel

# Lọc dữ liệu khi nhân viên gõ tài khoản/mật khẩu để đăng nhập
class UserLogin(BaseModel):
    username: str
    password: str

# Lớp này định nghĩa hình dáng của chiếc "Thẻ ra vào" (JWT Token) trả về cho Web
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

# Thông tin cơ bản của nhân viên (Không bao giờ trả về mật khẩu)
class UserResponse(BaseModel):
    staff_id: int
    staff_name: str
    role: str