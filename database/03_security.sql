-- ============================================================
--  RESTAURANT MANAGEMENT SYSTEM — SECURITY & ADMINISTRATION
--  Project 05 | DSEB66B | Spring 2026
-- ============================================================
USE RestaurantDB;

-- ═══════════════════════════════════════════════════════════
--  SECTION 1 — USER ROLES & PRIVILEGE ASSIGNMENT
-- ═══════════════════════════════════════════════════════════

-- Drop existing users if they exist (for clean re-run)
DROP USER IF EXISTS 'rms_admin'   @'localhost';
DROP USER IF EXISTS 'rms_manager' @'localhost';
DROP USER IF EXISTS 'rms_cashier' @'localhost';
DROP USER IF EXISTS 'rms_waiter'  @'localhost';
DROP USER IF EXISTS 'rms_chef'    @'localhost';
DROP USER IF EXISTS 'rms_report'  @'localhost';

-- ─────────────────────────────────────────────
--  Role 1: ADMIN  — full control
-- ─────────────────────────────────────────────
CREATE USER 'rms_admin'@'localhost' IDENTIFIED BY 'Admin@Secure2026!';
GRANT ALL PRIVILEGES ON RestaurantDB.* TO 'rms_admin'@'localhost' WITH GRANT OPTION;

-- ─────────────────────────────────────────────
--  Role 2: MANAGER — read/write, no schema change, no drop
-- ─────────────────────────────────────────────
CREATE USER 'rms_manager'@'localhost' IDENTIFIED BY 'Manager@Secure2026!';
GRANT SELECT, INSERT, UPDATE ON RestaurantDB.Customers       TO 'rms_manager'@'localhost';
GRANT SELECT, INSERT, UPDATE ON RestaurantDB.Staff           TO 'rms_manager'@'localhost';
GRANT SELECT, INSERT, UPDATE ON RestaurantDB.Tables          TO 'rms_manager'@'localhost';
GRANT SELECT, INSERT, UPDATE ON RestaurantDB.MenuItems       TO 'rms_manager'@'localhost';
GRANT SELECT, INSERT, UPDATE ON RestaurantDB.Categories      TO 'rms_manager'@'localhost';
GRANT SELECT, INSERT, UPDATE ON RestaurantDB.Reservations    TO 'rms_manager'@'localhost';
GRANT SELECT, INSERT, UPDATE ON RestaurantDB.Orders          TO 'rms_manager'@'localhost';
GRANT SELECT, INSERT, UPDATE ON RestaurantDB.OrderDetails    TO 'rms_manager'@'localhost';
GRANT SELECT, INSERT, UPDATE ON RestaurantDB.Invoices        TO 'rms_manager'@'localhost';
GRANT SELECT, INSERT        ON RestaurantDB.Payments         TO 'rms_manager'@'localhost';
GRANT SELECT                ON RestaurantDB.AuditLog         TO 'rms_manager'@'localhost';
GRANT SELECT                ON RestaurantDB.TableStatusLog   TO 'rms_manager'@'localhost';
-- Views
GRANT SELECT ON RestaurantDB.vw_DailyRevenue        TO 'rms_manager'@'localhost';
GRANT SELECT ON RestaurantDB.vw_TopSellingDishes     TO 'rms_manager'@'localhost';
GRANT SELECT ON RestaurantDB.vw_CustomerActivity     TO 'rms_manager'@'localhost';
GRANT SELECT ON RestaurantDB.vw_DailyReservations    TO 'rms_manager'@'localhost';
GRANT SELECT ON RestaurantDB.vw_TableAvailability    TO 'rms_manager'@'localhost';
-- Procedures
GRANT EXECUTE ON PROCEDURE RestaurantDB.sp_MonthlyRevenue    TO 'rms_manager'@'localhost';
GRANT EXECUTE ON PROCEDURE RestaurantDB.sp_GenerateInvoice   TO 'rms_manager'@'localhost';
GRANT EXECUTE ON PROCEDURE RestaurantDB.sp_MakeReservation   TO 'rms_manager'@'localhost';

-- ─────────────────────────────────────────────
--  Role 3: CASHIER — billing and payments only
-- ─────────────────────────────────────────────
CREATE USER 'rms_cashier'@'localhost' IDENTIFIED BY 'Cashier@Secure2026!';
GRANT SELECT            ON RestaurantDB.Orders           TO 'rms_cashier'@'localhost';
GRANT SELECT            ON RestaurantDB.OrderDetails     TO 'rms_cashier'@'localhost';
GRANT SELECT            ON RestaurantDB.MenuItems        TO 'rms_cashier'@'localhost';
GRANT SELECT            ON RestaurantDB.Customers        TO 'rms_cashier'@'localhost';
GRANT SELECT, INSERT, UPDATE ON RestaurantDB.Invoices    TO 'rms_cashier'@'localhost';
GRANT SELECT, INSERT        ON RestaurantDB.Payments     TO 'rms_cashier'@'localhost';
GRANT SELECT            ON RestaurantDB.vw_DailyRevenue  TO 'rms_cashier'@'localhost';
GRANT EXECUTE ON PROCEDURE RestaurantDB.sp_GenerateInvoice TO 'rms_cashier'@'localhost';

-- ─────────────────────────────────────────────
--  Role 4: WAITER — orders and reservations
-- ─────────────────────────────────────────────

