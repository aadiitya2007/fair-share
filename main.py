from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import mysql.connector
from dotenv import load_dotenv
import os

# Load database credentials from .env file
load_dotenv()

app = FastAPI(title="Fair Share")

# Serve CSS/Images and HTML Templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Database Connection Helper
def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "password"),
            database=os.getenv("DB_NAME", "FairShare_DB")
        )
    except Exception as e:
        print(f"Database Error: {e}")
        return None

# Route 1: Login Page
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Route 2: Handle Login Form (Simplified for Demo)
@app.post("/login")
async def login(username: str = Form(...)):
    # Redirects to the dashboard of the logged-in user
    return RedirectResponse(url=f"/dashboard/{username}", status_code=303)

# Route 3: The Dashboard (Analytics & Queries)
@app.get("/dashboard/{username}", response_class=HTMLResponse)
async def dashboard(request: Request, username: str):
    conn = get_db_connection()
    if not conn:
        return templates.TemplateResponse("dashboard.html", {"request": request, "error": "Database not connected! Check your MySQL password in .env."})
        
    cursor = conn.cursor(dictionary=True)
    
    # Query 1: Get User Info
    cursor.execute("SELECT * FROM Users WHERE user_name = %s", (username,))
    user = cursor.fetchone()
    
    if not user:
        return RedirectResponse(url="/", status_code=303) # User not found
        
    group_id = 1 # Assuming Group 1 ('Goa Trip') for this demo
    
    # Query 2: Who owes this user? (Using your trigger-maintained Balances table!)
    cursor.execute("""
        SELECT borrower.first_name, b.total_amount 
        FROM Balances b 
        JOIN Users borrower ON b.borrower_id = borrower.user_id 
        WHERE b.lender_id = %s AND b.total_amount > 0 AND b.group_id = %s
    """, (user['user_id'], group_id))
    balances = cursor.fetchall()

    # Query 3: Pie Chart Data (Aggregate Function)
    cursor.execute("""
        SELECT COALESCE(category, 'Uncategorized') as category, SUM(amount) as total 
        FROM Expenses 
        WHERE group_id = %s 
        GROUP BY category
    """, (group_id,))
    chart_data = cursor.fetchall()
    
    conn.close()
    
    # Send all this database data to the HTML page
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "user": user, 
        "balances": balances,
        "chart_data": chart_data
    })
