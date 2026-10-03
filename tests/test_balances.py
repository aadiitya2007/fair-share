import mysql.connector
import os
import sys
from dotenv import load_dotenv

def check_balances():
    load_dotenv()
    
    try:
        conn = mysql.connector.connect(
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 3306))
        )
        cursor = conn.cursor(dictionary=True)
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        sys.exit(1)

    print("🔍 Running Balances Validation Check...\n")
    
    # Check 1: No negative balances
    cursor.execute("SELECT * FROM Balances WHERE total_amount < 0")
    negatives = cursor.fetchall()
    if negatives:
        print("❌ FAILED: Found negative balances in the Balances cache table.")
        for n in negatives:
            print(f"   - Group {n['group_id']}: User {n['borrower_id']} owes User {n['lender_id']} amount {n['total_amount']}")
    else:
        print("✅ PASSED: No negative balances found (Constraint CHK_BALANCE_NONNEG respected).")

    # Check 2: No self-debts
    cursor.execute("SELECT * FROM Balances WHERE lender_id = borrower_id")
    self_debts = cursor.fetchall()
    if self_debts:
        print("❌ FAILED: Found self-debts in the Balances table.")
    else:
        print("✅ PASSED: No self-debts found (Constraint CHK_BALANCE_USERS respected).")

    # Check 3: Opposite direction debts are netted (No A owes B and B owes A in the same group)
    cursor.execute("""
        SELECT b1.* 
        FROM Balances b1 
        JOIN Balances b2 ON b1.group_id = b2.group_id 
        AND b1.lender_id = b2.borrower_id 
        AND b1.borrower_id = b2.lender_id
        WHERE b1.total_amount > 0 AND b2.total_amount > 0
    """)
    opposite_debts = cursor.fetchall()
    if opposite_debts:
        print("❌ FAILED: Found opposite direction active debts. Triggers failed to net them out.")
    else:
        print("✅ PASSED: All debts are perfectly netted out (Triggers are working).")

    print("\nSummary of Active Balances:")
    cursor.execute("SELECT * FROM Balances WHERE total_amount > 0")
    active = cursor.fetchall()
    if not active:
        print("  (No active debts in the system)")
    else:
        for b in active:
            print(f"  Group {b['group_id']}: User {b['borrower_id']} owes User {b['lender_id']} ₹{b['total_amount']}")

    conn.close()

if __name__ == "__main__":
    check_balances()
