from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from db import get_db_connection
from utils import require_login

router = APIRouter()

@router.post("/reminders/send")
async def send_reminder(request: Request, group_id: int = Form(...), borrower_id: int = Form(...)):
    user = require_login(request)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT expense_id FROM Expenses WHERE group_id = %s ORDER BY expense_date DESC LIMIT 1", (group_id,))
        exp = cursor.fetchone()
        if not exp:
            raise Exception("No expense to attach reminder to.")
        
        # Rate limit check: sent within last 24h
        cursor.execute("""
            SELECT sent_at FROM Reminders 
            WHERE sender_id = %s AND receiver_id = %s AND sent_at > NOW() - INTERVAL 10 SECOND
            ORDER BY sent_at DESC LIMIT 1
        """, (user['user_id'], borrower_id))
        
        if cursor.fetchone():
            raise Exception("Please wait a moment before sending another reminder.")

        cursor.execute("INSERT INTO Reminders (sender_id, receiver_id, expense_id) VALUES (%s, %s, %s)", 
                       (user['user_id'], borrower_id, exp['expense_id']))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return RedirectResponse(url=f"/group/{group_id}?error={e}", status_code=303)
    finally:
        conn.close()
    return RedirectResponse(url=f"/group/{group_id}?msg=Reminder sent successfully", status_code=303)

from fastapi.responses import JSONResponse

@router.get("/api/notifications")
async def get_notifications(request: Request):
    user = require_login(request)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Get unified notifications
        query = """
            SELECT 'reminder' as type, r.sent_at as timestamp, u.first_name as actor, g.group_name, 'sent you a reminder to settle up.' as action, r.reminder_id as id
            FROM Reminders r
            JOIN Users u ON r.sender_id = u.user_id
            JOIN Expenses e ON r.expense_id = e.expense_id
            JOIN Groups_Table g ON e.group_id = g.group_id
            WHERE r.receiver_id = %s
            
            UNION ALL
            
            SELECT 'payment' as type, p.paid_at as timestamp, u.first_name as actor, g.group_name, concat('paid you ₹', p.amount, '.') as action, p.payment_id as id
            FROM Payments p
            JOIN Users u ON p.paid_by_user_id = u.user_id
            JOIN Groups_Table g ON p.group_id = g.group_id
            WHERE p.paid_to_user_id = %s
            
            UNION ALL
            
            SELECT 'expense' as type, e.created_at as timestamp, u.first_name as actor, g.group_name, concat('added an expense: ', e.description, '.') as action, e.expense_id as id
            FROM Expense_Splits es
            JOIN Expenses e ON es.expense_id = e.expense_id
            JOIN Users u ON e.paid_by_user_id = u.user_id
            JOIN Groups_Table g ON e.group_id = g.group_id
            WHERE es.user_id = %s AND e.paid_by_user_id != %s
            
            UNION ALL
            
            SELECT 'join_request' as type, gr.created_at as timestamp, u.first_name as actor, g.group_name, 'requested to join.' as action, gr.request_id as id
            FROM Group_Requests gr
            JOIN Users u ON gr.user_id = u.user_id
            JOIN Groups_Table g ON gr.group_id = g.group_id
            JOIN Group_Members gm ON g.group_id = gm.group_id
            WHERE gm.user_id = %s AND gm.role = 'Admin' AND gr.status = 'Pending'
            
            UNION ALL
            
            SELECT 'join_update' as type, gr.created_at as timestamp, 'Group Admin' as actor, g.group_name, concat('has ', lower(gr.status), ' your request.') as action, gr.request_id as id
            FROM Group_Requests gr
            JOIN Groups_Table g ON gr.group_id = g.group_id
            WHERE gr.user_id = %s AND gr.status IN ('Approved', 'Rejected')
            
            ORDER BY timestamp DESC LIMIT 20
        """
        cursor.execute(query, (user['user_id'], user['user_id'], user['user_id'], user['user_id'], user['user_id'], user['user_id']))
        notifs = cursor.fetchall()
        
        # Get the latest timestamp of any activity across the user's groups to trigger live UI reloads
        cursor.execute("""
            SELECT MAX(latest) as global_latest FROM (
                SELECT MAX(created_at) as latest FROM Expenses e JOIN Group_Members gm ON e.group_id = gm.group_id WHERE gm.user_id = %s
                UNION ALL
                SELECT MAX(paid_at) as latest FROM Payments p JOIN Group_Members gm ON p.group_id = gm.group_id WHERE gm.user_id = %s
            ) as t
        """, (user['user_id'], user['user_id']))
        latest_act = cursor.fetchone()
        latest_timestamp = latest_act['global_latest'].isoformat() if latest_act and latest_act['global_latest'] else "2000-01-01T00:00:00"
        
        for n in notifs:
            n['timestamp'] = n['timestamp'].isoformat() if n['timestamp'] else ""
            
        return JSONResponse({
            "notifications": notifs,
            "latest_activity": latest_timestamp
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
    finally:
        conn.close()
