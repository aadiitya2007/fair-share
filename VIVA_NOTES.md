# 🎓 Viva Preparation Notes

These notes explain exactly how the new "Real World" features connect to your database logic. Keep these handy during your presentation.

## 1. Password Hashing (Security)
* **What it does:** We replaced plain text passwords with `bcrypt`.
* **Why it matters:** If the database is compromised, hackers cannot see user passwords.
* **How it works:** When someone signs up, Python uses `passlib` to hash the password before running `INSERT INTO Users`. During login, it fetches the hash from MySQL and compares it using `pwd_context.verify()`.

## 2. Server-Side Sessions (Authentication)
* **What it does:** We removed `/dashboard/alice_s` from the URL. The URL is now simply `/groups` or `/group/1`.
* **Why it matters:** Previously, anyone could type another person's username in the URL and see their data. Now, we use `SessionMiddleware`.
* **How it works:** When you log in, Python stores the `user_id` inside an encrypted cookie on the browser. Every single route in `routers/` checks this cookie via `get_current_user()` before running any SQL.

## 3. Transaction Management (Add Expense)
* **What it does:** When adding an expense, we insert 1 row into `Expenses` and multiple rows into `Expense_Splits`.
* **Why it matters:** If the database crashes after inserting the `Expense` but before the `Expense_Splits`, the database would be corrupted. 
* **How it works:** We use a Database Transaction. We do not run `conn.commit()` until the loop finishes successfully. If *any* error occurs, the `try...except` block catches it and runs `conn.rollback()`, ensuring no partial orphan data is saved.

## 4. The Triggers in Action (The best part to demonstrate)
When you present to the faculty, demonstrate this:
1. Go to the dashboard. Show that the Balances say "Nobody owes you money".
2. Click **Add Expense**, enter ₹90 for Food.
3. Show the Dashboard again. It instantly says "Bob owes you ₹30" and "Charlie owes you ₹30".
4. **Explain:** *"Notice that our Python code NEVER ran an `UPDATE` on the `Balances` table. We strictly inserted into `Expenses` and `Expense_Splits`, and the MySQL `AFTER INSERT` trigger automatically calculated the debts in the background. This guarantees data integrity."*

## 5. Fractional Cents (Rounding)
* **What it does:** If an expense is ₹100 split 3 ways, `100/3 = 33.333...`
* **How it works:** Our Python backend (`routers/expenses.py`) handles this mathematically. It rounds `split_amount` to 2 decimals (`33.33`), multiplies by 3 (`99.99`), and calculates the difference (`0.01`). It gives the leftover `0.01` to the first person, ensuring the splits perfectly sum to exactly ₹100.00 before touching the database.
