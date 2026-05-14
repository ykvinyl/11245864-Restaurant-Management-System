-- ============================================================
--  RESTAURANT MANAGEMENT SYSTEM — ADVANCED DATABASE OBJECTS
--  Project 05 | DSEB66B | Spring 2026
--  Covers: Indexes · Views · Stored Procedures · UDFs · Triggers
-- ============================================================
USE RestaurantDB;

-- ═══════════════════════════════════════════════════════════
--  SECTION 1 — INDEXES
--  Optimise frequent queries: reservation lookup, dish search,
--  invoice retrieval, revenue reports.
-- ═══════════════════════════════════════════════════════════

-- 1a. Speed up reservation queries by date range
CREATE INDEX idx_res_datetime    ON Reservations (DateTime);
CREATE INDEX idx_res_status      ON Reservations (Status);
CREATE INDEX idx_res_customer    ON Reservations (CustomerID);

-- 1b. Menu item search by name prefix
CREATE INDEX idx_menu_name       ON MenuItems (DishName);
CREATE INDEX idx_menu_category   ON MenuItems (CategoryID, IsAvailable);

-- 1c. Invoice lookup by payment date and status
CREATE INDEX idx_inv_paydate     ON Invoices (PaymentDate);
CREATE INDEX idx_inv_status      ON Invoices (Status);

-- 1d. Order details aggregation
CREATE INDEX idx_od_dish         ON OrderDetails (DishID);
CREATE INDEX idx_od_order        ON OrderDetails (OrderID);

-- 1e. Table status filtering
CREATE INDEX idx_table_status    ON Tables (Status);

-- EXPLAIN example to prove the index is used:
-- EXPLAIN SELECT * FROM MenuItems WHERE DishName LIKE 'Pho%';
-- EXPLAIN SELECT * FROM Reservations WHERE DateTime BETWEEN '2026-04-01' AND '2026-04-30';


-- ═══════════════════════════════════════════════════════════
--  SECTION 2 — VIEWS
-- ═══════════════════════════════════════════════════════════

-- 2a. Daily reservations with full details (used for front-desk display)
CREATE OR REPLACE VIEW vw_DailyReservations AS
SELECT
    r.ReservationID,
    DATE(r.DateTime)              AS ReservationDate,
    TIME(r.DateTime)              AS ReservationTime,
    c.CustomerName,
    c.PhoneNumber,
    t.TableNumber,
    t.Capacity,
    r.GuestCount,
    r.Status,
    r.SpecialRequests,
    s.StaffName                   AS HandledBy
FROM Reservations r
JOIN Customers c ON r.CustomerID = c.CustomerID
JOIN Tables    t ON r.TableID    = t.TableID
LEFT JOIN Staff s ON r.StaffID   = s.StaffID;

-- 2b. Real-time table availability
CREATE OR REPLACE VIEW vw_TableAvailability AS
SELECT
    t.TableID,
    t.TableNumber,
    t.Capacity,
    t.Location,
    t.Status,
    CASE
        WHEN t.Status = 'available'   THEN 'Ready for seating'
        WHEN t.Status = 'reserved'    THEN 'Has upcoming booking'
        WHEN t.Status = 'occupied'    THEN 'Currently in use'
        WHEN t.Status = 'maintenance' THEN 'Out of service'
    END                           AS StatusDescription,
    COUNT(r.ReservationID)        AS UpcomingReservations
FROM Tables t
LEFT JOIN Reservations r ON t.TableID = r.TableID
    AND r.DateTime  >= NOW()
    AND r.Status IN ('pending', 'confirmed')
GROUP BY t.TableID, t.TableNumber, t.Capacity, t.Location, t.Status;

-- 2c. Top-selling dishes (last 30 days)
CREATE OR REPLACE VIEW vw_TopSellingDishes AS
SELECT
    mi.DishID,
    mi.DishName,
    cat.CategoryName,
    mi.Price,
    SUM(od.Quantity)              AS TotalQuantitySold,
    SUM(od.Quantity * od.UnitPrice) AS TotalRevenue,
    COUNT(DISTINCT od.OrderID)    AS OrderCount,
    RANK() OVER (ORDER BY SUM(od.Quantity) DESC) AS SalesRank
