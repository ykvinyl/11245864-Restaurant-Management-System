// --- frontend/js/api.js ---

const API_BASE_URL = "http://127.0.0.1:8000/api/v1";

const apiClient = {
    // Hàm gọi API tổng quát, tự động đính kèm Token (nếu có)
    async request(endpoint, method = "GET", body = null) {
        const token = localStorage.getItem("jwt_token"); // Lấy token từ lúc Login
        
        const headers = {
            "Content-Type": "application/json",
        };
        
        if (token) {
            headers["Authorization"] = `Bearer ${token}`; // Gửi thẻ nhân viên cho Backend kiểm tra
        }

        const config = { method, headers };
        if (body) {
            config.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, config);
            const data = await response.json();

            // Xử lý lỗi từ Backend trả về (Ví dụ: 403 Forbidden - Không có quyền)
            if (!response.ok) {
                if (response.status === 401 || response.status === 403) {
                    console.error("Lỗi phân quyền từ Backend:", data.detail);
                    alert("⛔ Lỗi bảo mật: " + data.detail);
                }
                throw new Error(data.detail || "Lỗi kết nối Backend");
            }
            return data;
        } catch (error) {
            console.error(`[API Call Failed] ${method} ${endpoint}:`, error);
            throw error; 
        }
    },

    // Các hàm rút gọn
    get(endpoint) { return this.request(endpoint, "GET"); },
    post(endpoint, data) { return this.request(endpoint, "POST", data); },
    put(endpoint, data) { return this.request(endpoint, "PUT", data); },
    delete(endpoint) { return this.request(endpoint, "DELETE"); }
};