import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

def get_db_connection():
    try:
        return mysql.connector.connect(
            host=os.getenv("DB_HOST", "localhost"),
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", "password"),
            database=os.getenv("DB_NAME", "FairShare_DB"),
            port=int(os.getenv("DB_PORT", 3306))
        )
    except Exception as e:
        print(f"Database Error: {e}")
        return None
