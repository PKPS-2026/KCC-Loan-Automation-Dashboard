======================================================================
  KCC LOAN AUTOMATION — PRI FINAL (V4)
  Date: 23-May-2026
======================================================================

FILES IN THIS FOLDER:
─────────────────────
  PR_V4.py          ← Main automation script (LATEST WORKING)
  dashboard.py      ← Web dashboard to run automation & view live logs
  config.py         ← Credentials (DO NOT SHARE)
  config.example.py ← Template for config (copy → config.py, add credentials)
  loans.xlsx        ← Sample Excel file with 6 farmer records
  requirements.txt  ← Python packages needed
  README.txt        ← This file

HOW TO RUN:
─────────────────────
  Step 1: Open terminal in this folder
  Step 2: python dashboard.py
  Step 3: Open browser → http://localhost:5000
  Step 4: Paste data OR Upload Excel → Click Run
  Step 5: Login manually (mobile + password + captcha)
  Step 6: Automation runs all records automatically

EXCEL / PASTE FORMAT (required columns):
─────────────────────────────────────────
  | Aadhar Number | Loan Disbursal Date | Max Withdrawal Amount (INR) |
  Column names must match exactly.

  Date formats accepted (all work):
    3/27/2026   → 27/03/2026  ✅
    27/03/2026  → 27/03/2026  ✅
    27-03-2026  → 27/03/2026  ✅

WHAT THE AUTOMATION DOES:
─────────────────────────
  1. Waits for manual login (mobile, password, captcha)
  2. Applicant Details → State / District / Block / Village
  3. UPDATE & CONTINUE (Applicant Details)
  4. UPDATE & CONTINUE (Account Details)
  5. Financial Details:
       - KCC loan sanctioned date  ← RMDP calendar picker
       - KCC SOF Eligibility amount
       - KCC Drawing Limit amount
  6. SAVE & CONTINUE → Activity tab → Loan Sanctioned fill → SAVE
  7. PREVIEW → SUBMIT → CONFIRM → Final OK

FIXES IN V4 (vs V3):
─────────────────────
  - Date format fix: 3/27/2026 (M/D/Y) now correctly reads as 27 March
  - Auto-skip: "already submitted / IS/PRI pending" portal error → skip record
  - Debug logs: [parse_date] lines show exact date being parsed

KNOWN PORTAL ERRORS (auto-handled):
─────────────────────────────────────
  - "A loan application already submitted" → auto-skipped (SKIPPED in log)
  - State/District GetHandleVerifier crash → auto-continues (portal pre-fills)

======================================================================
