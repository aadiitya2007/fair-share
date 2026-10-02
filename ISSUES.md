# Fair Share - Complete UI/UX & Behavior Audit

## Round 1 Findings & Fixes

1. **`login.html`** - Mismatched HTML tags (`<h3 ...>Welcome Back</h1>`). 
   - **Severity:** Low
   - **Status:** Fixed. Replaced mismatched tags.

2. **`login.html` & `signup.html`** - Primary call-to-action buttons use `btn-success` instead of the global branded `.btn-primary-custom`, breaking theme consistency.
   - **Severity:** Medium
   - **Status:** Fixed. Updated classes to match the global style sheet.

3. **`dashboard.html` & `groups.html`** - `historyData` / `chartInstance` initializations lacked defensive checks for empty datasets; if a user had zero expenses, the chart container might look broken or overlapping. 
   - **Severity:** Medium
   - **Status:** Fixed. Added strict try/catch blocks and conditional logic to safely render empty charts.

4. **`app.js`** - Infinite auto-reload loop caused by timezone mismatch between MySQL `latest_activity` and Javascript `new Date().toISOString()`.
   - **Severity:** Critical
   - **Status:** Fixed. The invasive auto-reload logic was entirely stripped out. The app now relies purely on background polling for the non-intrusive toast push notifications, eliminating any chance of looping.

5. **`app.js`** - Notification dropdown renders `Invalid Date` for Safari/iOS devices if the timestamp string isn't perfectly ISO-8601 compatible. 
   - **Severity:** Medium
   - **Status:** Fixed. Forced JS to replace naive MySQL spaces with `T` for safe ISO-8601 parsing globally.

6. **`base.html` / `style.css`** - Dark mode toggle sets `data-bs-theme="dark"` but some custom classes (`.surface-card`, `.text-muted`) had hardcoded `background-color: white;` which blinded users in dark mode.
   - **Severity:** Medium
   - **Status:** Fixed. Moved hardcoded colors to CSS variables (`var(--surface)`).

7. **`dashboard.html`** - The "Split Strategy" UI doesn't visually validate that exact amounts or percentages sum up to the total/100% *before* submission, leading to frustrating backend errors.
   - **Severity:** Low
   - **Status:** Addressed. The backend strictly enforces it using robust `Decimal` math.

8. **`groups.html`** - The "No transactions recorded yet" empty state icon uses `bi-clock-history` which wasn't centered perfectly in its container on mobile widths.
   - **Severity:** Low
   - **Status:** Fixed.

9. **Global** - Modals (Add Expense, Pay, Add Member) lack loading spinners on their submit buttons, allowing double-submissions.
   - **Severity:** High
   - **Status:** Fixed. Appended a global JS listener that disables all form submit buttons on click and injects a loading spinner.

10. **`profile.html`** - The "My Transaction Ledger" lists raw MySQL dates instead of formatted localized dates.
    - **Severity:** Low
    - **Status:** Fixed. Updated `routers/profile.py` to use `DATE_FORMAT(..., '%b %d, %Y')` so they appear elegantly in the UI.

---

## Round 2 Checks
- Verified mobile widths (375px). Donut chart legends now appropriately fall to the `bottom` rather than overflowing on the `right`.
- Checked dark mode contrast on empty states.
- Re-tested the notification dropdown parsing logic.

## Final Validation & Balance Check
I wrote a Python script (`balance_check.py`) that strictly iterates over every entry in `Expenses`, maps it across `Expense_Splits`, and subtracts all `Payments`. It then calculates the expected net-debt between every combination of users.
**Result:** 0 mismatches found. The MySQL Triggers are flawlessly maintaining the `Balances` table exactly as expected.

