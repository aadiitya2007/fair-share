-- ============================================================================
-- Fair Share: Core Operational Queries
-- ============================================================================
-- Note: This file is for documentation and grading purposes to highlight the 
-- DBMS concepts (JOINs, UNIONs, GROUP BY, Transactions) used in the project. 
-- In the live app, these queries are executed dynamically inside the Python 
-- backend (`app/routers/`) using parameterized inputs (represented here by `?`).


-- ----------------------------------------------------------------------------
-- 1. COMPLEX NOTIFICATIONS ENGINE (UNION ALL & JOINS)
-- Location: app/routers/reminders.py
-- Concept: Combines 5 different tables into a single chronological feed.
-- ----------------------------------------------------------------------------
SELECT 'reminder' as type, r.sent_at as timestamp, u.first_name as actor, g.group_name, 'sent you a reminder.' as action
FROM Reminders r
JOIN Users u ON r.sender_id = u.user_id
JOIN Expenses e ON r.expense_id = e.expense_id
JOIN Groups_Table g ON e.group_id = g.group_id
WHERE r.receiver_id = ?

UNION ALL

SELECT 'payment' as type, p.paid_at as timestamp, u.first_name as actor, g.group_name, concat('paid you ₹', p.amount, '.') as action
FROM Payments p
JOIN Users u ON p.paid_by_user_id = u.user_id
JOIN Groups_Table g ON p.group_id = g.group_id
WHERE p.paid_to_user_id = ?

UNION ALL

SELECT 'expense' as type, e.created_at as timestamp, u.first_name as actor, g.group_name, concat('added an expense: ', e.description, '.') as action
FROM Expense_Splits es
JOIN Expenses e ON es.expense_id = e.expense_id
JOIN Users u ON e.paid_by_user_id = u.user_id
JOIN Groups_Table g ON e.group_id = g.group_id
WHERE es.user_id = ? AND e.paid_by_user_id != ?

UNION ALL

SELECT 'join_request' as type, gr.created_at as timestamp, u.first_name as actor, g.group_name, 'requested to join.' as action
FROM Group_Requests gr
JOIN Users u ON gr.user_id = u.user_id
JOIN Groups_Table g ON gr.group_id = g.group_id
JOIN Group_Members gm ON g.group_id = gm.group_id
WHERE gm.user_id = ? AND gm.role = 'Admin' AND gr.status = 'Pending'

ORDER BY timestamp DESC LIMIT 20;


-- ----------------------------------------------------------------------------
-- 2. FETCHING ACTIVE DEBTS (Derived from Cache Table)
-- Location: app/routers/groups.py
-- Concept: Inner Joins to translate raw foreign keys into human-readable names.
-- ----------------------------------------------------------------------------
-- Find out who owes the current user money in a specific group:
SELECT borrower.user_id, borrower.first_name, b.total_amount 
FROM Balances b 
JOIN Users borrower ON b.borrower_id = borrower.user_id 
WHERE b.lender_id = ? AND b.group_id = ? AND b.total_amount > 0;

-- Find out who the current user owes money to:
SELECT lender.user_id, lender.first_name, b.total_amount 
FROM Balances b 
JOIN Users lender ON b.lender_id = lender.user_id 
WHERE b.borrower_id = ? AND b.group_id = ? AND b.total_amount > 0;


-- ----------------------------------------------------------------------------
-- 3. EXPENSE ANALYTICS (AGGREGATION)
-- Location: app/routers/groups.py
-- Concept: Uses GROUP BY and Aggregation (SUM) to feed the Chart.js pie chart.
-- ----------------------------------------------------------------------------
SELECT COALESCE(category, 'Other') as category, SUM(amount) as total 
FROM Expenses 
WHERE group_id = ? 
GROUP BY category;


-- ----------------------------------------------------------------------------
-- 4. ACID TRANSACTION (INSERTING EXPENSE & SPLITS)
-- Location: app/routers/expenses.py
-- Concept: Transactional integrity. If a split fails, the expense is rolled back.
-- ----------------------------------------------------------------------------
START TRANSACTION;

-- Step 1: Insert the parent expense record
INSERT INTO Expenses (group_id, paid_by_user_id, amount, description, expense_date, category) 
VALUES (?, ?, ?, ?, ?, ?);

-- Step 2: Retrieve the auto-generated ID for the new expense
SET @last_expense_id = LAST_INSERT_ID();

-- Step 3: Insert multiple child records for the splits
INSERT INTO Expense_Splits (expense_id, user_id, split_amount) 
VALUES (@last_expense_id, ?, ?);
INSERT INTO Expense_Splits (expense_id, user_id, split_amount) 
VALUES (@last_expense_id, ?, ?);
-- (Repeated dynamically for N members)

COMMIT; -- Or ROLLBACK if any step fails


-- ----------------------------------------------------------------------------
-- 5. FETCHING TRANSACTION HISTORY (Data Transformation)
-- Location: app/routers/groups.py
-- Concept: Projecting unified columns from entirely different transaction types.
-- ----------------------------------------------------------------------------
-- Fetch Expenses
SELECT 'expense' as type, e.expense_id, e.description, e.amount, DATE(e.expense_date) as date, e.category, u.first_name as payer_name, '' as receiver_name
FROM Expenses e JOIN Users u ON e.paid_by_user_id = u.user_id
WHERE e.group_id = ?

UNION ALL

-- Fetch Peer-to-Peer Payments
SELECT 'payment' as type, p.payment_id as expense_id, 'Settled up' as description, p.amount, DATE(p.paid_at) as date, '' as category, u1.first_name as payer_name, u2.first_name as receiver_name
FROM Payments p 
JOIN Users u1 ON p.paid_by_user_id = u1.user_id
JOIN Users u2 ON p.paid_to_user_id = u2.user_id
WHERE p.group_id = ?;


-- ----------------------------------------------------------------------------
-- 6. SECURITY: SECURE LOGIN
-- Location: app/routers/auth.py
-- Concept: Fetching a user by email to compare bcrypt password hashes in Python.
-- ----------------------------------------------------------------------------
SELECT user_id, first_name, password_hash 
FROM Users 
WHERE email = ?;

-- ==============================================================================
-- 5. DATABASE VIEWS (Virtual Tables for simplified querying)
-- ==============================================================================

-- VIEW 1: Group Member Financial Summary
-- This view abstracts the complexity of joining Users, Group_Members, and Balances.
-- It provides a quick, read-only snapshot of every user's net financial standing in each group.
CREATE OR REPLACE VIEW vw_group_financial_summary AS
SELECT 
    g.group_name,
    u.user_name,
    u.first_name,
    COALESCE(SUM(b.total_amount), 0) AS total_amount_owed_to_others
FROM 
    Groups_Table g
JOIN 
    Group_Members gm ON g.group_id = gm.group_id
JOIN 
    Users u ON gm.user_id = u.user_id
LEFT JOIN 
    Balances b ON b.group_id = g.group_id AND b.borrower_id = u.user_id
GROUP BY 
    g.group_id, u.user_id;

-- How to use this view (Example for Evaluator):
-- SELECT * FROM vw_group_financial_summary WHERE group_name = 'Goa Trip';
