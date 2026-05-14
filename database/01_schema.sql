-- ============================================================
--  RESTAURANT MANAGEMENT SYSTEM — DATABASE SCHEMA
--  Project 05 | DSEB66B | Spring 2026
--  Author  : [Your Name]
--  DBMS    : MySQL 8.0+
-- ============================================================

DROP DATABASE IF EXISTS RestaurantDB;
CREATE DATABASE RestaurantDB
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
USE RestaurantDB;

-- ─────────────────────────────────────────────
--  1. CATEGORIES  (extends base MenuItems)
-- ─────────────────────────────────────────────
CREATE TABLE Categories (
    CategoryID   INT           AUTO_INCREMENT PRIMARY KEY,
    CategoryName VARCHAR(100)  NOT NULL UNIQUE,
    Description  TEXT,
    CreatedAt    DATETIME      DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
--  2. CUSTOMERS
-- ─────────────────────────────────────────────
CREATE TABLE Customers (
    CustomerID   INT           AUTO_INCREMENT PRIMARY KEY,
    CustomerName VARCHAR(150)  NOT NULL,
    PhoneNumber  VARCHAR(20)   NOT NULL UNIQUE,
    Email        VARCHAR(255)  UNIQUE,
    Address      TEXT,
    JoinDate     DATE          DEFAULT (CURRENT_DATE),
    LoyaltyPoints INT          DEFAULT 0 CHECK (LoyaltyPoints >= 0),
    IsActive     BOOLEAN       DEFAULT TRUE,
    CreatedAt    DATETIME      DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
--  3. STAFF
-- ─────────────────────────────────────────────
CREATE TABLE Staff (
    StaffID      INT           AUTO_INCREMENT PRIMARY KEY,
    StaffName    VARCHAR(150)  NOT NULL,
    Role         ENUM('admin','manager','cashier','waiter','chef') NOT NULL,
    PhoneNumber  VARCHAR(20)   UNIQUE,
    Salary       DECIMAL(10,2) CHECK (Salary > 0),
    HireDate     DATE          DEFAULT (CURRENT_DATE),
    IsActive     BOOLEAN       DEFAULT TRUE
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
--  4. TABLES (dining tables)
-- ─────────────────────────────────────────────
CREATE TABLE Tables (
    TableID      INT           AUTO_INCREMENT PRIMARY KEY,
    TableNumber  INT           NOT NULL UNIQUE,
    Capacity     INT           NOT NULL CHECK (Capacity BETWEEN 1 AND 20),
    Location     VARCHAR(100)  DEFAULT 'Main Hall',
    Status       ENUM('available','reserved','occupied','maintenance')
                               DEFAULT 'available'
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
--  5. MENU ITEMS  (extended with CategoryID)
-- ─────────────────────────────────────────────
CREATE TABLE MenuItems (
    DishID          INT            AUTO_INCREMENT PRIMARY KEY,
    CategoryID      INT            NOT NULL,
    DishName        VARCHAR(200)   NOT NULL,
    Price           DECIMAL(10,2)  NOT NULL CHECK (Price > 0),
    Description     TEXT,
    IsAvailable     BOOLEAN        DEFAULT TRUE,
    PreparationTime INT            DEFAULT 15 COMMENT 'minutes',
    CreatedAt       DATETIME       DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_mi_cat FOREIGN KEY (CategoryID)
        REFERENCES Categories (CategoryID)
        ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
--  6. RESERVATIONS
-- ─────────────────────────────────────────────
CREATE TABLE Reservations (
    ReservationID   INT           AUTO_INCREMENT PRIMARY KEY,
    CustomerID      INT           NOT NULL,
    TableID         INT           NOT NULL,
    StaffID         INT,
    DateTime        DATETIME      NOT NULL,
    GuestCount      INT           NOT NULL CHECK (GuestCount >= 1),
    SpecialRequests TEXT,
    Status          ENUM('pending','confirmed','cancelled','completed')
                                  DEFAULT 'pending',
    CreatedAt       DATETIME      DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_res_cust  FOREIGN KEY (CustomerID)  REFERENCES Customers (CustomerID),
    CONSTRAINT fk_res_table FOREIGN KEY (TableID)     REFERENCES Tables    (TableID),
    CONSTRAINT fk_res_staff FOREIGN KEY (StaffID)     REFERENCES Staff     (StaffID)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
--  7. ORDERS
-- ─────────────────────────────────────────────
CREATE TABLE Orders (
    OrderID         INT           AUTO_INCREMENT PRIMARY KEY,
    ReservationID   INT,
    TableID         INT           NOT NULL,
    CustomerID      INT,
    StaffID         INT,
    OrderTime       DATETIME      DEFAULT CURRENT_TIMESTAMP,
    Status          ENUM('open','preparing','served','closed','cancelled')
                                  DEFAULT 'open',
    Notes           TEXT,
    CONSTRAINT fk_ord_res   FOREIGN KEY (ReservationID) REFERENCES Reservations (ReservationID),
    CONSTRAINT fk_ord_table FOREIGN KEY (TableID)        REFERENCES Tables       (TableID),
    CONSTRAINT fk_ord_cust  FOREIGN KEY (CustomerID)     REFERENCES Customers    (CustomerID),
    CONSTRAINT fk_ord_staff FOREIGN KEY (StaffID)        REFERENCES Staff        (StaffID)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
--  8. ORDER DETAILS  (many-to-many: Orders × MenuItems)
-- ─────────────────────────────────────────────
CREATE TABLE OrderDetails (
    OrderDetailID INT            AUTO_INCREMENT PRIMARY KEY,
    OrderID       INT            NOT NULL,
    DishID        INT            NOT NULL,
    Quantity      INT            NOT NULL CHECK (Quantity >= 1),
    UnitPrice     DECIMAL(10,2)  NOT NULL,
    Notes         TEXT,
    CONSTRAINT fk_od_order FOREIGN KEY (OrderID) REFERENCES Orders    (OrderID),
    CONSTRAINT fk_od_dish  FOREIGN KEY (DishID)  REFERENCES MenuItems (DishID)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
--  9. INVOICES
-- ─────────────────────────────────────────────
CREATE TABLE Invoices (
    InvoiceID      INT            AUTO_INCREMENT PRIMARY KEY,
    OrderID        INT            NOT NULL UNIQUE,
    CustomerID     INT,
    SubTotal       DECIMAL(10,2)  NOT NULL DEFAULT 0.00,
    DiscountAmount DECIMAL(10,2)  DEFAULT 0.00,
    ServiceCharge  DECIMAL(10,2)  DEFAULT 0.00,
    TaxAmount      DECIMAL(10,2)  DEFAULT 0.00,
    TotalAmount    DECIMAL(10,2)  NOT NULL DEFAULT 0.00,
    PaymentMethod  ENUM('cash','card','bank_transfer','ewallet') DEFAULT 'cash',
    PaymentDate    DATE,
    Status         ENUM('unpaid','paid','refunded')   DEFAULT 'unpaid',
    CreatedAt      DATETIME       DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_inv_order FOREIGN KEY (OrderID)    REFERENCES Orders    (OrderID),
    CONSTRAINT fk_inv_cust  FOREIGN KEY (CustomerID) REFERENCES Customers (CustomerID)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- 10. PAYMENTS  (supports partial / split payments)
-- ─────────────────────────────────────────────
CREATE TABLE Payments (
    PaymentID      INT            AUTO_INCREMENT PRIMARY KEY,
    InvoiceID      INT            NOT NULL,
    Amount         DECIMAL(10,2)  NOT NULL CHECK (Amount > 0),
    Method         ENUM('cash','card','bank_transfer','ewallet') DEFAULT 'cash',
    PaidAt         DATETIME       DEFAULT CURRENT_TIMESTAMP,
    TransactionRef VARCHAR(100),
    CONSTRAINT fk_pay_inv FOREIGN KEY (InvoiceID) REFERENCES Invoices (InvoiceID)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- 11. TABLE STATUS LOG  (audit trail — trigger-populated)
-- ─────────────────────────────────────────────
CREATE TABLE TableStatusLog (
    LogID       INT    AUTO_INCREMENT PRIMARY KEY,
    TableID     INT    NOT NULL,
    OldStatus   ENUM('available','reserved','occupied','maintenance'),
    NewStatus   ENUM('available','reserved','occupied','maintenance'),
    ChangedAt   DATETIME DEFAULT CURRENT_TIMESTAMP,
    ChangedBy   VARCHAR(100),
    CONSTRAINT fk_log_table FOREIGN KEY (TableID) REFERENCES Tables (TableID)
) ENGINE=InnoDB;

-- ─────────────────────────────────────────────
-- 12. AUDIT LOG  (general change tracking)
-- ─────────────────────────────────────────────
CREATE TABLE AuditLog (
    LogID      INT          AUTO_INCREMENT PRIMARY KEY,
    TableName  VARCHAR(100) NOT NULL,
    Action     ENUM('INSERT','UPDATE','DELETE') NOT NULL,
    RecordID   INT,
    ChangedBy  VARCHAR(100),
    ChangedAt  DATETIME     DEFAULT CURRENT_TIMESTAMP,
    OldValue   JSON,
    NewValue   JSON
) ENGINE=InnoDB;