FROM OrderDetails od
JOIN MenuItems  mi  ON od.DishID     = mi.DishID
JOIN Categories cat ON mi.CategoryID = cat.CategoryID
JOIN Orders     o   ON od.OrderID    = o.OrderID
WHERE o.OrderTime >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY mi.DishID, mi.DishName, cat.CategoryName, mi.Price;

-- 2d. Daily revenue summary
CREATE OR REPLACE VIEW vw_DailyRevenue AS
SELECT
    DATE(inv.PaymentDate)         AS RevenueDate,
    COUNT(inv.InvoiceID)          AS InvoiceCount,
    SUM(inv.SubTotal)             AS GrossRevenue,
    SUM(inv.DiscountAmount)       AS TotalDiscounts,
    SUM(inv.ServiceCharge)        AS TotalServiceCharge,
    SUM(inv.TaxAmount)            AS TotalTax,
    SUM(inv.TotalAmount)          AS NetRevenue,
    AVG(inv.TotalAmount)          AS AvgBillAmount
FROM Invoices inv
WHERE inv.Status = 'paid'
GROUP BY DATE(inv.PaymentDate)
ORDER BY RevenueDate DESC;

-- 2e. Customer visit history (for loyalty programme)
CREATE OR REPLACE VIEW vw_CustomerActivity AS
SELECT
    c.CustomerID,
    c.CustomerName,
    c.PhoneNumber,
    c.LoyaltyPoints,
    COUNT(DISTINCT r.ReservationID)  AS TotalReservations,
    COUNT(DISTINCT inv.InvoiceID)    AS TotalInvoices,
    COALESCE(SUM(inv.TotalAmount),0) AS TotalSpent,
    MAX(inv.PaymentDate)             AS LastVisit,
    CASE
        WHEN COALESCE(SUM(inv.TotalAmount),0) >= 5000000 THEN 'Gold'
        WHEN COALESCE(SUM(inv.TotalAmount),0) >= 2000000 THEN 'Silver'
        ELSE 'Bronze'
    END                              AS MembershipTier
FROM Customers c
LEFT JOIN Reservations r   ON c.CustomerID = r.CustomerID
LEFT JOIN Orders       o   ON r.ReservationID = o.ReservationID
LEFT JOIN Invoices     inv ON o.OrderID = inv.OrderID AND inv.Status = 'paid'
GROUP BY c.CustomerID, c.CustomerName, c.PhoneNumber, c.LoyaltyPoints;
-- 2f. Market Basket Data (Hỗ trợ Thuật toán Khuyến nghị món ăn)
-- View này trải phẳng dữ liệu để Python dễ dàng chạy thuật toán Apriori/FP-Growth
CREATE OR REPLACE VIEW vw_MarketBasketData AS
SELECT 
    od.OrderID, 
    mi.DishName, 
    cat.CategoryName
FROM OrderDetails od
JOIN MenuItems mi ON od.DishID = mi.DishID
JOIN Categories cat ON mi.CategoryID = cat.CategoryID
ORDER BY od.OrderID;

-- ═══════════════════════════════════════════════════════════
--  SECTION 3 — STORED PROCEDURES
-- ═══════════════════════════════════════════════════════════
-- 3a. Make a reservation (validates capacity and time conflicts)
DELIMITER //

