from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse
from decimal import Decimal
from db import get_db_connection
from utils import require_login
import datetime

router = APIRouter()

@router.post("/expense/add")
async def add_expense(request: Request):
    user = require_login(request)
    form = await request.form()
    
    group_id = int(form.get('group_id'))
    description = form.get('description')
    amount_str = form.get('amount')
    try:
        amount = Decimal(amount_str).quantize(Decimal('0.01'))
    except:
        return RedirectResponse(url=f"/group/{form.get('group_id')}?error=Invalid amount.", status_code=303)
        
    category = form.get('category')
    split_type = form.get('split_type', 'equal')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT * FROM Group_Members WHERE user_id = %s AND group_id = %s", (user['user_id'], group_id))
        if not cursor.fetchone():
            raise Exception("Unauthorized")
            
        if amount <= 0:
            raise Exception("Amount must be greater than zero.")
            
        cursor.execute("SELECT user_id FROM Group_Members WHERE group_id = %s", (group_id,))
        members = cursor.fetchall()
        num_members = len(members)
        if num_members == 0:
            raise Exception("No members in group.")
            
        splits_to_insert = [] # list of (user_id, amount)
        
        if split_type == 'equal':
            split_amount = (amount / Decimal(num_members)).quantize(Decimal('0.01'), rounding='ROUND_DOWN')
            total_split = split_amount * num_members
            difference = amount - total_split
            for i, member in enumerate(members):
                adj_split = split_amount + (difference if i == 0 else Decimal('0.00'))
                splits_to_insert.append((member['user_id'], adj_split))
                
        elif split_type == 'exact':
            total_exact = Decimal('0.00')
            for member in members:
                val = form.get(f"split_val_{member['user_id']}")
                if not val:
                    val = "0"
                try:
                    val_dec = Decimal(val).quantize(Decimal('0.01'))
                except:
                    val_dec = Decimal('0.00')
                total_exact += val_dec
                if val_dec > 0:
                    splits_to_insert.append((member['user_id'], val_dec))
                    
            if abs(total_exact - amount) > Decimal('0.01'):
                raise Exception(f"Exact splits sum (₹{total_exact}) does not equal total amount (₹{amount}).")
                
        elif split_type == 'percentage':
            total_pct = Decimal('0.00')
            raw_splits = []
            for member in members:
                val = form.get(f"split_val_{member['user_id']}")
                if not val:
                    val = "0"
                try:
                    pct = Decimal(val)
                except:
                    pct = Decimal('0.00')
                
                total_pct += pct
                calc_amount = ((pct / Decimal('100.0')) * amount).quantize(Decimal('0.01'))
                raw_splits.append([member['user_id'], calc_amount])
                
            if abs(total_pct - Decimal('100.0')) > Decimal('0.01'):
                raise Exception(f"Percentages must sum to 100%. (Current: {total_pct}%)")
                
            # adjust for rounding
            sum_v = sum(v[1] for v in raw_splits)
            diff = amount - sum_v
            if raw_splits:
                raw_splits[0][1] += diff
                
            for u_id, v in raw_splits:
                if v > 0:
                    splits_to_insert.append((u_id, v))
        else:
            raise Exception("Invalid split type.")
            
        # Validated successfully, now insert
        today = datetime.date.today()
        cursor.execute("""
            INSERT INTO Expenses (group_id, paid_by_user_id, amount, description, expense_date, category) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (group_id, user['user_id'], amount, description, today, category))
        
        expense_id = cursor.lastrowid
        
        for u_id, v in splits_to_insert:
            cursor.execute("INSERT INTO Expense_Splits (user_id, expense_id, split_amount) VALUES (%s, %s, %s)", 
                           (u_id, expense_id, v))
                           
        conn.commit()
    except Exception as e:
        conn.rollback()
        return RedirectResponse(url=f"/group/{group_id}?error=Error: {e}", status_code=303)
    finally:
        conn.close()
        
    return RedirectResponse(url=f"/group/{group_id}?msg=Expense added successfully", status_code=303)