import os
import sqlite3
from functools import wraps
from flask import Flask, request, redirect, url_for, session, flash, render_template_string

app = Flask(__name__)
app.secret_key = 'siw_balochistan_highly_secure_session_key_2026'
DB_FILE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # 1. Training Centers Setup Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS training_centers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            s_no TEXT,
            ddo_code TEXT,
            center_name TEXT UNIQUE,
            status TEXT,
            type TEXT,
            ddo_name TEXT
        )
    ''')
    # 2. Dynamic Extra Columns Registry
    conn.execute('''
        CREATE TABLE IF NOT EXISTS custom_columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column_name TEXT UNIQUE
        )
    ''')
    # 3. Secure Role Based Users Table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS system_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            assigned_center TEXT
        )
    ''')
    # 4. Trainee Enrollment System Record Matrix
    conn.execute('''
        CREATE TABLE IF NOT EXISTS trainees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trainee_name TEXT,
            cnic_or_bform TEXT,
            phone_number TEXT,
            center_name TEXT,
            trade_name TEXT,
            enrollment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Pre-seed default authorization access credentials
    try:
        conn.execute("INSERT INTO system_users (username, password, role, assigned_center) VALUES ('admin', 'admin123', 'admin', 'ALL')")
        conn.execute("INSERT INTO system_users (username, password, role, assigned_center) VALUES ('quettajr', 'quetta123', 'incharge', 'Quetta Center')")
        conn.execute("INSERT INTO training_centers (s_no, ddo_code, center_name, status, type, ddo_name) VALUES ('1', 'QA-404', 'Quetta Center', 'Functional', 'Government', 'Ali Ahmed')")
    except sqlite3.IntegrityError:
        pass
        
    conn.commit()
    conn.close()

init_db()

# --- AUTHENTICATION INTERCEPTORS ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- WEB CONTROLLERS & ROUTING ---

@app.route('/')
def public_enrollment():
    conn = get_db_connection()
    centers = conn.execute('SELECT center_name FROM training_centers WHERE status = "Functional"').fetchall()
    conn.close()
    
    public_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Public Trainee Enrollment - Small Industries Wing, Balochistan</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; margin: 0; padding: 20px; }
            .form-card { max-width: 600px; background: white; margin: 40px auto; padding: 35px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
            header { text-align: center; border-bottom: 2px solid #004d40; padding-bottom: 15px; margin-bottom: 25px; }
            h1 { color: #004d40; margin: 0; font-size: 24px; }
            h2 { font-size: 14px; color: #555; margin: 5px 0 0 0; font-weight: 400; }
            label { display: block; font-weight: bold; margin-bottom: 5px; color: #333; font-size: 14px; }
            input, select { width: 100%; padding: 10px; margin-bottom: 20px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
            button { width: 100%; padding: 12px; background: #004d40; color: white; border: none; border-radius: 4px; font-size: 16px; font-weight: bold; cursor: pointer; }
            button:hover { background: #00332c; }
            .admin-access { text-align: center; margin-top: 30px; }
            .admin-link { color: #555; text-decoration: none; font-size: 13px; background: #e0e0e0; padding: 8px 15px; border-radius: 4px; }
            .admin-link:hover { background: #d5d5d5; color: #000; }
            .alert { padding: 12px; background: #e8f5e9; color: #2e7d32; border-radius: 4px; margin-bottom: 20px; font-size: 14px; border: 1px solid #c8e6c9; }
        </style>
    </head>
    <body>
        <div class="form-card">
            <header>
                <h1>Small Industries Wing, Balochistan</h1>
                <h2>Public Trainee Admission & Enrollment Desk</h2>
            </header>

            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for message in messages %}
                        <div class="alert">✓ {{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            <form action="/submit_enrollment" method="POST">
                <label>Full Name of Trainee</label>
                <input type="text" name="trainee_name" placeholder="Enter Full Name" required>

                <label>CNIC / B-Form Number</label>
                <input type="text" name="cnic" placeholder="e.g., 54401-XXXXXXX-X" required>

                <label>Active Contact Phone Number</label>
                <input type="text" name="phone" placeholder="e.g., 0333-XXXXXXX" required>

                <label>Select Preferred Training Center</label>
                <select name="center_name" required>
                    <option value="">-- Choose Center --</option>
                    {% for center in centers %}
                        <option value="{{ center.center_name }}">{{ center.center_name }}</option>
                    {% endfor %}
                </select>

                <label>Trade Course Selection</label>
                <input type="text" name="trade_name" placeholder="e.g., Tailoring, Computer Systems, Embroidery" required>

                <button type="submit">Submit My Application Enrollment</button>
            </form>

            <div class="admin-access">
                <a href="/admin/login" class="admin-link">🔒 Management Console & Records Access</a>
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(public_html, centers=centers)

@app.route('/submit_enrollment', methods=['POST'])
def submit_enrollment():
    t_name = request.form.get('trainee_name')
    cnic = request.form.get('cnic')
    phone = request.form.get('phone')
    center = request.form.get('center_name')
    trade = request.form.get('trade_name')
    
    conn = get_db_connection()
    conn.execute('INSERT INTO trainees (trainee_name, cnic_or_bform, phone_number, center_name, trade_name) VALUES (?, ?, ?, ?, ?)',
                 (t_name, cnic, phone, center, trade))
    conn.commit()
    conn.close()
    flash('Your enrollment profile application record has been registered successfully!')
    return redirect(url_for('public_enrollment'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'user_id' in session:
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM system_users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        
        if user:
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            session['assigned_center'] = user['assigned_center']
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid login credentials, please try again.', 'error')

    login_html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Console Login - Small Industries Wing, Balochistan</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .card { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 350px; text-align: center; }
            h2 { color: #004d40; margin: 0 0 5px 0; }
            h3 { font-size: 13px; color: #666; font-weight: 400; margin: 0 0 25px 0; }
            input { width: 100%; padding: 11px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
            button { width: 100%; padding: 11px; background: #004d40; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; }
            .err { color: #c62828; font-size: 13px; margin-bottom: 15px; text-align: left; background: #ffebee; padding: 8px; border-radius: 4px; }
            .back-home { margin-top: 15px; display: block; font-size: 12px; color: #004d40; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>Small Industries Wing</h2>
            <h3>Government of Balochistan</h3>
            {% with messages = get_flashed_messages() %}
                {% if messages %}
                    {% for msg in messages %}<div class="err">{{ msg }}</div>{% endfor %}
                {% endif %}
            {% endwith %}
            <form method="POST">
                <input type="text" name="username" placeholder="Console Username" required>
                <input type="password" name="password" placeholder="Console Password" required>
                <button type="submit">Verify & Login</button>
            </form>
            <a href="/" class="back-home">← Back to Enrollment Form</a>
