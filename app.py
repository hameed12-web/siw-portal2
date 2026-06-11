import os
import json
from flask import Flask, request, redirect, url_for, session, send_from_directory, render_template_string

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'siw-balochistan-2026-fixed-master-key')

UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', '/opt/render/project/src/static/uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

DATA_DIR = os.environ.get('DATA_DIR', '/opt/render/project/src/data_store')
os.makedirs(DATA_DIR, exist_ok=True)

TRAINEES_FILE = os.path.join(DATA_DIR, 'trainees.json')
CENTERS_FILE = os.path.join(DATA_DIR, 'centers.json')
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
DOCS_FILE = os.path.join(DATA_DIR, 'docs.json')

def load_data(file_path):
    if not os.path.exists(file_path):
        with open(file_path, 'w') as f: json.dump([], f)
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except: return []

def save_data(file_path, data):
    with open(file_path, 'w') as f: json.dump(data if isinstance(data, list) else [], f, indent=4)

# Force load variables
load_data(TRAINEES_FILE)
load_data(CENTERS_FILE)
load_data(USERS_FILE)
load_data(DOCS_FILE)

# ----------------------------------------------------
# VISUAL HTML INJECTIONS (CRASH-PROOF HARDCODED PAGES)
# ----------------------------------------------------
PUBLIC_FORM_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Small Industries Wing, Balochistan</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #0f172a; margin: 0; padding: 40px 20px; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; }
        .wrapper { width: 100%; max-width: 850px; background: #ffffff; border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); overflow: hidden; }
        .branding-header { background: #004d26; color: #ffffff; padding: 35px 20px; text-align: center; }
        .branding-header h1 { margin: 0; font-size: 26px; text-transform: uppercase; font-weight: 700; }
        .accent-strip { background: #d4af37; height: 5px; }
        .form-body { padding: 40px; }
        .form-section-title { font-size: 14px; color: #004d26; font-weight: bold; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; margin-top: 30px; margin-bottom: 18px; text-transform: uppercase; }
        .input-row { display: grid; grid-template-columns: 1fr; gap: 20px; margin-bottom: 15px; }
        @media(min-width: 768px) { .input-row { grid-template-columns: 1fr 1fr; } }
        .field-box { display: flex; flex-direction: column; }
        .field-box label { font-size: 12px; font-weight: 600; margin-bottom: 6px; color: #34495e; text-transform: uppercase; }
        .field-box input, .field-box select { padding: 11px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 14px; background-color: #f8fafc; }
        .btn-register { background: #004d26; color: #fff; border: none; padding: 15px; border-radius: 4px; font-size: 15px; font-weight: bold; width: 100%; cursor: pointer; text-transform: uppercase; }
        .gateway-footer { text-align: center; margin-top: 40px; padding-top: 25px; border-top: 1px solid #e2e8f0; }
        .gateway-footer a { background: #1e293b; color: #ffffff; text-decoration: none; font-weight: 600; padding: 12px 24px; border-radius: 4px; font-size: 13px; text-transform: uppercase; display: inline-block; }
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
        <div class="input-row">
            <div class="field-box" style="grid-column: span 2;">
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
            <div class="field-box"><label>Mobile Number</label><input type="text" name="phone_number" required></div>
        </div>
        <div class="input-row">
            <div class="field-box"><label>Session Batch</label><input type="text" name="session_cohort" required></div>
            <div class="field-box"><label>Email Address</label><input type="email" name="email_address" required></div>
        </div>
        <div class="input-row" style="grid-template-columns: 1fr;">
            <div class="field-box"><label>Assigned Course Module</label><input type="text" name="course_module" required></div>
        </div>
        <div class="form-section-title">C. STATUS AND DEMOGRAPHICS</div>
        <div class="input-row">
            <div class="field-box">
                <label>Gender</label>
                <select name="gender" required>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                </select>
            </div>
            <div class="field-box"><label>Local Status</label><input type="text" name="local_status" required></div>
        </div>
        <div class="form-section-title">D. FINANCIAL DISBURSEMENT ACCOUNTS</div>
        <div class="input-row">
            <div class="field-box"><label>Vendor ID</label><input type="text" name="vendor_id"></div>
            <div class="field-box"><label>Bank IBAN</label><input type="text" name="iban"></div>
        </div>
        <div class="input-row">
            <div class="field-box"><label>Monthly Stipend</label><input type="text" name="stipend"></div>
            <div class="field-box"><label>Wallet Number</label><input type="text" name="wallet_number"></div>
        </div>
        <button type="submit" class="btn-register">Submit Enrollment Registration</button>
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
<html>
<head>
    <meta charset="UTF-8">
    <title>Secure Administrative Login Gateway</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #0f172a; margin: 0; padding: 20px; display: flex; justify-content: center; align-items: center; min-height: 100vh; }
        .login-card { background: #ffffff; padding: 40px; border-radius: 8px; box-shadow: 0 10px 25px rgba(0,0,0,0.3); width: 100%; max-width: 420px; }
        h2 { color: #0f172a; margin: 0 0 8px 0; font-size: 20px; text-transform: uppercase; font-weight: 700; text-align: center; }
        .form-group { margin-bottom: 20px; }
        label { display: block; font-size: 11px; font-weight: bold; color: #475569; text-transform: uppercase; margin-bottom: 6px; }
        input { width: 100%; padding: 12px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 14px; background: #f8fafc; box-sizing: border-box; }
        .btn-verify { background: #1e293b; color: white; text-transform: uppercase; font-weight: bold; border: none; width: 100%; padding: 14px; border-radius: 4px; cursor: pointer; }
        .back-link { margin-top: 25px; display: block; font-size: 12px; color: #004d26; text-decoration: none; font-weight: bold; text-align: center; }
    </style>
</head>
<body>
<div class="login-card">
    <h2>Secure Gateway Login</h2>
    <form method="POST" action="/admin/login">
        <div class="form-group">
            <label>Username Account ID</label>
            <input type="text" name="username" required>
        </div>
        <div class="form-group">
            <label>Password</label>
            <input type="password" name="password" required>
        </div>
        <button type="submit" class="btn-verify">Verify Identity Credentials</button>
    </form>
    <a href="/" class="back-link">📋 Return to Public Portal Form</a>
</div>
</body>
</html>
"""

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Admin Dashboard Control Command Portal</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; background-color: #0f172a; margin: 0; padding-bottom: 60px; color: #1e293b; }
        .navbar { background: #1e293b; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; color: white; border-bottom: 3px solid #d4af37; }
        .navbar h2 { margin: 0; font-size: 16px; text-transform: uppercase; }
        .container { max-width: 1400px; margin: 30px auto; padding: 0 20px; }
        .metrics-board { display: grid; grid-template-columns: 1fr 3fr; gap: 20px; margin-bottom: 30px; }
        .calc-card { background: #ffffff; border-radius: 8px; padding: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #004d26; text-align: center; }
        .calc-card .count { font-size: 48px; font-weight: 800; color: #004d26; margin: 10px 0; }
        .trade-breakdown { background: #ffffff; border-radius: 8px; padding: 20px; }
