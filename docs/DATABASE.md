# Database Architecture

This document describes the schema and design decisions for the Fair Share MySQL database.

## Entity-Relationship Overview

The database is built around **Users**, **Groups**, and **Expenses**. 

- **Users** can belong to many **Groups** (Many-to-Many via `Group_Members`).
- An **Expense** is paid by one User, but split among many Users (Many-to-Many via `Expense_Splits`).
- **Balances** is a specialized cache table that represents the final computed debt graph between users.

## Table Details

### `Users`
Stores authentication and profile data. Passwords are encrypted using `bcrypt`.
- **Keys**: `user_id` (PK)

### `Groups_Table`
Stores groups (e.g., "Goa Trip", "Hostel"). 
- **Keys**: `group_id` (PK)

### `Group_Members`
Junction table linking Users to Groups. Tracks whether a user is an 'Admin' or 'Member'.
- **Keys**: `(user_id, group_id)` (Composite PK)

### `Expenses`
The core transaction record. Tracks who paid the total amount, and when.
- **Keys**: `expense_id` (PK)
- **Foreign Keys**: `group_id`, `paid_by_user_id`

### `Expense_Splits`
Junction table detailing exactly how an Expense is divided. If Alice pays ₹900, the splits might be Alice (300), Bob (300), Charlie (300).
- **Keys**: `split_id` (PK)
- **Foreign Keys**: `expense_id`, `user_id`

### `Payments`
Records direct peer-to-peer settlements (e.g., Bob pays Alice ₹150).
- **Keys**: `payment_id` (PK)
- **Foreign Keys**: `group_id`, `paid_by_user_id`, `paid_to_user_id`

### `Balances` (The Cache Table)
**Crucial Design Decision:** Calculating debts recursively via SUM(Expenses) - SUM(Payments) across thousands of transactions is extremely slow ($O(N)$ computation per load). Instead, we use a **cache table** called `Balances`.

- **Rules enforced by Constraints**:
  - `lender_id != borrower_id` (No self-debt).
  - `total_amount >= 0` (No negative balances. A negative balance simply reverses the `lender_id` and `borrower_id`).
  - `UNIQUE(group_id, lender_id, borrower_id)` (Only one directed edge between two nodes).

- **Rules enforced by Triggers**:
  - `after_expense_split_insert`: Automatically creates or updates debts when an expense is split.
  - `after_payment_insert`: Automatically reduces debts when a settlement payment is recorded.
  - **Netting**: If Bob owes Alice ₹300, and Alice borrows ₹100 from Bob, the triggers automatically net this out so Bob just owes Alice ₹200.

### `Reminders` & `Group_Requests`
Auxiliary tables for the real-time notification engine.

---

## Sample Queries

**1. Calculate total money owed to a user globally:**
```sql
SELECT SUM(total_amount) 
FROM Balances 
WHERE lender_id = 1;
```

**2. Fetch all expenses in a group with the payer's name:**
```sql
SELECT e.description, e.amount, u.first_name 
FROM Expenses e 
JOIN Users u ON e.paid_by_user_id = u.user_id 
WHERE e.group_id = 1 
ORDER BY e.expense_date DESC;
```