-- Bước 1: Tạo View che dữ liệu khách hàng
CREATE OR REPLACE VIEW vw_SafeCustomers AS
SELECT 
    CustomerID,
    CustomerName,
    CONCAT('***-***-', RIGHT(PhoneNumber, 4)) AS MaskedPhone, -- Che số điện thoại, chỉ hiện 4 số cuối
    LoyaltyPoints
FROM Customers;

-- Bước 2: TẠO TÀI KHOẢN TRƯỚC (Rất quan trọng - Không được để sau lệnh GRANT)
CREATE USER 'rms_waiter'@'localhost' IDENTIFIED BY 'Waiter@Secure2026!';

-- Bước 3: TIẾN HÀNH CẤP QUYỀN TRÊN TÀI KHOẢN ĐÃ TẠO
GRANT SELECT ON RestaurantDB.vw_SafeCustomers TO 'rms_waiter'@'localhost';
GRANT SELECT, INSERT, UPDATE ON RestaurantDB.Orders         TO 'rms_waiter'@'localhost';
GRANT SELECT, INSERT, UPDATE ON RestaurantDB.OrderDetails   TO 'rms_waiter'@'localhost';
GRANT SELECT, INSERT, UPDATE ON RestaurantDB.Reservations   TO 'rms_waiter'@'localhost';
GRANT SELECT, UPDATE         ON RestaurantDB.Tables         TO 'rms_waiter'@'localhost';
GRANT SELECT                 ON RestaurantDB.MenuItems      TO 'rms_waiter'@'localhost';
GRANT SELECT                 ON RestaurantDB.vw_TableAvailability  TO 'rms_waiter'@'localhost';
GRANT SELECT                 ON RestaurantDB.vw_DailyReservations  TO 'rms_waiter'@'localhost';
GRANT EXECUTE ON PROCEDURE RestaurantDB.sp_MakeReservation  TO 'rms_waiter'@'localhost';

-- ─────────────────────────────────────────────
--  Role 5: CHEF — read-only on orders and menu
-- ─────────────────────────────────────────────
CREATE USER 'rms_chef'@'localhost' IDENTIFIED BY 'Chef@Secure2026!';
GRANT SELECT            ON RestaurantDB.Orders          TO 'rms_chef'@'localhost';
GRANT SELECT            ON RestaurantDB.OrderDetails    TO 'rms_chef'@'localhost';
GRANT SELECT            ON RestaurantDB.MenuItems       TO 'rms_chef'@'localhost';
GRANT SELECT            ON RestaurantDB.Categories      TO 'rms_chef'@'localhost';
GRANT UPDATE (IsAvailable, PreparationTime)
                        ON RestaurantDB.MenuItems       TO 'rms_chef'@'localhost';

-- ─────────────────────────────────────────────
--  Role 6: REPORT (read-only analytics account)
-- ─────────────────────────────────────────────
CREATE USER 'rms_report'@'localhost' IDENTIFIED BY 'Report@Secure2026!';
GRANT SELECT ON RestaurantDB.vw_DailyRevenue        TO 'rms_report'@'localhost';
GRANT SELECT ON RestaurantDB.vw_TopSellingDishes     TO 'rms_report'@'localhost';
GRANT SELECT ON RestaurantDB.vw_CustomerActivity     TO 'rms_report'@'localhost';
GRANT SELECT ON RestaurantDB.vw_DailyReservations    TO 'rms_report'@'localhost';
GRANT SELECT ON RestaurantDB.vw_TableAvailability    TO 'rms_report'@'localhost';
GRANT EXECUTE ON PROCEDURE RestaurantDB.sp_MonthlyRevenue TO 'rms_report'@'localhost';

-- FLUSH PRIVILEGES;

-- ═══════════════════════════════════════════════════════════
--  SECTION 2 — BACKUP & RECOVERY STRATEGY
-- ═══════════════════════════════════════════════════════════

-- Full backup command (run from shell, not MySQL):
-- mysqldump -u rms_admin -p --single-transaction --routines --triggers \
--   --events RestaurantDB > RestaurantDB_backup_$(date +%Y%m%d_%H%M).sql

-- Restore command:
-- mysql -u rms_admin -p RestaurantDB < RestaurantDB_backup_20260425_0200.sql

-- Recommended cron schedule:
-- Full backup  : every day at 2:00 AM
-- Incremental  : MySQL binlog enabled (log_bin=ON in my.cnf)
-- Retention    : Keep 7 daily + 4 weekly + 12 monthly snapshots


-- ═══════════════════════════════════════════════════════════
--  SECTION 3 — PERFORMANCE TUNING NOTES (documented)
-- ═══════════════════════════════════════════════════════════

-- 3a. Check which indexes are being used
-- SELECT * FROM performance_schema.table_io_waits_summary_by_index_usage
--   WHERE OBJECT_SCHEMA = 'RestaurantDB' ORDER BY SUM_TIMER_WAIT DESC;

-- 3b. Identify slow queries (must enable slow_query_log=ON in my.cnf)
-- SELECT * FROM mysql.slow_log ORDER BY query_time DESC LIMIT 20;

-- 3c. Analyze query execution plan
-- EXPLAIN ANALYZE
--   SELECT c.CustomerName, SUM(inv.TotalAmount)
--   FROM Customers c
--   JOIN Invoices inv ON c.CustomerID = inv.CustomerID
--   WHERE inv.Status = 'paid'
--   GROUP BY c.CustomerID;
