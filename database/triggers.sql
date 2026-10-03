-- ==========================================
-- Fair Share Database Triggers
-- ==========================================
-- NOTE: In MySQL, change the delimiter before running these triggers.
-- DELIMITER //

-- Trigger 1: A new split creates a debt (borrower owes the payer)
CREATE TRIGGER after_expense_split_insert
AFTER INSERT ON Expense_Splits
FOR EACH ROW
BEGIN
    DECLARE lender INT;
    DECLARE borrower INT;
    DECLARE grp INT;
    DECLARE amt DECIMAL(10,2);
    DECLARE rev_amt DECIMAL(10,2);
    
    SET borrower = NEW.user_id;
    SET amt = NEW.split_amount;
    
    SELECT paid_by_user_id, group_id INTO lender, grp
    FROM Expenses WHERE expense_id = NEW.expense_id;
    
    IF borrower != lender THEN
        -- 1. Check if borrower is already owed money by the lender (reverse debt)
        SELECT total_amount INTO rev_amt FROM Balances 
        WHERE group_id = grp AND lender_id = borrower AND borrower_id = lender;
        
        IF rev_amt IS NOT NULL AND rev_amt > 0 THEN
            IF rev_amt > amt THEN
                -- Reduce the reverse debt
                UPDATE Balances SET total_amount = total_amount - amt 
                WHERE group_id = grp AND lender_id = borrower AND borrower_id = lender;
            ELSEIF rev_amt = amt THEN
                -- Debt perfectly cancels out
                UPDATE Balances SET total_amount = 0 
                WHERE group_id = grp AND lender_id = borrower AND borrower_id = lender;
            ELSE
                -- Reverse debt is smaller than new debt. Cancel reverse, create forward debt.
                UPDATE Balances SET total_amount = 0 
                WHERE group_id = grp AND lender_id = borrower AND borrower_id = lender;
                
                INSERT INTO Balances (group_id, lender_id, borrower_id, total_amount)
                VALUES (grp, lender, borrower, amt - rev_amt)
                ON DUPLICATE KEY UPDATE total_amount = total_amount + (amt - rev_amt);
            END IF;
        ELSE
            -- Normal case: no reverse debt exists. Add to standard balance.
            INSERT INTO Balances (group_id, lender_id, borrower_id, total_amount)
            VALUES (grp, lender, borrower, amt)
            ON DUPLICATE KEY UPDATE total_amount = total_amount + amt;
        END IF;
    END IF;
END;
-- //

-- Trigger 2: A payment reduces a debt (payer pays the receiver)
CREATE TRIGGER after_payment_insert
AFTER INSERT ON Payments
FOR EACH ROW
BEGIN
    DECLARE v_lender INT;
    DECLARE v_borrower INT;
    DECLARE v_grp INT;
    DECLARE v_amt DECIMAL(10,2);
    DECLARE fwd_amt DECIMAL(10,2);
    
    SET v_borrower = NEW.paid_by_user_id;
    SET v_lender = NEW.paid_to_user_id;
    SET v_grp = NEW.group_id;
    SET v_amt = NEW.amount;
    
    -- Check the direct debt direction first
    SELECT total_amount INTO fwd_amt FROM Balances
    WHERE group_id = v_grp AND lender_id = v_lender AND borrower_id = v_borrower;
    
    IF fwd_amt IS NOT NULL AND fwd_amt > 0 THEN
        IF fwd_amt >= v_amt THEN
            -- Payment fully or partially covers the debt
            UPDATE Balances SET total_amount = total_amount - v_amt
            WHERE group_id = v_grp AND lender_id = v_lender AND borrower_id = v_borrower;
        ELSE
            -- Payment is more than what is owed. Clear forward, create reverse debt (overpayment).
            UPDATE Balances SET total_amount = 0
            WHERE group_id = v_grp AND lender_id = v_lender AND borrower_id = v_borrower;
            
            INSERT INTO Balances (group_id, lender_id, borrower_id, total_amount)
            VALUES (v_grp, v_borrower, v_lender, v_amt - fwd_amt)
            ON DUPLICATE KEY UPDATE total_amount = total_amount + (v_amt - fwd_amt);
        END IF;
    ELSE
        -- No forward debt exists. They just sent money, so it becomes a reverse debt (overpayment).
        INSERT INTO Balances (group_id, lender_id, borrower_id, total_amount)
        VALUES (v_grp, v_borrower, v_lender, v_amt)
        ON DUPLICATE KEY UPDATE total_amount = total_amount + v_amt;
    END IF;
END;
-- //
-- DELIMITER ;
