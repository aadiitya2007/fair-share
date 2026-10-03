from fastapi import APIRouter, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from db import get_db_connection
from utils import require_login, format_currency

router = APIRouter()
templates = Jinja2Templates(directory="templates")
templates.env.filters["currency"] = format_currency

def check_group_membership(user_id, group_id, cursor):
    cursor.execute("SELECT * FROM Group_Members WHERE user_id = %s AND group_id = %s", (user_id, group_id))
    if not cursor.fetchone():
        raise HTTPException(status_code=403, detail="Not authorized to access this group.")

@router.get("/groups", response_class=HTMLResponse)
async def list_groups(request: Request, msg: str = None, error: str = None):
    user = require_login(request)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT g.group_id, g.group_name, gm.role,
        (SELECT COUNT(*) FROM Group_Members WHERE group_id = g.group_id) as member_count,
        COALESCE((SELECT SUM(total_amount) FROM Balances WHERE lender_id = %s AND group_id = g.group_id), 0) as total_to_collect,
        COALESCE((SELECT SUM(total_amount) FROM Balances WHERE borrower_id = %s AND group_id = g.group_id), 0) as total_to_pay
        FROM Groups_Table g
        JOIN Group_Members gm ON g.group_id = gm.group_id
        WHERE gm.user_id = %s
    """, (user['user_id'], user['user_id'], user['user_id']))
    groups = cursor.fetchall()
    
    for g in groups:
        g['net_position'] = float(g['total_to_collect'] - g['total_to_pay'])
        
    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as collect FROM Balances WHERE lender_id = %s", (user['user_id'],))
    global_collect = cursor.fetchone()['collect']
    
    cursor.execute("SELECT COALESCE(SUM(total_amount), 0) as owe FROM Balances WHERE borrower_id = %s", (user['user_id'],))
    global_owe = cursor.fetchone()['owe']
    
    cursor.execute("""
        SELECT 'expense' as type, e.description, e.amount, DATE(e.expense_date) as date, e.category, u.first_name as payer, g.group_name, '' as receiver
        FROM Expenses e
        JOIN Users u ON e.paid_by_user_id = u.user_id
        JOIN Groups_Table g ON e.group_id = g.group_id
        JOIN Group_Members gm ON e.group_id = gm.group_id
        WHERE gm.user_id = %s
    """, (user['user_id'],))
    exp_h = cursor.fetchall()
    
    cursor.execute("""
        SELECT 'payment' as type, 'Payment' as description, p.amount, DATE(p.paid_at) as date, '' as category, u1.first_name as payer, g.group_name, u2.first_name as receiver
        FROM Payments p
        JOIN Users u1 ON p.paid_by_user_id = u1.user_id
        JOIN Users u2 ON p.paid_to_user_id = u2.user_id
        JOIN Groups_Table g ON p.group_id = g.group_id
        WHERE p.paid_by_user_id = %s OR p.paid_to_user_id = %s
    """, (user['user_id'], user['user_id']))
    pay_h = cursor.fetchall()
    
    history = exp_h + pay_h
    history.sort(key=lambda x: str(x['date']), reverse=True)
    history = history[:100]
        
    conn.close()
    return templates.TemplateResponse("groups.html", {
        "request": request, "user": user, "groups": groups, 
        "msg": msg, "error": error,
        "global_collect": global_collect, "global_owe": global_owe,
        "history": history
    })

@router.post("/groups/create")
async def create_group(request: Request, group_name: str = Form(...), description: str = Form("")):
    user = require_login(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO Groups_Table (group_name, description) VALUES (%s, %s)", 
                       (group_name, description))
        group_id = cursor.lastrowid
        cursor.execute("INSERT INTO Group_Members (group_id, user_id, role) VALUES (%s, %s, 'Admin')", 
                       (group_id, user['user_id']))
        conn.commit()
    except Exception as e:
        conn.rollback()
    finally:
        conn.close()
    return RedirectResponse(url="/groups?msg=Group created successfully.", status_code=303)

@router.get("/group/{group_id}", response_class=HTMLResponse)
async def group_dashboard(request: Request, group_id: int, msg: str = None, error: str = None):
    user = require_login(request)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    check_group_membership(user['user_id'], group_id, cursor)
    
    cursor.execute("SELECT * FROM Groups_Table WHERE group_id = %s", (group_id,))
    group = cursor.fetchone()
    
    cursor.execute("""
        SELECT u.user_id, u.first_name, u.user_name, gm.role 
        FROM Group_Members gm 
        JOIN Users u ON gm.user_id = u.user_id 
        WHERE gm.group_id = %s
    """, (group_id,))
    members = cursor.fetchall()
    
    # Check Admin Role for pending requests
    cursor.execute("SELECT role FROM Group_Members WHERE user_id = %s AND group_id = %s", (user['user_id'], group_id))
    role_res = cursor.fetchone()
    role = role_res['role'] if role_res else 'Member'
    
    pending_requests = []
    if role == 'Admin':
        cursor.execute("SELECT gr.user_id, u.first_name, u.last_name, u.user_name FROM Group_Requests gr JOIN Users u ON gr.user_id = u.user_id WHERE gr.group_id = %s AND gr.status = 'Pending'", (group_id,))
        pending_requests = cursor.fetchall()
    
    # Balances for current user
    cursor.execute("""
        SELECT borrower.user_id, borrower.first_name, b.total_amount 
        FROM Balances b JOIN Users borrower ON b.borrower_id = borrower.user_id 
        WHERE b.lender_id = %s AND b.group_id = %s AND b.total_amount > 0
    """, (user['user_id'], group_id))
    owed_to_user = cursor.fetchall()
    
    cursor.execute("""
        SELECT lender.user_id, lender.first_name, b.total_amount 
        FROM Balances b JOIN Users lender ON b.lender_id = lender.user_id 
        WHERE b.borrower_id = %s AND b.group_id = %s AND b.total_amount > 0
    """, (user['user_id'], group_id))
    user_owes = cursor.fetchall()

    # Transaction History
    cursor.execute("""
        SELECT 'expense' as type, e.expense_id, e.description, e.amount, DATE(e.expense_date) as date, e.category, u.first_name as payer_name, '' as receiver_name
        FROM Expenses e JOIN Users u ON e.paid_by_user_id = u.user_id
        WHERE e.group_id = %s
    """, (group_id,))
    exp_list = cursor.fetchall()
    
    cursor.execute("""
        SELECT 'payment' as type, p.payment_id as expense_id, 'Settled up' as description, p.amount, DATE(p.paid_at) as date, '' as category, u1.first_name as payer_name, u2.first_name as receiver_name
        FROM Payments p 
        JOIN Users u1 ON p.paid_by_user_id = u1.user_id
        JOIN Users u2 ON p.paid_to_user_id = u2.user_id
        WHERE p.group_id = %s
    """, (group_id,))
    pay_list = cursor.fetchall()
    
    expenses = exp_list + pay_list
    expenses.sort(key=lambda x: str(x['date']), reverse=True)
    expenses = expenses[:500]

    # Analytics
    cursor.execute("SELECT COALESCE(category, 'Other') as category, SUM(amount) as total FROM Expenses WHERE group_id = %s GROUP BY category", (group_id,))
    chart_data = cursor.fetchall()
    
    # FIX: Decimal to float for JSON serialization
    for row in chart_data:
        row['total'] = float(row['total']) if row['total'] else 0.0
        
    conn.close()

    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "user": user, "group": group, "members": members,
        "owed_to_user": owed_to_user, "user_owes": user_owes, "expenses": expenses,
        "chart_data": chart_data, "msg": msg, "error": error, "pending_requests": pending_requests, "role": role
    })
    
@router.post("/group/{group_id}/add_member")
async def add_member(request: Request, group_id: int, new_username: str = Form(...)):
    user = require_login(request)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    check_group_membership(user['user_id'], group_id, cursor)
    
    # Only Admin can add? Let's allow any member for simplicity, or check role.
    cursor.execute("SELECT role FROM Group_Members WHERE user_id = %s AND group_id = %s", (user['user_id'], group_id))
    if cursor.fetchone()['role'] != 'Admin':
        conn.close()
        return RedirectResponse(url=f"/group/{group_id}?error=Only Admins can add members.", status_code=303)
        
    try:
        cursor.execute("SELECT user_id FROM Users WHERE user_name = %s OR email = %s", (new_username, new_username))
        new_user = cursor.fetchone()
        if not new_user:
            raise Exception("User not found.")
            
        cursor.execute("INSERT INTO Group_Members (group_id, user_id, role) VALUES (%s, %s, 'Member')", (group_id, new_user['user_id']))
        conn.commit()
        msg = "Member added successfully."
    except Exception as e:
        conn.rollback()
        msg = f"Error: User might already be in group or doesn't exist."
        return RedirectResponse(url=f"/group/{group_id}?error={msg}", status_code=303)
    finally:
        conn.close()
    return RedirectResponse(url=f"/group/{group_id}?msg={msg}", status_code=303)

@router.post("/groups/request_join")
async def request_join(request: Request, group_id: int = Form(...)):
    user = require_login(request)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if group exists
    cursor.execute("SELECT * FROM Groups_Table WHERE group_id = %s", (group_id,))
    if not cursor.fetchone():
        conn.close()
        return RedirectResponse(url="/groups?error=Group not found.", status_code=303)
        
    # Check if already a member
    cursor.execute("SELECT * FROM Group_Members WHERE group_id = %s AND user_id = %s", (group_id, user['user_id']))
    if cursor.fetchone():
        conn.close()
        return RedirectResponse(url=f"/group/{group_id}?error=You are already a member.", status_code=303)
        
    # Check if request already exists
    cursor.execute("SELECT * FROM Group_Requests WHERE group_id = %s AND user_id = %s AND status = 'Pending'", (group_id, user['user_id']))
    if cursor.fetchone():
        conn.close()
        return RedirectResponse(url="/groups?msg=Join request already pending.", status_code=303)
        
    cursor.execute("INSERT INTO Group_Requests (group_id, user_id) VALUES (%s, %s)", (group_id, user['user_id']))
    conn.commit()
    conn.close()
    return RedirectResponse(url="/groups?msg=Join request sent to group admins!", status_code=303)

@router.post("/groups/{group_id}/approve/{req_user_id}")
async def approve_request(request: Request, group_id: int, req_user_id: int):
    user = require_login(request)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # Check if admin
    cursor.execute("SELECT role FROM Group_Members WHERE user_id = %s AND group_id = %s", (user['user_id'], group_id))
    member = cursor.fetchone()
    if not member or member['role'] != 'Admin':
        conn.close()
        return RedirectResponse(url=f"/group/{group_id}?error=Only admins can approve requests.", status_code=303)
        
    # Add to group
    try:
        cursor.execute("INSERT INTO Group_Members (group_id, user_id, role) VALUES (%s, %s, 'Member')", (group_id, req_user_id))
        cursor.execute("UPDATE Group_Requests SET status = 'Approved' WHERE group_id = %s AND user_id = %s", (group_id, req_user_id))
        conn.commit()
    except Exception as e:
        conn.rollback()
    
    conn.close()
    return RedirectResponse(url=f"/group/{group_id}?msg=User approved and added to group.", status_code=303)

@router.post("/groups/{group_id}/reject/{req_user_id}")
async def reject_request(request: Request, group_id: int, req_user_id: int):
    user = require_login(request)
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if admin
    cursor.execute("SELECT role FROM Group_Members WHERE user_id = %s AND group_id = %s", (user['user_id'], group_id))
    member = cursor.fetchone()
    if member and member[0] == 'Admin':
        cursor.execute("UPDATE Group_Requests SET status = 'Rejected' WHERE group_id = %s AND user_id = %s", (group_id, req_user_id))
        conn.commit()
    
    conn.close()
    return RedirectResponse(url=f"/group/{group_id}?msg=Request rejected.", status_code=303)
