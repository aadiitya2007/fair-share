import mysql.connector
import os
from dotenv import load_dotenv
from passlib.context import CryptContext
import datetime

load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def seed():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "password"),
        database=os.getenv("DB_NAME", "FairShare_DB")
    )
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Note: In a real app we'd TRUNCATE, but we don't want to break FKs or constraints.
        # This script inserts demo data assuming empty tables or just adds to existing.
        
        hashed_pw = pwd_context.hash("Password@123")
        
        users = [
            ("Alice", "Smith", "alice_s", "alice@example.com", hashed_pw, "2000-01-01"),
            ("Bob", "Jones", "bobby_j", "bob@example.com", hashed_pw, "1999-05-10"),
            ("Charlie", "Brown", "charlie_b", "charlie@example.com", hashed_pw, "2001-08-20")
        ]
        
        user_ids = {}
        for u in users:
            try:
                cursor.execute("INSERT INTO Users (first_name, last_name, user_name, email, password_hash, date_of_birth) VALUES (%s, %s, %s, %s, %s, %s)", u)
                user_ids[u[2]] = cursor.lastrowid
            except:
                # Already exists, just fetch the ID
                cursor.execute("SELECT user_id FROM Users WHERE user_name = %s", (u[2],))
                user_ids[u[2]] = cursor.fetchone()['user_id']
                
        # Create Group
        cursor.execute("INSERT INTO Groups_Table (group_name) VALUES ('Goa Trip')", ())
        group_id = cursor.lastrowid
        
        # Add Members
        for uname, uid in user_ids.items():
            role = 'Admin' if uname == 'alice_s' else 'Member'
            cursor.execute("INSERT INTO Group_Members (group_id, user_id, role) VALUES (%s, %s, %s)", (group_id, uid, role))
            
        today = datetime.date.today()
        
        # Scenario 1: Alice pays 90, equal split of 3 -> Bob owes Alice 30, Charlie owes Alice 30.
        cursor.execute("INSERT INTO Expenses (group_id, paid_by_user_id, amount, description, expense_date, category) VALUES (%s, %s, %s, 'Dinner', %s, 'Food')", 
                       (group_id, user_ids['alice_s'], 90.0, today))
        exp1_id = cursor.lastrowid
        for uid in user_ids.values():
            cursor.execute("INSERT INTO Expense_Splits (user_id, expense_id, split_amount) VALUES (%s, %s, 30.0)", (uid, exp1_id))
            
        # Scenario 2: Bob settles 30 to Alice -> Bob-Alice row becomes 0.
        cursor.execute("INSERT INTO Payments (group_id, paid_by_user_id, paid_to_user_id, amount) VALUES (%s, %s, %s, 30.0)", 
                       (group_id, user_ids['bobby_j'], user_ids['alice_s']))
                       
        # Scenario 3: Bob pays a taxi of 60 split with Alice -> Alice owes Bob 30
        cursor.execute("INSERT INTO Expenses (group_id, paid_by_user_id, amount, description, expense_date, category) VALUES (%s, %s, %s, 'Taxi', %s, 'Travel')", 
                       (group_id, user_ids['bobby_j'], 60.0, today))
        exp2_id = cursor.lastrowid
        cursor.execute("INSERT INTO Expense_Splits (user_id, expense_id, split_amount) VALUES (%s, %s, 30.0)", (user_ids['bobby_j'], exp2_id))
        cursor.execute("INSERT INTO Expense_Splits (user_id, expense_id, split_amount) VALUES (%s, %s, 30.0)", (user_ids['alice_s'], exp2_id))
        
        # Scenario 4: Charlie pays Alice 50 while owing 30 -> direction flips, Alice owes Charlie 20.
        cursor.execute("INSERT INTO Payments (group_id, paid_by_user_id, paid_to_user_id, amount) VALUES (%s, %s, %s, 50.0)", 
                       (group_id, user_ids['charlie_b'], user_ids['alice_s']))
                       
        conn.commit()
        print("Demo data seeded successfully! The scenarios were processed and Triggers fired!")
    except Exception as e:
        print("Error seeding data:", e)
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    seed()
