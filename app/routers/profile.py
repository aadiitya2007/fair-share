from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from passlib.context import CryptContext
from app.db import get_db_connection
from app.utils import require_login, format_currency

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
templates.env.filters["currency"] = format_currency
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request, msg: str = None, error: str = None):
    user = require_login(request)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        query = """
            SELECT 'payment_sent' as type, p.amount, p.paid_at as raw_date, DATE_FORMAT(p.paid_at, '%b %d, %Y') as date, u2.first_name as other, g.group_name, 'Settled up' as description
            FROM Payments p JOIN Users u2 ON p.paid_to_user_id = u2.user_id JOIN Groups_Table g ON p.group_id = g.group_id
            WHERE p.paid_by_user_id = %s
            UNION ALL
            SELECT 'payment_received' as type, p.amount, p.paid_at as raw_date, DATE_FORMAT(p.paid_at, '%b %d, %Y') as date, u1.first_name as other, g.group_name, 'Settled up' as description
            FROM Payments p JOIN Users u1 ON p.paid_by_user_id = u1.user_id JOIN Groups_Table g ON p.group_id = g.group_id
            WHERE p.paid_to_user_id = %s
            UNION ALL
            SELECT 'expense_paid' as type, e.amount, e.expense_date as raw_date, DATE_FORMAT(e.expense_date, '%b %d, %Y') as date, '' as other, g.group_name, e.description
            FROM Expenses e JOIN Groups_Table g ON e.group_id = g.group_id
            WHERE e.paid_by_user_id = %s
            UNION ALL
            SELECT 'expense_owed' as type, es.split_amount as amount, e.expense_date as raw_date, DATE_FORMAT(e.expense_date, '%b %d, %Y') as date, u.first_name as other, g.group_name, e.description
            FROM Expense_Splits es JOIN Expenses e ON es.expense_id = e.expense_id JOIN Users u ON e.paid_by_user_id = u.user_id JOIN Groups_Table g ON e.group_id = g.group_id
            WHERE es.user_id = %s AND e.paid_by_user_id != %s
        """
        uid = user['user_id']
        cursor.execute(query, (uid, uid, uid, uid, uid))
        ledger = cursor.fetchall()
        ledger.sort(key=lambda x: x['raw_date'], reverse=True)
    except Exception as e:
        print("Error fetching ledger:", e)
        ledger = []
    finally:
        conn.close()
    
    return templates.TemplateResponse("profile.html", {"request": request, "user": user, "msg": msg, "error": error, "ledger": ledger})

@router.post("/profile/edit")
async def edit_profile(request: Request, first_name: str = Form(...), last_name: str = Form(...), email: str = Form(...)):
    user = require_login(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Users SET first_name=%s, last_name=%s, email=%s WHERE user_id=%s", 
                       (first_name, last_name, email, user['user_id']))
        conn.commit()
        msg = "Profile updated successfully."
    except Exception as e:
        conn.rollback()
        return RedirectResponse(url=f"/profile?error=Email already in use", status_code=303)
    finally:
        conn.close()
    return RedirectResponse(url=f"/profile?msg={msg}", status_code=303)

@router.post("/profile/delete")
async def delete_profile(request: Request):
    user = require_login(request)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Block deletion if user has non-zero balance
    cursor.execute("SELECT * FROM Balances WHERE (lender_id = %s OR borrower_id = %s) AND total_amount > 0", (user['user_id'], user['user_id']))
    if cursor.fetchone():
        conn.close()
        return RedirectResponse(url="/profile?error=Cannot delete account while you have active balances.", status_code=303)
    
    try:
        # Assuming deleted_at exists. If not, this might fail, but it's the requested feature.
        cursor.execute("UPDATE Users SET deleted_at = CURRENT_TIMESTAMP WHERE user_id = %s", (user['user_id'],))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Schema missing deleted_at:", e)
        conn.close()
        return RedirectResponse(url="/profile?error=Database schema missing deleted_at column. Update schema first.", status_code=303)
        
    conn.close()
    request.session.clear()
    return RedirectResponse(url="/login?msg=Account deleted.", status_code=303)
