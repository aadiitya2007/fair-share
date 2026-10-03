# Viva Preparation Notes

This document contains straightforward answers to common professor questions regarding the database and backend architecture of Fair Share.

## 1. Why did you use a `Balances` table instead of just calculating debts on the fly?
**Answer:** Performance and scalability. If we calculate debts on the fly, every time a user opens the dashboard, the database has to scan and sum up every single expense and payment they have ever been part of (which is an $O(N)$ operation). By creating a `Balances` table, we cache the final result. The dashboard simply does a direct $O(1)$ lookup.

## 2. What is a Trigger, and how did you use it?
**Answer:** A trigger is a set of SQL instructions that automatically execute in response to an `INSERT`, `UPDATE`, or `DELETE` event. In this project, I wrote two triggers: `after_expense_split_insert` and `after_payment_insert`. They automatically update the `Balances` table in real-time whenever an expense or payment happens, guaranteeing that the cache is always 100% mathematically correct.

## 3. What is a Database Transaction? Did you use them?
**Answer:** A transaction is a sequence of SQL operations that must entirely succeed or entirely fail together (the "Atomicity" in ACID). Yes, I used them extensively. For example, when adding an expense, we insert into `Expenses` and multiple rows into `Expense_Splits`. If one split fails to insert, we do a `conn.rollback()` to undo everything. If it succeeds, we `conn.commit()`. This prevents corrupted data where an expense exists without its splits.

## 4. Why is your data normalized?
**Answer:** To eliminate data redundancy and anomalies. For example, instead of storing a comma-separated list of group members in a single row, I created a `Group_Members` junction table (1st Normal Form). This allows us to easily query members, assign roles (Admin/Member), and securely delete a user using `ON DELETE CASCADE` without breaking the database.

## 5. What happens if two people pay each other at the exact same moment? (Concurrency)
**Answer:** Because we rely on MySQL, it uses Row-Level Locking (InnoDB engine). If two payments happen simultaneously between Alice and Bob, the database will lock the specific row in the `Balances` table for the first transaction. The second transaction must wait for the lock to be released. This prevents "race conditions" where balance updates overwrite each other.

## 6. Why did you use `DECIMAL(10,2)` for money instead of `FLOAT` or `DOUBLE`?
**Answer:** `FLOAT` and `DOUBLE` use binary floating-point math, which can cause precision errors (e.g., `0.1 + 0.2 = 0.30000000000000004`). Money requires exact decimal math to the penny. `DECIMAL(10,2)` stores up to 8 digits before the decimal and exactly 2 digits after, ensuring perfect accuracy for financial transactions.

## 7. How does the real-time notification system work?
**Answer:** We wrote a unified `UNION ALL` SQL query that pulls the latest data from `Expenses`, `Payments`, `Reminders`, and `Group_Requests`. The frontend Javascript runs an asynchronous `fetch()` polling loop every 10 seconds. If the query returns a new timestamp, the JavaScript automatically triggers a notification toast and reloads the balances smoothly without a hard page refresh.
