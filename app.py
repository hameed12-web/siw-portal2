import os
import json
import sqlite3
from flask import Flask, request, redirect, url_for, session, send_from_directory, render_template_string
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'siw-balochistan-2026-ultimate-fixed-key')

UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/opt/render/project/src/static/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DB_PATH = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # 1. Main Trainees table with explicit UNIQUE structural constraints to block duplicate entries
    c.execute('''
        CREATE TABLE IF NOT EXISTS trainees (
            id INTEGER PRIMARY KEY AUTOINCREMENT, center_name TEXT, full_name TEXT, father_name TEXT, 
            cnic_number TEXT UNIQUE, phone_number TEXT UNIQUE, session_cohort TEXT, email_address TEXT, 
            course_module TEXT, gender TEXT, local_status TEXT, disability TEXT, minority TEXT, 
            vendor_id TEXT UNIQUE, iban TEXT UNIQUE, stipend TEXT, wallet_number TEXT
        )
    ''')
    # 2. Affiliated Centers Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS training_centers (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ddo_code TEXT NOT NULL UNIQUE, 
            center_name TEXT NOT NULL UNIQUE, status TEXT NOT NULL, sector TEXT NOT NULL, 
            ddo_name TEXT NOT NULL, extra_columns TEXT DEFAULT '{}'
        )
    ''')
    # 3. Dedicated Access Control Table for Center Incharge DDO Logins
    c.execute('''
        CREATE TABLE IF NOT EXISTS ddo_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, center_name TEXT UNIQUE, username TEXT UNIQUE, password TEXT
        )
    ''')
    # 4. Document Correspondence Vault Storage
    c.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT, direction TEXT, filename TEXT, center_name TEXT, uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ====================================================
# CRASH-PROOF EMBEDDED FRONT-END TEMPLATES (RAW TEXT STRINGS)
# ====================================================

PUBLIC_FORM_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Small Industries Wing, Balochistan - Registration Portal</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #0f172a; margin: 0; padding: 40px 20px; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; box-sizing: border-box; }
        .wrapper { width: 100%; max-width: 850px; background: #ffffff; border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); overflow: hidden; }
        .branding-header { background: #004d26; color: #ffffff; padding: 35px 20px; text-align: center; }
        .branding-header h1 { margin: 0; font-size: 26px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; }
        .branding-header p { margin: 8px 0 0 0; font-size: 13px; opacity: 0.85; }
        .accent-strip { background: #d4af37; height: 5px; }
        .form-body { padding: 40px; }
        .form-section-title { font-size: 14px; color: #004d26; font-weight: bold; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; margin-top: 30px; margin-bottom: 18px; text-transform: uppercase; }
        .input-row { display: grid; grid-template-columns: 1fr; gap: 20px; margin-bottom: 15px; }
        @media(min-width: 768px) { .input-row { grid-template-columns: 1fr 1fr; } }
        .field-box { display: flex; flex-direction: column; }
        .field-box label { font-size: 12px; font-weight: 600; margin-bottom: 6px; color: #34495e; text-transform: uppercase; }
        .field-box input, .field-box select { padding: 11px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 14px; background-color: #f8fafc; box-sizing: border-box; }
        .btn-register { background: #004d26; color: #fff; border: none; padding: 15px; border-radius: 4px; font-size: 15px; font-weight: bold; width: 100%; cursor: pointer; text-transform: uppercase; transition: background 0.2s; }
        .btn-register:hover { background: #003318; }
        .gateway-footer { text-align: center; margin-top: 40px; padding-top: 25px; border-top: 1px solid #e2e8f0; }
        .gateway-footer a { background: #1e293b; color: #ffffff; text-decoration: none; font-weight: 600; padding: 12px 24px; border-radius: 4px; border: 1px solid #475569; font-size: 13px; text-transform: uppercase; display: inline-block; }
    </style>
</head>
<body>
<div class="wrapper">
    <div class="branding-header">
        <h1>Small Industries Wing, Balochistan</h1>
        <p>National Trainee Enrollment & Registration Portal — Directorate Training Division</p>
    </div>
    <div class="accent-strip"></div>
    <form class="form-body" method="POST" action="/">
        <div class="form-section-title">A. CENTER ALLOCATION DETAILS</div>
        <div class="input-row" style="grid-template-columns: 1fr;">
            <div class="field-box">
                <label>Center / DDO Unit Name</label>
                <select name="center_name" required>
                    <option value="">-- Choose Assigned Location --</option>
                    {% for item in centers %}
                    <option value="{{ item.center_name }}">{{ item.center_name }}</option>
                    {% endfor %}
                </select>
            </div>
        </div>
        <div class="form-section-title">B. PERSONAL PROFILE PARTICULARS</div>
        <div class="input-row">
            <div class="field-box"><label>Full Name</label><input type="text" name="full_name" required></div>
            <div class="field-box"><label>Father Name</label><input type="text" name="father_name" required></div>
        </div>
        <div class="input-row">
            <div class="field-box"><label>CNIC Number</label><input type="text" name="cnic_number" placeholder="xxxxx-xxxxxxx-x" required></div>
            <div class="field-box"><label>Mobile Number</label><input type="text" name="phone_number" placeholder="03xxxxxxxx" required></div>
        </div>
        <div class="input-row">
            <div class="field-box"><label>Session Batch Cohort</label><input type="text" name="session_cohort" required></div>
            <div class="field-box"><label>Email Address</label><input type="email" name="email_address" required></div>
        </div>
        <div class="input-row" style="grid-template-columns: 1fr;">
            <div class="field-box"><label>Assigned Course Module / Trade</label><input type="text" name="course_module" required></div>
        </div>
        <div class="form-section-title">C. STATUS AND DEMOGRAPHICS</div>
        <div class="input-row">
            <div class="field-box">
                <label>Gender Classification</label>
                <select name="gender" required>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                </select>
            </div>
            <div class="field-box"><label>Local Status Residency</label><input type="text" name="local_status" required></div>
        </div>
        <div class="form-section-title">D. FINANCIAL DISBURSEMENT ACCOUNTS</div>
        <div class="input-row">
            <div class="field-box"><label>Vendor ID Number</label><input type="text" name="vendor_id"></div>
            <div class="field-box"><label>Bank Account Number (IBAN)</label><input type="text" name="iban"></div>
        </div>
        <div class="input-row">
            <div class="field-box"><label>Monthly Stipend Allowance (Rs.)</label><input type="text" name="stipend"></div>
            <div class="field-box"><label>Wallet Account Number (Easypaisa/Omni)</label><input type="text" name="wallet_number"></div>
        </div>
        <div class="submit-container">
            <button type="submit" class="btn-register">Submit Official Enrollment Registration</button>
        </div>
        <div class="gateway-footer">
            <a href="/admin/login">🛡️ ACCESS ADMIN WORKSPACE / RECORDS CONTROL PANEL</a>
        </div>
    </form>
</div>
</body>
</html>
"""

ADMIN_LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Secure Administrative Login Gateway</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #0f172a; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .login-card { background: #ffffff; padding: 40px; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); width: 100%; max-width: 420px; box-sizing: border-box; }
        h2 { color: #0f172a; margin: 0 0 8px 0; font-size: 20px; text-transform: uppercase; font-weight: 700; text-align: center; }
        .form-group { margin-bottom: 20px; }
        label { display: block; font-size: 11px; font-weight: bold; color: #475569; text-transform: uppercase; margin-bottom: 6px; }
        input { width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 4px; box-sizing: border-box; font-size: 14px; background: #f8fafc; }
        .btn-verify { background: #1e293b; color: white; text-transform: uppercase; font-weight: bold; border: none; width: 100%; padding: 14px; border-radius: 4px; cursor: pointer; width: 100%; }
        .back-link { margin-top: 25px; display: block; font-size: 12px; color: #004d26; text-decoration: none; font-weight: bold; text-align: center; }
    </style>
</head>
<body>
<div class="login-card">
    <h2>Secure Gateway Login</h2>
    <form method="POST" action="/admin/login">
