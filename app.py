import os
import json
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
from jinja2 import ChoiceLoader, FileSystemLoader

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'siw-balochistan-2026-final-key')

app.jinja_loader = ChoiceLoader([
    FileSystemLoader(os.path.join(app.root_path, 'templates')),
    FileSystemLoader(os.path.join(app.root_path, 'templates', 'templates')),
    FileSystemLoader(app.root_path)
])

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
    except:
        return []

def save_data(file_path, data):
    with open(file_path, 'w') as f: json.dump(data if isinstance(data, list) else [], f, indent=4)

load_data(TRAINEES_FILE)
load_data(CENTERS_FILE)
load_data(USERS_FILE)
load_data(DOCS_FILE)

@app.route('/', methods=['GET', 'POST'])
@app.route('/register', methods=['GET', 'POST'])
def public_registration():
    if request.method == 'POST':
        trainees = load_data(TRAINEES_FILE)
        cnic = request.form.get('cnic_number', '').strip()
        phone = request.form.get('phone_number', '').strip()
        vendor = request.form.get('vendor_id', '').strip()
        iban = request.form.get('iban', '').strip()
        
        error_msg = None
        for t in trainees:
            if t.get('cnic_number') == cnic: error_msg = "Submission Denied: CNIC already registered."
            if t.get('phone_number') == phone: error_msg = "Submission Denied: Mobile Number already registered."
            if vendor and t.get('vendor_id') == vendor: error_msg = "Submission Denied: Vendor ID already registered."
            if iban and t.get('iban') == iban: error_msg = "Submission Denied: Bank IBAN Account Number already registered."
            if error_msg: break
                
        if error_msg:
            return f"<div style='color:red; font-family:sans-serif; text-align:center; padding:50px;'><h2>{error_msg}</h2><br><a href='/'>Return to Form</a></div>"

        next_id = len(trainees) + 1
        new_trainee = {
            "id": next_id, "center_name": request.form.get('center_name'), "full_name": request.form.get('full_name'),
            "father_name": request.form.get('father_name'), "cnic_number": cnic, "phone_number": phone,
            "session_cohort": request.form.get('session_cohort'), "email_address": request.form.get('email_address'),
            "course_module": request.form.get('course_module'), "gender": request.form.get('gender'),
            "local_status": request.form.get('local_status'), "vendor_id": vendor if vendor else None,
            "iban": iban if iban else None, "stipend": request.form.get('stipend'), "wallet_number": request.form.get('wallet_number')
        }
        trainees.append(new_trainee)
        save_data(TRAINEES_FILE, trainees)
        return "<div style='color:green; font-family:sans-serif; text-align:center; padding:50px;'><h2>Trainee Enrolled Successfully!</h2><br><a href='/'>Go Back Home</a></div>"
        
    all_centers = load_data(CENTERS_FILE)
    functional_centers = [c for c in all_centers if c.get('status') == 'Functional']
    return render_template('public_form.html', centers=functional_centers)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if username == "admin" and password == "protected123":
            session['user_role'] = 'CENTRAL_ADMIN'
            session['logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        users = load_data(USERS_FILE)
        for u in users:
            if u.get('username') == username and u.get('password') == password:
                session['user_role'] = 'DDO_USER'
                session['logged_in'] = True
                session['assigned_center'] = u.get('center_name')
                return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    role = session.get('user_role')
    
    all_trainees = load_data(TRAINEES_FILE)
    all_centers = load_data(CENTERS_FILE)
    all_docs = load_data(DOCS_FILE)
    all_users = load_data(USERS_FILE)
    
    if role == 'DDO_USER':
        target = session.get('assigned_center')
        view_trainees = [t for t in all_trainees if t.get('center_name') == target]
        view_centers = [c for c in all_centers if c.get('center_name') == target]
        docs_to_me = [d for d in all_docs if d.get('direction') == 'directorate_to_centers']
        docs_from_me = [d for d in all_docs if d.get('direction') == 'centers_to_directorate' and d.get('center_name') == target]
        ddo_accounts = []
    else:
        view_trainees = all_trainees
        view_centers = all_centers
        docs_to_me = [d for d in all_docs if d.get('direction') == 'directorate_to_centers']
        docs_from_me = [d for d in all_docs if d.get('direction') == 'centers_to_directorate']
        ddo_accounts = all_users

    total_trainees = len(view_trainees)
    trade_metrics = {}
    for t in view_trainees:
        trade = t.get('course_module', 'Unassigned')
        trade_metrics[trade] = trade_metrics.get(trade, 0) + 1

    extra_keys = set()
    for c in view_centers:
        fields = c.get('extra_fields_data', {})
        if isinstance(fields, dict):
            for k in fields.keys(): extra_keys.add(k)

    return render_template('dashboard.html', trainees=view_trainees, centers=view_centers, extra_keys=list(extra_keys), total_trainees=total_trainees, trade_metrics=trade_metrics, ddo_accounts=ddo_accounts, all_centers_list=all_centers, docs_to_me=docs_to_me, docs_from_me=docs_from_me)

@app.route('/admin/add-center', methods=['POST'])
def add_center():
    if not session.get('logged_in') or session.get('user_role') != 'CENTRAL_ADMIN': return "Unauthorized", 403
    centers = load_data(CENTERS_FILE)
    ddo_code = request.form.get('ddo_code')
    center_name = request.form.get('center_name')
    status = request.form.get('status')
    sector = request.form.get('sector')
    ddo_name = request.form.get('ddo_name')
    
    payload = {k: v for k, v in request.form.items() if k not in ['ddo_code', 'center_name', 'status', 'sector', 'ddo_name']}
    centers.append({"ddo_code": ddo_code, "center_name": center_name, "status": status, "sector": sector, "ddo_name": ddo_name, "extra_fields_data": payload})
    save_data(CENTERS_FILE, centers)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/create-ddo-user', methods=['POST'])
def create_ddo_user():
    if not session.get('logged_in') or session.get('user_role') != 'CENTRAL_ADMIN': return "Unauthorized", 403
    users = load_data(USERS_FILE)
    users.append({"center_name": request.form.get('center_name'), "username": request.form.get('ddo_username', '').strip(), "password": request.form.get('ddo_password', '').strip()})
    save_data(USERS_FILE, users)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/upload-document', methods=['POST'])
def upload_document():
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    direction = request.form.get('channel_direction')
    file = request.files.get('vault_file')
    if file and file.filename != '':
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        center_name = session.get('assigned_center', 'Directorate Desk') if session.get('user_role') == 'DDO_USER' else request.form.get('target_center', 'Global Desk')
        docs = load_data(DOCS_FILE)
        docs.append({"direction": direction, "filename": filename, "center_name": center_name})
        save_data(DOCS_FILE, docs)
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/download-file/<filename>')
def download_file(filename):
    if not session.get('logged_in'): return redirect(url_for('admin_login'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('public_registration'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
