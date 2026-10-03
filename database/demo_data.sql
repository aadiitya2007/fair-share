-- ==========================================
-- Fair Share Demo Data
-- ==========================================
-- Logins:
-- alice@example.com / password123
-- bob@example.com / password123
-- charlie@example.com / password123

INSERT INTO Users (first_name, last_name, user_name, email, password_hash, date_of_birth) VALUES
('Alice', 'Smith', 'alice_s', 'alice@example.com', '$2b$12$FTR6p04sIqZ.7.SRxXsNnONGCqDfV7oAS8oE5G3DqqZDHwRq0H5uq', '2000-01-01'),
('Bob', 'Jones', 'bobj', 'bob@example.com', '$2b$12$/GVO9WsizTeWPlB13thYZey6Gr8aoeK/Fe1YUpSgQ0w1s.qIsA.9C', '1999-05-15'),
('Charlie', 'Brown', 'charlieb', 'charlie@example.com', '$2b$12$bcM0H56QkTTI4hllVI8RxOUbR0ccYS1vh0.hHNHCLK7Qy/X4/BQMW', '2001-10-20');

INSERT INTO Groups_Table (group_name, description) VALUES
('Goa Trip 2026', 'College trip to Goa');

INSERT INTO Group_Members (user_id, group_id, role) VALUES
(1, 1, 'Admin'),
(2, 1, 'Member'),
(3, 1, 'Member');

-- Alice pays 900 for dinner, split equally 3 ways.
-- Trigger will auto-create Balances: Bob owes Alice 300, Charlie owes Alice 300.
INSERT INTO Expenses (group_id, paid_by_user_id, amount, description, expense_date, category) VALUES
(1, 1, 900.00, 'Seafood Dinner', '2026-10-01', 'Food');

SET @last_exp = LAST_INSERT_ID();

INSERT INTO Expense_Splits (expense_id, user_id, split_amount) VALUES
(@last_exp, 1, 300.00),
(@last_exp, 2, 300.00),
(@last_exp, 3, 300.00);

-- Bob pays Alice back 150.
-- Trigger will reduce Bob's debt to Alice to 150.
INSERT INTO Payments (group_id, paid_by_user_id, paid_to_user_id, amount) VALUES
(1, 2, 1, 150.00);
