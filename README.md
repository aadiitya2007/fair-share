# Fair Share - Expense Management (DBMS Project)

A production-quality web application for splitting expenses, demonstrating complex MySQL database constraints, triggers, and transaction management via Python FastAPI.

## Tech Stack
* **Backend:** Python 3.9, FastAPI, Uvicorn, Jinja2
* **Database:** MySQL 8, mysql-connector-python
* **Security:** bcrypt (Password Hashing), SessionMiddleware (Authentication)
* **Frontend:** Bootstrap 5, Chart.js, HTML5

## Setup Instructions

1. **Activate Virtual Environment**
   ```bash
   source venv/bin/activate
   ```
2. **Install Requirements**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure Database (.env)**
   Ensure your `.env` file contains your local MySQL credentials:
   ```env
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_password_here
   DB_NAME=FairShare_DB
   SESSION_SECRET=supersecret-viva-key-123
   ```
4. **Prepare Demo Accounts (Important!)**
   Because we upgraded to **bcrypt password hashing**, old plain-text passwords in MySQL won't work. Run this script to re-hash the demo users (`alice_s`, `bobby_j`, `charlie_b`) to the password `Password@123`:
   ```bash
   python reset_sample_passwords.py
   ```
5. **Start the Application**
   ```bash
   uvicorn main:app --reload
   ```
   Open `http://127.0.0.1:8000` in your browser.

## Database & Routing Map (For Viva)

| Page / Feature | Router File | Table Written To | Description |
|---|---|---|---|
| Signup | `auth.py` | `Users` | Validates data and inserts bcrypt hash. |
| Login / Logout | `auth.py` | N/A | Verifies hash, manages server-side HTTP session. |
| Create Group | `groups.py` | `Groups_Table`, `Group_Members` | Transaction inserting group and setting creator as Admin. |
| Add Friend | `groups.py` | `Group_Members` | Validates user exists and inserts them into group. |
| Add Expense | `expenses.py` | `Expenses`, `Expense_Splits` | Splits amount equally handling paisa remainder, inserts inside single transaction. **Fires `After_Expense_Split_Insert` trigger.** |
| Settle Up (Pay) | `payments.py` | `Payments` | Validates you don't overpay, inserts payment. **Fires `After_Payment_Insert` trigger.** |
| Remind | `reminders.py`| `Reminders` | Finds latest shared expense, rate limits to 24h, inserts reminder. |

*Note on Soft Deletion:* The Profile page contains an Account Deletion feature. This attempts to set `deleted_at = CURRENT_TIMESTAMP`. If your schema does not have this column, it will gracefully show an error asking you to alter the schema.
