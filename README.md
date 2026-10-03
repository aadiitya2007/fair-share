# 💸 Fair Share

**A lightning-fast, Splitwise-style group expense tracker built for real-time settlements.**

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.103-009688.svg?logo=fastapi&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1.svg?logo=mysql&logoColor=white)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-7952B3.svg?logo=bootstrap&logoColor=white)

---

## 📖 The Problem
College students, roommates, and friends frequently share expenses for trips, groceries, and dinners. Tracking who owes whom on paper or Excel quickly becomes a mathematical nightmare. 

**Fair Share** completely automates this. You add an expense, and the system's database automatically calculates exactly who owes whom, cancels out reverse debts, and provides a real-time dashboard of your exact financial position.

## ✨ Features
* **Authentication:** Secure user signup and login with `bcrypt` password hashing.
* **Groups:** Create groups (e.g., "Goa Trip") and invite friends securely via Group IDs.
* **Join Requests:** Users can request to join groups, which Admins can approve or reject.
* **Expense Splitting:** Add expenses and split them across multiple members simultaneously.
* **Intelligent Debt Netting:** If Bob owes Alice ₹300, and Alice borrows ₹100 from Bob, the database automatically nets it out to Bob owing Alice ₹200.
* **Peer-to-peer Settlements:** Record direct payments to settle active debts.
* **Real-time Notifications:** In-app toast notifications and auto-reloading UI when someone requests to join, adds an expense, or settles a debt.
* **Dark Mode:** Seamless light/dark mode toggle.

## 📸 Screenshots
*(Add your screenshots here)*
* [Dashboard / My Groups](docs/screenshots/dashboard.png)
* [Group Details & Balances](docs/screenshots/group_details.png)

---

## 🛠️ Tech Stack & Architecture

* **Backend:** `FastAPI` (Python) - Chosen for its incredible speed, asynchronous design, and clean routing structure.
* **Database:** `MySQL` - Chosen for robust ACID compliance, transactions, and powerful native trigger support.
* **Frontend:** `Jinja2` Templates, `Bootstrap 5`, Vanilla JS - Chosen to keep the architecture simple and server-side rendered, eliminating the need for a heavy React/Node compilation pipeline.

### Architecture Flow
1. The **Browser** sends a standard HTTP POST request (e.g., Add Expense).
2. **FastAPI** intercepts it, verifies the session cookie, and wraps the MySQL queries in an ACID Transaction.
3. **MySQL** inserts the data. Deep inside the database, native **Triggers** automatically intercept the insert and recursively update the cache tables.
4. FastAPI commits the transaction and redirects the browser, rendering the new state via **Jinja2**.

---

## 🗄️ Database Design

Please see [docs/DATABASE.md](docs/DATABASE.md) for the ER Diagram and full table schemas. 

**Key Design Decisions:**
* **The `Balances` Cache Table:** Calculating debts recursively across thousands of transactions is an $O(N)$ operation. We use a cache table (`Balances`) to make dashboard loads $O(1)$.
* **Database Triggers:** To ensure the `Balances` table is never out of sync, we use MySQL Triggers (`after_expense_split_insert`, `after_payment_insert`). They handle the complex mathematics of netting opposite-direction debts precisely at the database layer.
* **ACID Transactions:** When saving an expense, we must insert 1 row into `Expenses` and 3 rows into `Expense_Splits`. If the server crashes mid-way, the database is corrupted. We wrap these in a single SQL Transaction (`conn.commit()` / `conn.rollback()`) to ensure complete atomicity.
* **DECIMAL over FLOAT:** Money is stored as `DECIMAL(10, 2)` to prevent binary floating-point precision errors.

---

## 🚀 Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/fair-share.git
cd fair-share
```

### 2. Environment Setup (Mac/Linux)
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Environment Setup (Windows)
```cmd
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

### 3. Database Setup
1. Create a database in MySQL named `FairShare_DB`.
2. Update your `.env` file with your MySQL credentials.
3. Run the SQL files in order inside your MySQL client (or MySQL Workbench):
   - `database/schema.sql`
   - `database/triggers.sql`
   - *(Optional)* `database/demo_data.sql`

### 4. Run the Server
```bash
uvicorn app.main:app --reload
```
Open your browser to `http://127.0.0.1:8000`.

---

## 🧪 Running Automated Tests
We have included a script to aggressively verify that the database triggers are working correctly. It checks for negative balances, self-debts, and opposite-direction debts that failed to net out.
```bash
python tests/test_balances.py
```

---

## ⚠️ Troubleshooting

* **`ModuleNotFoundError: No module named multipart`**: FastAPI requires `python-multipart` to read form data. Run `pip install python-multipart`.
* **Database Connection Errors**: Ensure your MySQL server is actually running, and your `.env` password is correct.
* **`[Errno 98] Address already in use`**: Port 8000 is occupied. Stop other running apps or run `uvicorn app.main:app --port 8001`.

---

## 📈 Known Limitations & Future Improvements
* Currently, expenses can only be split equally or by strict fixed amounts. Future versions should support percentage-based splits.
* The system does not currently export reports to PDF/CSV.

## 🎓 What I Learned
Building this project taught me how to bridge the gap between frontend templates and robust relational databases. I learned how to manage complex many-to-many state, write native database triggers to offload processing from Python, and protect against race conditions using transactions. 

---
**Developed by:** Aditya Agarrwal  
**Institution:** Sardar Patel Institute of Technology (SPIT)  
**License:** [MIT](LICENSE)
