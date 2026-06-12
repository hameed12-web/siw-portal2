import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = 'siw_balochistan_highly_secure_session_key_2026'
DB_FILE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # 1. Training Centers Database
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
    # 2. Dynamic Table Extension Schema Registry
    conn.execute('''
        CREATE TABLE IF NOT EXISTS custom_columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column_name TEXT UNIQUE
        )
    ''')
    # 3. Secure Role Based Users Directory
    conn.execute('''
        CREATE TABLE IF NOT EXISTS system_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT,
            assigned_center TEXT
        )
    ''')
    # 4. Trainee Applications Registration Matrix
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
    
    # Auto seed starting data assets if table is empty
    try:
        conn.execute("INSERT INTO system_users (username, password, role, assigned_center) VALUES ('admin', 'admin123', 'admin', 'ALL')")
        conn.execute("INSERT INTO system_users (username, password, role, assigned_center) VALUES ('quettajr', 'quetta123', 'incharge', 'Quetta Center')")
        conn.execute("INSERT INTO training_centers (s_no, ddo_code, center_name, status, type, ddo_name) VALUES ('1', 'QA-404', 'Quetta Center', 'Functional', 'Government', 'Ali Ahmed')")
    except sqlite3.IntegrityError:
        pass
        
    conn.commit()
    conn.close()

init_db()

# --- AUTHENTICATION ROUTE MIDDLEWARE ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROUTING LOGIC HANDLERS ---

@app.route('/')
def public_enrollment():
    conn = get_db_connection()
    centers = conn.execute('SELECT center_name FROM training_centers WHERE status = "Functional"').fetchall()
    conn.close()
    return render_template('public.html', centers=centers)

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
    flash('Your enrollment registration profile application record has been logged successfully!')
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
            flash('Invalid admin console access credentials.')

    return render_template('login.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    conn = get_db_connection()
    role = session.get('role')
    assigned = session.get('assigned_center')
    
    custom_cols = conn.execute('SELECT column_name FROM custom_columns').fetchall()
    col_names = [row['column_name'] for row in custom_cols]
    
    for col in col_names:
        try:
            conn.execute(f'ALTER TABLE training_centers ADD COLUMN "{col}" TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass
            
    if role == 'admin':
        centers = conn.execute('SELECT * FROM training_centers').fetchall()
        trainees = conn.execute('SELECT * FROM trainees').fetchall()
    else:
        centers = conn.execute('SELECT * FROM training_centers WHERE center_name = ?', (assigned,)).fetchall()
        trainees = conn.execute('SELECT * FROM trainees WHERE center_name = ?', (assigned,)).fetchall()

    conn.close()
    return render_template('dashboard.html', centers=centers, trainees=trainees, custom_columns=col_names, user_role=role, assigned_center=assigned)

@app.route('/admin/add_center', methods=['POST'])
@login_required
def add_center():
    if session.get('role') != 'admin':
        return "Access Denied", 403
    conn = get_db_connection()
    s_no = request.form.get('s_no')
    ddo_code = request.form.get('ddo_code')
    center_name = request.form.get('center_name')
    status = request.form.get('status')
    ctype = request.form.get('type')
    ddo_name = request.form.get('ddo_name')
    
    fields = ['s_no', 'ddo_code', 'center_name', 'status', 'type', 'ddo_name']
    values = [s_no, ddo_code, center_name, status, ctype, ddo_name]
    
    custom_cols = conn.execute('SELECT column_name FROM custom_columns').fetchall()
    for col in custom_cols:
        col_name = col['column_name']
        fields.append(f'"{col_name}"')
        values.append(request.form.get(col_name, ''))
        
    placeholders = ', '.join(['?'] * len(values))
    field_str = ', '.join(fields)
    
    conn.execute(f'INSERT INTO training_centers ({field_str}) VALUES ({placeholders})', values)
    conn.commit()
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/add_column', methods=['POST'])
@login_required
def add_column():
    if session.get('role') != 'admin':
        return "Access Denied", 403
    column_name = request.form.get('new_column_name').strip()
    if column_name:
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO custom_columns (column_name) VALUES (?)', (column_name,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/create_user', methods=['POST'])
@login_required
def create_user():
    if session.get('role') != 'admin':
        return "Access Denied", 403
    username = request.form.get('username').strip()
    password = request.form.get('password').strip()
    center_name = request.form.get('center_name')
    
    conn = get_db_connection()
    try:
        conn.execute('INSERT INTO system_users (username, password, role, assigned_center) VALUES (?, ?, "incharge", ?)', (username, password, center_name))
        conn.commit()
    except sqlite3.IntegrityError:
        pass
    conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def logout():
    session.clear()
    return redirect(url_for('public_enrollment'))

if __name__ == '__main__':
    app.run(debug=True)
