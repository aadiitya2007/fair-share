import mysql.connector
import os
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

hashed_pw = pwd_context.hash("Password@123")

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", "password"),
    database=os.getenv("DB_NAME", "FairShare_DB")
)
cursor = conn.cursor()

try:
    cursor.execute("UPDATE Users SET password_hash = %s WHERE user_name IN ('alice_s', 'bobby_j', 'charlie_b')", (hashed_pw,))
    conn.commit()
    print("Passwords successfully reset to 'Password@123' for alice_s, bobby_j, charlie_b")
except Exception as e:
    print("Error:", e)
finally:
    conn.close()
