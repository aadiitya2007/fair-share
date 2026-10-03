from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from decimal import Decimal
from app.db import get_db_connection
from app.utils import require_login

router = APIRouter()

@router.post("/payment/settle")
async def settle_up(request: Request, group_id: int = Form(...), paid_to_user_id: int = Form(...), amount: str = Form(...)):
    user = require_login(request)
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        # Validate balance doesn't exceed owed amount
        try:
            amt_dec = Decimal(amount).quantize(Decimal('0.01'))
        except:
            raise Exception("Invalid amount format.")
            
        if amt_dec <= 0:
            raise Exception("Payment amount must be greater than zero.")
            
        if int(paid_to_user_id) == int(user['user_id']):
            raise Exception("You cannot pay yourself.")
            
        # Validate balance doesn't exceed owed amount
        cursor.execute("SELECT total_amount FROM Balances WHERE lender_id = %s AND borrower_id = %s AND group_id = %s", 
                       (paid_to_user_id, user['user_id'], group_id))
        bal = cursor.fetchone()
        if not bal or Decimal(str(bal['total_amount'])) < amt_dec:
            raise Exception("Cannot pay more than you owe.")
            
        cursor.execute("INSERT INTO Payments (group_id, paid_by_user_id, paid_to_user_id, amount) VALUES (%s, %s, %s, %s)", 
                       (group_id, user['user_id'], paid_to_user_id, amt_dec))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return RedirectResponse(url=f"/group/{group_id}?error={e}", status_code=303)
    finally:
        conn.close()
    return RedirectResponse(url=f"/group/{group_id}?msg=Payment recorded successfully", status_code=303)
