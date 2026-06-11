import os
import json
from flask import Flask, request, redirect, url_for, session, send_from_directory

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'siw-balochistan-2026-bulletproof-json')

# Persistent Data Storage System Paths Config
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
            d = json.load(f)
            return d if isinstance(d, list) else []
    except: return []

def save_data(file_path, data):
    with open(file_path, 'w') as f: json.dump(data if isinstance(data, list) else [], f, indent=4)

# ----------------------------------------------------
# VISUAL CLIENT INTAKE REGISTRATION PORTAL FRONTEND
# ----------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def public_registration():
    if request.method == 'POST':
        trainees = load_data(TRAINEES_FILE)
        cnic = request.form.get('cnic_number', '').strip()
        phone = request.form.get('phone_number', '').strip()
        vendor = request.form.get('vendor_id', '').strip()
        iban = request.form.get('iban', '').strip()
        
        # RESTRICT DUPLICATE ENTRIES ENGINE
        for t in trainees:
            if t.get('cnic_number') == cnic:
                return "<div style='color:red; font-family:sans-serif; text-align:center; padding:50px;'><h2>Submission Denied: This CNIC Number is already registered.</h2><br><a href='/'>Return to Form</a></div>"
            if t.get('phone_number') == phone:
                return "<div style='color:red; font-family:sans-serif; text-align:center; padding:50px;'><h2>Submission Denied: This Mobile Number is already in use.</h2><br><a href='/'>Return to Form</a></div>"
            if vendor and t.get('vendor_id') == vendor:
                return "<div style='color:red; font-family:sans-serif; text-align:center; padding:50px;'><h2>Submission Denied: This Vendor ID is already registered.</h2><br><a href='/'>Return to Form</a></div>"
            if iban and t.get('iban') == iban:
                return "<div style='color:red; font-family:sans-serif; text-align:center; padding:50px;'><h2>Submission Denied: This Bank IBAN Account Number is already registered.</h2><br><a href='/'>Return to Form</a></div>"

        new_trainee = {
            "id": len(trainees) + 1,
            "center_name": request.form.get('center_name', ''),
            "full_name": request.form.get('full_name', ''),
            "father_name": request.form.get('father_name', ''),
            "cnic_number": cnic,
            "phone_number": phone,
            "session_cohort": request.form.get('session_cohort', ''),
            "email_address": request.form.get('email_address', ''),
            "course_module": request.form.get('course_module', ''),
            "gender": request.form.get('gender', ''),
            "local_status": request.form.get('local_status', ''),
            "vendor_id": vendor if vendor else None,
            "iban": iban if iban else None,
            "stipend": request.form.get('stipend', ''),
            "wallet_number": request.form.get('wallet_number', '')
        }
        trainees.append(new_trainee)
        save_data(TRAINEES_FILE, trainees)
        return "<div style='color:green; font-family:sans-serif; text-align:center; padding:50px;'><h2>Trainee Profile Processed and Enrolled Successfully!</h2><br><a href='/'>Go Back to Intake Form</a></div>"

    centers = load_data(CENTERS_FILE)
    center_options = "".join([f'<option value="{c.get("center_name")}">{c.get("center_name")}</option>' for c in centers if c.get('status') == 'Functional'])

    # Standard Self-Contained HTML layout
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Small Industries Wing, Balochistan - Registration Portal</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background-color: #0f172a; margin: 0; padding: 40px 20px; color: #2c3e50; display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 100vh; box-sizing: border-box; }}
            .wrapper {{ width: 100%; max-width: 850px; background: #ffffff; border-radius: 8px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); overflow: hidden; }}
            .branding-header {{ background: #004d26; color: #ffffff; padding: 35px 20px; text-align: center; }}
            .branding-header h1 {{ margin: 0; font-size: 26px; text-transform: uppercase; letter-spacing: 1px; font-weight: 700; }}
            .branding-header p {{ margin: 8px 0 0 0; font-size: 13px; opacity: 0.85; }}
            .accent-strip {{ background: #d4af37; height: 5px; }}
            .form-body {{ padding: 40px; }}
            .form-section-title {{ font-size: 14px; color: #004d26; font-weight: bold; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; margin-top: 30px; margin-bottom: 18px; text-transform: uppercase; }}
            .input-row {{ display: grid; grid-template-columns: 1fr; gap: 20px; margin-bottom: 15px; }}
            @media(min-width: 768px) {{ .input-row {{ grid-template-columns: 1fr 1fr; }} }}
            .field-box {{ display: flex; flex-direction: column; }}
            .field-box label {{ font-size: 12px; font-weight: 600; margin-bottom: 6px; color: #34495e; text-transform: uppercase; }}
            .field-box input, .field-box select {{ padding: 11px; border: 1px solid #cbd5e1; border-radius: 4px; font-size: 14px; background-color: #f8fafc; box-sizing: border-box; }}
            .btn-register {{ background: #004d26; color: #fff; border: none; padding: 15px; border-radius: 4px; font-size: 15px; font-weight: bold; width: 100%; cursor: pointer; text-transform: uppercase; transition: background 0.2s; }}
            .btn-register:hover {{ background: #003318; }}
            .gateway-footer {{ text-align: center; margin-top: 40px; padding-top: 25px; border-top: 1px solid #e2e8f0; }}
            .gateway-footer a {{ background: #1e293b; color: #ffffff; text-decoration: none; font-weight: 600; padding: 12px 24px; border-radius: 4px; border: 1px solid #475569; font-size: 13px; text-transform: uppercase; display: inline-block; }}
        </style>
    </head>
    <body>
    <div class="wrapper">
        <div class="branding-header">
            <h1>Small Industries Wing, Balochistan</h1>
            <p>National Trainee Enrollment & Registration Portal — Directorate Training Division</p>
        </div>
        <div class="accent-strip"></div>
        <form class="form-body" method="POST" action="/register">
            <div class="form-section-title">A. CENTER ALLOCATION DETAILS</div>
            <div class="input-row" style="grid-template-columns: 1fr;">
                <div class="field-box">
                    <label>Center / DDO Unit Name</label>
                    <select name="center_name" required>
                        <option value="">-- Choose Assigned Location --</option>
                        {center_options}
                    </select>
                </div>
            </div>
            <div class="form-section-title">B. PERSONAL PROFILE PARTICULARS</div>
            <div class="input-row">
                <div class="field-box"><label>Full Name</label><input type="text" name="full_name" required></div>
                <div class="field-box"><label>Father Name</label><input type="text" name="father_name" required></div>
            </div>
            <div class="input-row">
                <div class="field-box"><label>CNIC Number</label><input type="text" name="cnic_number" required></div>
                <div class="field-box"><label>Mobile Contact Number</label><input type="text" name="phone_number" required></div>
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
                <div class="field-box"><label>Vendor Identification Number</label><input type="text" name="vendor_id"></div>
                <div class="field-box"><label>Bank Account Number (IBAN)</label><input type="text" name="iban"></div>
            </div>