CREATE PROCEDURE sp_MakeReservation(
    IN p_CustomerID INT,
    IN p_TableID INT,
    IN p_StaffID INT,
    IN p_DateTime DATETIME,
    IN p_GuestCount INT,
    IN p_SpecialRequests VARCHAR(255),
    OUT p_ReservationID INT,
    OUT p_Message VARCHAR(255)
)
-- 1. Gắn nhãn cho khối BEGIN (Ví dụ đặt tên nhãn là 'main_block')
main_block: BEGIN 
    
    DECLARE v_Capacity INT;
    DECLARE v_ExistingReservations INT;

    -- Kiểm tra sức chứa của bàn
    SELECT Capacity INTO v_Capacity FROM Tables WHERE TableID = p_TableID;
    
    IF v_Capacity < p_GuestCount THEN
        SET p_ReservationID = -1;
        SET p_Message = 'Reservation failed: Guest count exceeds table capacity.';
        -- 2. Dùng LEAVE kèm theo đúng tên nhãn đã đặt ở trên
        LEAVE main_block; 
    END IF;

    -- Kiểm tra trùng lịch (Ví dụ: bàn đã được đặt trong khoảng thời gian đó)
    SELECT COUNT(*) INTO v_ExistingReservations
    FROM Reservations
    WHERE TableID = p_TableID 
      AND Status IN ('Confirmed', 'Pending')
      AND ABS(TIMESTAMPDIFF(MINUTE, ReservationTime, p_DateTime)) < 120;

    IF v_ExistingReservations > 0 THEN
        SET p_ReservationID = -1;
        SET p_Message = 'Reservation failed: Table is already booked for this time slot.';
        -- Dùng LEAVE kèm theo đúng tên nhãn
        LEAVE main_block; 
    END IF;

    -- Nếu qua hết các vòng kiểm tra, thực hiện INSERT dữ liệu
    INSERT INTO Reservations (CustomerID, TableID, StaffID, ReservationTime, GuestCount, SpecialRequests, Status)
    VALUES (p_CustomerID, p_TableID, p_StaffID, p_DateTime, p_GuestCount, p_SpecialRequests, 'Confirmed');

    SET p_ReservationID = LAST_INSERT_ID();
    SET p_Message = 'Reservation successfully created.';

-- 3. Đóng khối lệnh kèm theo tên nhãn
END main_block //

DELIMITER ;

-- 3b. Generate invoice for a closed order
DELIMITER //

CREATE PROCEDURE sp_GenerateInvoice(
    IN  p_OrderID         INT,
    IN  p_PaymentMethod   VARCHAR(20),
    IN  p_DiscountPct     DECIMAL(5,2),
    OUT p_InvoiceID       INT,
    OUT p_TotalAmount     DECIMAL(10,2),
    OUT p_Message         VARCHAR(255)
)
-- 1. Gắn nhãn cho khối BEGIN
sp_GenerateInvoice: BEGIN 
    DECLARE v_SubTotal      DECIMAL(10,2);
    DECLARE v_Discount      DECIMAL(10,2);
    DECLARE v_ServiceCharge DECIMAL(10,2);
    DECLARE v_Tax           DECIMAL(10,2);
    DECLARE v_Total         DECIMAL(10,2);
    DECLARE v_CustomerID    INT;
    DECLARE v_Existing      INT;

    -- Check if invoice already exists
    SELECT COUNT(*) INTO v_Existing FROM Invoices WHERE OrderID = p_OrderID;
    IF v_Existing > 0 THEN
        SET p_InvoiceID   = -1;
        SET p_TotalAmount = 0;
        SET p_Message     = 'Invoice already exists for this order';
        -- Thoát bằng đúng tên nhãn
        LEAVE sp_GenerateInvoice; 
    END IF;

    -- Calculate subtotal from order details (Đã fix lỗi NULL bằng LEFT JOIN và COALESCE)
    SELECT COALESCE(SUM(od.Quantity * od.UnitPrice), 0), o.CustomerID 
    INTO v_SubTotal, v_CustomerID
    FROM Orders o
    LEFT JOIN OrderDetails od ON o.OrderID = od.OrderID
    WHERE o.OrderID = p_OrderID
    GROUP BY o.CustomerID;

    -- Apply discount, service charge (5%), tax (10%)
    SET v_Discount = ROUND(v_SubTotal * (p_DiscountPct / 100), 2);
    SET v_ServiceCharge = ROUND((v_SubTotal - v_Discount) * 0.05, 2);
    
    -- 2. ĐÃ BỔ SUNG CÔNG THỨC TÍNH TAX VÀ TOTAL BỊ THIẾU
    SET v_Tax = ROUND((v_SubTotal - v_Discount + v_ServiceCharge) * 0.10, 2);
    SET v_Total = v_SubTotal - v_Discount + v_ServiceCharge + v_Tax;

    -- Insert invoice
    INSERT INTO Invoices
        (OrderID, CustomerID, SubTotal, DiscountAmount, ServiceCharge, TaxAmount, TotalAmount, PaymentMethod, PaymentDate, Status)
    VALUES
        (p_OrderID, v_CustomerID, v_SubTotal, v_Discount, v_ServiceCharge, v_Tax, v_Total, p_PaymentMethod, CURRENT_DATE, 'paid');

    SET p_InvoiceID   = LAST_INSERT_ID();
    SET p_TotalAmount = v_Total;
    SET p_Message     = CONCAT('Invoice #', p_InvoiceID, ' created. Total: ', FORMAT(v_Total, 0), ' VND');

    -- Close the order
    UPDATE Orders SET Status = 'closed' WHERE OrderID = p_OrderID;

    -- Award loyalty points (1 point per 10,000 VND spent)
    UPDATE Customers
    SET LoyaltyPoints = LoyaltyPoints + FLOOR(v_Total / 10000)
    WHERE CustomerID = v_CustomerID;

