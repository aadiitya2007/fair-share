-- ==========================================
-- Fair Share Database Schema
-- ==========================================

-- 1. Users Table
CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    user_name VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    date_of_birth DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);

-- 2. Groups Table
CREATE TABLE Groups_Table (
    group_id INT AUTO_INCREMENT PRIMARY KEY,
    group_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 3. Group Members (Many-to-Many junction)
CREATE TABLE Group_Members (
    user_id INT NOT NULL,
    group_id INT NOT NULL,
    role VARCHAR(50) DEFAULT 'Member',
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, group_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES Groups_Table(group_id) ON DELETE CASCADE
);

-- 4. Expenses Table
CREATE TABLE Expenses (
    expense_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT NOT NULL,
    paid_by_user_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount > 0),
    description VARCHAR(255) NOT NULL,
    expense_date DATE NOT NULL, 
    category VARCHAR(50),       
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES Groups_Table(group_id) ON DELETE CASCADE,
    FOREIGN KEY (paid_by_user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- 5. Expense Splits Table (Many-to-Many junction)
CREATE TABLE Expense_Splits (
    split_id INT AUTO_INCREMENT PRIMARY KEY,
    expense_id INT NOT NULL,
    user_id INT NOT NULL,
    split_amount DECIMAL(10, 2) NOT NULL CHECK (split_amount > 0),
    FOREIGN KEY (expense_id) REFERENCES Expenses(expense_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- 6. Payments Table (Direct peer-to-peer settlements)
CREATE TABLE Payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT NOT NULL,
    paid_by_user_id INT NOT NULL,
    paid_to_user_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL CHECK (amount > 0),
    paid_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (paid_by_user_id <> paid_to_user_id),
    FOREIGN KEY (group_id) REFERENCES Groups_Table(group_id) ON DELETE CASCADE,
    FOREIGN KEY (paid_by_user_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (paid_to_user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

-- 7. Balances Table (Cache table maintained by triggers)
CREATE TABLE Balances (
    balance_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT NOT NULL,
    lender_id INT NOT NULL,
    borrower_id INT NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT uq_balance UNIQUE (group_id, lender_id, borrower_id),
    CONSTRAINT chk_balance_users CHECK (lender_id <> borrower_id),
    CONSTRAINT chk_balance_nonneg CHECK (total_amount >= 0),
    FOREIGN KEY (lender_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (borrower_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (group_id) REFERENCES Groups_Table(group_id) ON DELETE CASCADE
);

-- 8. Reminders Table
CREATE TABLE Reminders (
    reminder_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT NOT NULL,
    sender_id INT NOT NULL,
    receiver_id INT NOT NULL,
    expense_id INT NOT NULL,
    amount_due DECIMAL(10, 2),
    status VARCHAR(50) DEFAULT 'pending',
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES Groups_Table(group_id) ON DELETE CASCADE,
    FOREIGN KEY (sender_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (expense_id) REFERENCES Expenses(expense_id) ON DELETE CASCADE
);

-- 9. Group Requests Table
CREATE TABLE Group_Requests (
    request_id INT AUTO_INCREMENT PRIMARY KEY,
    group_id INT NOT NULL,
    user_id INT NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (group_id) REFERENCES Groups_Table(group_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);
