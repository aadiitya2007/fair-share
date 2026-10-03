# Fair Share

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0%2B-4479A1?logo=mysql&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green.svg)

Fair Share is a high-performance, real-time expense splitting and debt settlement application. Built with a modern FastAPI backend and a robust MySQL relational database, it allows groups to easily track shared expenses, automatically calculate minimal debt paths, and settle balances efficiently.

## Features

- **Algorithmic Debt Settlement:** Automatically calculates and simplifies "who owes who" using advanced backend SQL triggers.
- **Real-Time Synchronization:** Utilizes cache-busting sync engines to update transaction ledgers across multiple clients instantly.
- **Interactive Analytics:** Visualizes spending trends and category distributions using Chart.js.
- **Secure Authentication:** Implements stateless session management and Bcrypt password hashing.
- **Granular Group Management:** Role-based access control (Admin/Member) for shared financial environments.

## Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **Database:** MySQL, `mysql-connector-python`
- **Frontend:** HTML5, CSS3, JavaScript (ES6), Bootstrap 5, Chart.js
- **Security:** Passlib (Bcrypt)

---

## Local Development Setup

### 1. Prerequisites
Ensure you have the following installed on your machine:
- Python 3.9+
- MySQL Server 8.0+
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/yourusername/fair-share.git
cd fair-share
```

### 3. Create a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Environment Variables
Create a `.env` file in the root directory and configure your MySQL database credentials:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_secure_password
DB_NAME=FairShare_DB
SESSION_SECRET=your_secure_secret_key
```

### 6. Initialize the Database
Run the schema migration script to build the required tables and background triggers.
```bash
python create_empty_tables.py
```
*(Optional: If you want to populate the database with dummy test users, run `python seed_demo_data.py` instead).*

### 7. Run the Application
Start the ASGI server using Uvicorn:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.

---

## Deployment (Production)

This application is configured for seamless deployment on PaaS providers like **Railway** or **Render**. 

1. Provision a Cloud MySQL Database and retrieve the connection credentials.
2. Inject the credentials into the host's Environment Variables.
3. The included `Procfile` will automatically execute the optimized production boot command:
   ```bash
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

## Architecture Notes

* **Database Triggers:** Debt reconciliation is offloaded to the database layer via MySQL triggers (`After_Expense_Split_Insert`, `After_Payment_Insert`) to guarantee ACID compliance and absolute mathematical accuracy across concurrent transactions.
* **Stateless Client Polling:** The frontend utilizes an optimized long-polling fallback to fetch notification states without overwhelming the FastAPI event loop.

## License
Distributed under the MIT License. See `LICENSE` for more information.