-- 3. Đóng nhãn ở cuối
END sp_GenerateInvoice //

DELIMITER ;

-- 3c. Monthly revenue report
DELIMITER $$
CREATE PROCEDURE sp_MonthlyRevenue(
    IN p_Year  INT,
    IN p_Month INT
)
BEGIN
    SELECT
        DATE(PaymentDate)             AS Day,
        COUNT(InvoiceID)              AS Bills,
        SUM(TotalAmount)              AS Revenue,
        SUM(DiscountAmount)           AS Discounts,
        AVG(TotalAmount)              AS AvgBill
    FROM Invoices
    WHERE YEAR(PaymentDate)  = p_Year
      AND MONTH(PaymentDate) = p_Month
      AND Status = 'paid'
    GROUP BY DATE(PaymentDate)
    ORDER BY Day;
END$$

DELIMITER ;


-- ═══════════════════════════════════════════════════════════
--  SECTION 4 — USER-DEFINED FUNCTIONS
-- ═══════════════════════════════════════════════════════════
DELIMITER $$

-- 4a. Calculate dynamic discount based on loyalty tier
CREATE FUNCTION fn_GetDiscount(p_LoyaltyPoints INT)
RETURNS DECIMAL(5,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    RETURN CASE
        WHEN p_LoyaltyPoints >= 1000 THEN 10.00  -- Gold: 10% discount
        WHEN p_LoyaltyPoints >= 500  THEN  7.00  -- Silver: 7%
        WHEN p_LoyaltyPoints >= 200  THEN  5.00  -- Bronze+: 5%
        ELSE                               0.00  -- Standard: no discount
    END;
END$$

-- 4b. Calculate service charge based on table location (VIP = 7%, standard = 5%)
CREATE FUNCTION fn_ServiceCharge(p_TableID INT, p_SubTotal DECIMAL(10,2))
RETURNS DECIMAL(10,2)
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_Location VARCHAR(100);
    DECLARE v_Rate     DECIMAL(4,2);

    SELECT Location INTO v_Location FROM Tables WHERE TableID = p_TableID;

    SET v_Rate = CASE v_Location
        WHEN 'VIP Room'     THEN 0.07
        WHEN 'Private Room' THEN 0.07
        WHEN 'Banquet Hall' THEN 0.08
        ELSE                     0.05
    END;

    RETURN ROUND(p_SubTotal * v_Rate, 2);
END$$

-- 4c. Format amount as VND string
CREATE FUNCTION fn_FormatVND(p_Amount DECIMAL(15,2))
RETURNS VARCHAR(50)
DETERMINISTIC
NO SQL
BEGIN
    RETURN CONCAT(FORMAT(p_Amount, 0), ' VND');
END$$

-- 4d. Calculate estimated preparation time for an entire order
CREATE FUNCTION fn_OrderPrepTime(p_OrderID INT)
RETURNS INT
DETERMINISTIC
READS SQL DATA
BEGIN
    DECLARE v_MaxPrepTime INT;
    -- Kitchen works in parallel, so total time = MAX item prep time
    SELECT MAX(mi.PreparationTime) INTO v_MaxPrepTime
    FROM OrderDetails od
    JOIN MenuItems mi ON od.DishID = mi.DishID
    WHERE od.OrderID = p_OrderID;
    RETURN COALESCE(v_MaxPrepTime, 0);
END$$

DELIMITER ;


-- ═══════════════════════════════════════════════════════════
--  SECTION 5 — TRIGGERS
-- ═══════════════════════════════════════════════════════════
DELIMITER $$

-- 5a. Auto-update table status to 'occupied' when a new order opens
CREATE TRIGGER trg_OrderOpen_UpdateTable
AFTER INSERT ON Orders
FOR EACH ROW
BEGIN
    IF NEW.Status = 'open' THEN
        UPDATE Tables
        SET Status = 'occupied'
        WHERE TableID = NEW.TableID;
    END IF;
END$$

-- 5b. Auto-release table to 'available' when order is closed/cancelled
CREATE TRIGGER trg_OrderClose_UpdateTable
AFTER UPDATE ON Orders
FOR EACH ROW
BEGIN
    IF NEW.Status IN ('closed', 'cancelled') AND OLD.Status NOT IN ('closed','cancelled') THEN
        UPDATE Tables
        SET Status = 'available'
        WHERE TableID = NEW.TableID;
    END IF;
END$$

-- 5c. Log every table status change for auditing
CREATE TRIGGER trg_TableStatusChange
AFTER UPDATE ON Tables
FOR EACH ROW
BEGIN
    IF OLD.Status <> NEW.Status THEN
        INSERT INTO TableStatusLog (TableID, OldStatus, NewStatus, ChangedAt, ChangedBy)
        VALUES (NEW.TableID, OLD.Status, NEW.Status, NOW(), USER());
    END IF;
END$$

-- 5d. Auto-set UnitPrice from current menu price when an order detail is inserted
CREATE TRIGGER trg_OrderDetail_SetPrice
BEFORE INSERT ON OrderDetails
FOR EACH ROW
BEGIN
    DECLARE v_Price DECIMAL(10,2);
    SELECT Price INTO v_Price FROM MenuItems WHERE DishID = NEW.DishID;
    -- Only set if caller didn't explicitly provide a price
    IF NEW.UnitPrice IS NULL OR NEW.UnitPrice = 0 THEN
        SET NEW.UnitPrice = v_Price;
    END IF;
END$$

-- 5e. Prevent booking a table with status 'maintenance'
CREATE TRIGGER trg_PreventMaintenanceReservation
BEFORE INSERT ON Reservations
FOR EACH ROW
BEGIN
    DECLARE v_Status VARCHAR(20);
    SELECT Status INTO v_Status FROM Tables WHERE TableID = NEW.TableID;
    IF v_Status = 'maintenance' THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Cannot reserve a table that is under maintenance';
    END IF;
END$$

-- 5f. Auto-mark reservation 'completed' when order closes
CREATE TRIGGER trg_OrderClosed_CompleteReservation
AFTER UPDATE ON Orders
FOR EACH ROW
BEGIN
    IF NEW.Status = 'closed' AND OLD.Status <> 'closed' AND NEW.ReservationID IS NOT NULL THEN
        UPDATE Reservations
        SET Status = 'completed'
        WHERE ReservationID = NEW.ReservationID;
    END IF;
END$$

DELIMITER ;

DELIMITER //

CREATE TRIGGER trg_AfterReservationInsert
AFTER INSERT ON Reservations
FOR EACH ROW
BEGIN
    -- Tự động cập nhật trạng thái bàn thành 'Reserved' khi có khách đặt
    UPDATE Tables 
    SET Status = 'Reserved' 
    WHERE TableID = NEW.TableID;
END //

DELIMITER ;


-- ═══════════════════════════════════════════════════════════
--  QUICK VERIFICATION QUERIES
-- ═══════════════════════════════════════════════════════════
-- SELECT * FROM vw_TableAvailability;
-- SELECT * FROM vw_TopSellingDishes;
-- SELECT * FROM vw_DailyRevenue;
-- SELECT * FROM vw_CustomerActivity ORDER BY TotalSpent DESC;
-- SELECT fn_GetDiscount(850), fn_FormatVND(2597588);
-- CALL sp_MonthlyRevenue(2026, 4);
