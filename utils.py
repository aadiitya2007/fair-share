from fastapi import Request, HTTPException, status
from db import get_db_connection

def get_current_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    
    conn = get_db_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    # Check if deleted_at exists safely, though we assume the schema will be updated
    try:
        cursor.execute("SELECT * FROM Users WHERE user_id = %s AND (deleted_at IS NULL)", (user_id,))
    except:
        cursor.execute("SELECT * FROM Users WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    conn.close()
    if not user:
        request.session.clear()
    return user

def require_login(request: Request):
    user = get_current_user(request)
    if not user:
        request.session.clear()
        raise HTTPException(status_code=status.HTTP_303_SEE_OTHER, headers={"Location": "/login"})
    return user

def format_currency(value):
    if value is None:
        return "₹0.00"
    return f"₹{float(value):.2f}"
