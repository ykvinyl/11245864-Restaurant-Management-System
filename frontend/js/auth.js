// frontend/js/api.js
const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

async function fetchAPI(endpoint, options = {}) {
    // Lấy token từ bộ nhớ trình duyệt
    const token = localStorage.getItem("access_token");
    
    // Cấu hình Header mặc định
    const headers = {
        "Content-Type": "application/json",
        ...options.headers
    };

    // Nếu đã đăng nhập, tự động đính kèm "Thẻ thông hành" Token
    if (token) {
        headers["Authorization"] = `Bearer ${token}`;
    }

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers
        });

        // Nếu lỗi 401 (Hết hạn hoặc Token giả), đá ra trang login
        if (response.status === 401 && !endpoint.includes("/auth/login")) {
            localStorage.clear();
            window.location.href = "index.html";
            return;
        }

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || "Yêu cầu thất bại");
        }
        
        return data;
    } catch (error) {
        console.error("API Fetch Error:", error);
        throw error;
    }
}