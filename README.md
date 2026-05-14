# 🍽️ Advanced Restaurant Management System

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg?logo=fastapi&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-orange.svg?logo=mysql&logoColor=white)
![VanillaJS](https://img.shields.io/badge/Frontend-HTML/JS/CSS-f0db4f.svg?logo=javascript&logoColor=black)

> **Final Project 05 - Introduction to Database Systems (DSEB 66B)** > **National Economics University (NEU)** > **Author:** Le Thuy Duong  

## 📖 Project Overview
This project is a comprehensive, full-stack database application designed to manage restaurant operations. It transcends basic CRUD requirements by implementing a robust **3-tier architecture**, featuring a highly optimized **11-table MySQL database**, a fast and secure **FastAPI backend**, and an interactive **Web Frontend**.

The system demonstrates advanced database engineering skills, including complex relationship modeling (Master-Detail), automated data integrity enforcement, and encapsulated business logic.

## ✨ Key Features & Technical Highlights

### 1. Advanced Database Architecture
- **Extended Schema:** Scaled from the required 5 tables to an 11-table relational model, resolving M:N relationships properly with `OrderDetails`.
- **Financial Flexibility:** Implementation of a separate `Payments` table to support split/partial payments per invoice.
- **Audit & Traceability:** Automated `TableStatusLog` to track infrastructure usage history.

### 2. Smart Automation & Integrity (Database Objects)
- **Triggers:** - *Price Snapshotting:* Preserves historical financial accuracy by copying current menu prices into `OrderDetails` at the time of order.
  - *State Synchronization:* Automatically transitions table statuses (Available ↔ Occupied ↔ Reserved) without backend intervention.
- **Views & Stored Procedures:** Implements `vw_TopSellingDishes`, `vw_DailyRevenue`, and robust procedures like `sp_MakeReservation` and `sp_GenerateInvoice` to handle atomic transactions.
- **User-Defined Functions (UDFs):** Dynamic calculations for loyalty discounts and service charges.

### 3. Business Intelligence & Analytics
- **Market Basket Analysis:** Custom SQL analytics to identify cross-selling opportunities (frequently bought together items).
- **Dashboard Reporting:** Real-time KPI aggregation visualized dynamically using **Chart.js**.

### 4. Enterprise-Grade Security
- **Column-Level Security:** `vw_SafeCustomers` masks sensitive contact data (Phone/Email) from unauthorized staff.
- **Role-Based Access Control (RBAC):** Granular MySQL privileges mapping to 6 distinct staff roles.
- **Stateless Authentication:** Secure login using encrypted passwords (Bcrypt) and JSON Web Tokens (JWT).

## 🛠️ Tech Stack
- **Database Layer:** MySQL 8.0+
- **Application Layer (Backend):** Python 3.10+, FastAPI, Uvicorn, Pydantic, mysql-connector-python, Passlib, Python-JOSE
- **Presentation Layer (Frontend):** HTML5, Tailwind CSS, Vanilla JavaScript (ES6+), Chart.js

## 📂 Repository Structure

```text
RestaurantManagementSystem/
│
├── database/                 # SQL scripts for database initialization
│   ├── 01_schema.sql         # Creates DB, tables, and constraints
│   ├── 02_advanced_objects.sql # Creates Indexes, Views, Procedures, Functions, Triggers
│   └── 03_security.sql       # Sets up roles and database users
│
├── frontend/                 # UI assets (HTML, JS, CSS)
│   ├── login.html            # Staff authentication interface
│   ├── dashboard.html        # Real-time KPI and analytics dashboard
│   ├── customers.html        # CRM module for customer management
│   ├── menu.html             # Menu and category management
│   ├── pos.html              # Point of Sale (POS) and ordering interface
│   └── js/                   # Vanilla JavaScript logic (api.js, auth.js, etc.)
│
├── scripts/                  # Development scripts
│   └── seed_data.py          # Python script to generate realistic sample data
│
├── src/                      # FastAPI backend source code
│   ├── api/                  
│   │   └── endpoints/        # Domain-driven routers (auth, orders, pos, etc.)
│   ├── analytics/            # Market Basket and Reporting logic
│   ├── core/                 # Config, DB connection, Security utils
│   ├── models/               # Data access layer
│   ├── schemas/              # Pydantic models for request/response validation
│   └── main.py               # Application entry point
│
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

## 🚀 Installation & Setup Guide

### Phase 1: Database Setup
1. Open MySQL Workbench.
2. Execute the SQL scripts in the `database/` folder in this exact order:
   - `01_schema.sql` (Creates DB and tables)
   - `02_advanced_objects.sql` (Creates Indexes, Views, Procedures, Functions, Triggers)
   - `03_security.sql` (Sets up roles and DB users)

### Phase 2: Backend Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/ykvinyl/11245864-Restaurant-Management-System
   cd Restaurant-Management-System
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/Scripts/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Configure Environment Variables:
   Create a `.env` file in the root directory:
   ```env
   DB_HOST=localhost
DB_USER=root
DB_PASSWORD=060106
DB_NAME=RestaurantDB
SECRET_KEY=7d9f8e2b1a3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e
   ```
5. Seed Sample Data (Highly Recommended):
   ```bash
   python scripts/seed_data.py
   ```
6. Run the FastAPI server:
   ```bash
   uvicorn src.main:app --reload
   ```
   *The API documentation will be available at: `http://127.0.0.1:8000/docs`*

### Phase 3: Frontend Access
Since the frontend uses Vanilla JS with relative paths, simply open `frontend/index.html` in your web browser (or use the VS Code Live Server extension) to launch the application.

## 🔐 Default Test Accounts
If you executed the `seed_data.py` script, use the following credentials to access the system:
- **Admin:** Username: `admin` | Password: `admin123`
- **Waiter:** Username: `waiter1` | Password: `waiter123`

---
*This project was developed for academic evaluation purposes.*