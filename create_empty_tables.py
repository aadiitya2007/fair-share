import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def create_schema():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "password"),
        database=os.getenv("DB_NAME", "FairShare_DB")
    )
    cursor = conn.cursor()

    # Drop existing triggers first
    cursor.execute("DROP TRIGGER IF EXISTS after_expense_split_insert")
    cursor.execute("DROP TRIGGER IF EXISTS after_payment_insert")

    # Drop tables if they exist
    tables = [
        "Reminders", "Balances", "Payments", "Expense_Splits", "Expenses", 
        "Group_Members", "Groups_Table", "Users"
    ]
    cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

    schema = [
        """
        CREATE TABLE Users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            user_name VARCHAR(100) UNIQUE,
            email VARCHAR(100) UNIQUE,
            password_hash VARCHAR(255),
            date_of_birth DATE,
            deleted_at TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE Groups_Table (
            group_id INT AUTO_INCREMENT PRIMARY KEY,
            group_name VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        """
        CREATE TABLE Group_Members (
            group_id INT,
            user_id INT,
            role VARCHAR(50),
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (group_id, user_id),
            FOREIGN KEY (group_id) REFERENCES Groups_Table(group_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE Expenses (
            expense_id INT AUTO_INCREMENT PRIMARY KEY,
            group_id INT,
            paid_by_user_id INT,
            amount DECIMAL(10, 2),
            description VARCHAR(255),
            category VARCHAR(100),
            expense_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES Groups_Table(group_id) ON DELETE CASCADE,
            FOREIGN KEY (paid_by_user_id) REFERENCES Users(user_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE Expense_Splits (
            split_id INT AUTO_INCREMENT PRIMARY KEY,
            expense_id INT,
            user_id INT,
            split_amount DECIMAL(10, 2),
            FOREIGN KEY (expense_id) REFERENCES Expenses(expense_id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE Payments (
            payment_id INT AUTO_INCREMENT PRIMARY KEY,
            group_id INT,
            paid_by_user_id INT,
            paid_to_user_id INT,
            amount DECIMAL(10, 2),
            paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES Groups_Table(group_id) ON DELETE CASCADE,
            FOREIGN KEY (paid_by_user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (paid_to_user_id) REFERENCES Users(user_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE Balances (
            balance_id INT AUTO_INCREMENT PRIMARY KEY,
            group_id INT,
            lender_id INT,
            borrower_id INT,
            total_amount DECIMAL(10, 2),
            FOREIGN KEY (group_id) REFERENCES Groups_Table(group_id) ON DELETE CASCADE,
            FOREIGN KEY (lender_id) REFERENCES Users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (borrower_id) REFERENCES Users(user_id) ON DELETE CASCADE
        )
        """,
        """
        CREATE TABLE Reminders (
            reminder_id INT AUTO_INCREMENT PRIMARY KEY,
            group_id INT,
            sender_id INT,
            receiver_id INT,
            amount_due DECIMAL(10, 2),
            status VARCHAR(50) DEFAULT 'pending',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES Groups_Table(group_id) ON DELETE CASCADE,
            FOREIGN KEY (sender_id) REFERENCES Users(user_id) ON DELETE CASCADE,
            FOREIGN KEY (receiver_id) REFERENCES Users(user_id) ON DELETE CASCADE
        )
        """
    ]

    for stmt in schema:
        cursor.execute(stmt)

    # TRIGGERS
    cursor.execute("""
    CREATE TRIGGER after_expense_split_insert
    AFTER INSERT ON Expense_Splits
    FOR EACH ROW
    BEGIN
        DECLARE lender INT;
        DECLARE grp INT;
        
        SELECT paid_by_user_id, group_id INTO lender, grp
        FROM Expenses WHERE expense_id = NEW.expense_id;
        
        IF NEW.user_id != lender THEN
            IF EXISTS (SELECT 1 FROM Balances WHERE group_id = grp AND lender_id = lender AND borrower_id = NEW.user_id) THEN
                UPDATE Balances SET total_amount = total_amount + NEW.split_amount
                WHERE group_id = grp AND lender_id = lender AND borrower_id = NEW.user_id;
            ELSEIF EXISTS (SELECT 1 FROM Balances WHERE group_id = grp AND lender_id = NEW.user_id AND borrower_id = lender) THEN
                UPDATE Balances SET total_amount = total_amount - NEW.split_amount
                WHERE group_id = grp AND lender_id = NEW.user_id AND borrower_id = lender;
                
                IF (SELECT total_amount FROM Balances WHERE group_id = grp AND lender_id = NEW.user_id AND borrower_id = lender) < 0 THEN
                    UPDATE Balances 
                    SET lender_id = lender, borrower_id = NEW.user_id, total_amount = ABS(total_amount)
                    WHERE group_id = grp AND lender_id = NEW.user_id AND borrower_id = lender;
                END IF;
            ELSE
                INSERT INTO Balances (group_id, lender_id, borrower_id, total_amount)
                VALUES (grp, lender, NEW.user_id, NEW.split_amount);
            END IF;
        END IF;
    END;
    """)

    cursor.execute("""
    CREATE TRIGGER after_payment_insert
    AFTER INSERT ON Payments
    FOR EACH ROW
    BEGIN
        IF EXISTS (SELECT 1 FROM Balances WHERE group_id = NEW.group_id AND lender_id = NEW.paid_to_user_id AND borrower_id = NEW.paid_by_user_id) THEN
            UPDATE Balances SET total_amount = total_amount - NEW.amount
            WHERE group_id = NEW.group_id AND lender_id = NEW.paid_to_user_id AND borrower_id = NEW.paid_by_user_id;
            
            IF (SELECT total_amount FROM Balances WHERE group_id = NEW.group_id AND lender_id = NEW.paid_to_user_id AND borrower_id = NEW.paid_by_user_id) < 0 THEN
                UPDATE Balances 
                SET lender_id = NEW.paid_by_user_id, borrower_id = NEW.paid_to_user_id, total_amount = ABS(total_amount)
                WHERE group_id = NEW.group_id AND lender_id = NEW.paid_to_user_id AND borrower_id = NEW.paid_by_user_id;
            END IF;
        ELSEIF EXISTS (SELECT 1 FROM Balances WHERE group_id = NEW.group_id AND lender_id = NEW.paid_by_user_id AND borrower_id = NEW.paid_to_user_id) THEN
            UPDATE Balances SET total_amount = total_amount + NEW.amount
            WHERE group_id = NEW.group_id AND lender_id = NEW.paid_by_user_id AND borrower_id = NEW.paid_to_user_id;
        ELSE
            INSERT INTO Balances (group_id, lender_id, borrower_id, total_amount)
            VALUES (NEW.group_id, NEW.paid_by_user_id, NEW.paid_to_user_id, NEW.amount);
        END IF;
    END;
    """)

    conn.commit()
    conn.close()
    print("Database schema created successfully! All tables are empty.")

if __name__ == "__main__":
    create_schema()
