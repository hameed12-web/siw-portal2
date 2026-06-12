import os
import sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify

app = Flask(__name__)
app.secret_key = 'siw_balochistan_secret_secure_key_2026'
DB_FILE = 'database.db'

# --- DATABASE LAYER ---
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # 1. Main training centers table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS training_centers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            s_no TEXT,
            ddo_code TEXT,
            center_name TEXT,
            status TEXT,
            type TEXT,
            ddo_name TEXT
        )
    ''')
    # 2. Dynamic schema tracking table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS custom_columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column_name TEXT UNIQUE
        )
    ''')
    # 3. RBAC Application User Authentication table
    conn.execute('''
        CREATE TABLE IF NOT EXISTS system_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')
    
    # Pre-seed default test accounts if the system is completely clean
    try:
        conn.execute("INSERT INTO system_users (username, password, role) VALUES ('admin', 'admin123', 'admin')")
        conn.execute("INSERT INTO system_users (username, password, role) VALUES ('user', 'user123', 'viewer')")
    except sqlite3.IntegrityError:
        pass # Users already exist
        
    conn.commit()
    conn.close()

init_db()

# --- SECURITY INTERCEPTORS (DECORATORS) ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to access this section.', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('admin_login'))
        if session.get('role') != 'admin':
            flash('Access Denied: Administrative privileges required.', 'error')
            return redirect(url_for('admin_dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# --- APPLICATION CORE CONTROLLERS & ROUTING ---

@app.route('/')
def home_redirect():
    return redirect(url_for('admin_login'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM system_users WHERE username = ? AND password = ?', (username, password)).fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid login credentials, please try again.', 'error')
            
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Login - Small Industries Wing, Balochistan</title>
        <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; background: #f4f6f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .login-card { background: white; padding: 40px; border-radius: 8px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 360px; text-align: center; }
            h2 { color: #004d40; margin-bottom: 5px; font-size: 24px; }
            h3 { color: #666; font-weight: 400; font-size: 14px; margin-top: 0; margin-bottom: 25px; }
            input { width: 100%; padding: 12px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; font-size: 14px; }
            button { width: 100%; padding: 12px; background: #004d40; color: white; border: none; border-radius: 4px; font-size: 16px; font-weight: bold; cursor: pointer; }
            button:hover { background: #00332c; }
            .flash-msg { color: #d32f2f; background: #ffebee; padding: 10px; border-radius: 4px; margin-bottom: 15px; font-size: 13px; text-align: left; border: 1px solid #ffcdd2; }
            .hint { font-size: 11px; color: #888; margin-top: 15px; text-align: left; background: #eee; padding: 8px; border-radius: 4px; line-height: 1.4; }
        </style>
    </head>
    <body>
        <div class="login-card">
            <h2>Small Industries Wing</h2>
            <h3>Government of Balochistan</h3>
            
            <!-- Context Alerts Display Engine -->
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash-msg">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            <form method="POST">
                <input type="text" name="username" placeholder="Username" required autofocus>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Sign In</button>
            </form>
            
            <div class="hint">
                <strong>System Accounts:</strong><br>
                • Admin Access: admin / admin123<br>
                • Viewer Access: user / user123
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    conn = get_db_connection()
    
    # 1. Collect dynamic structural modifications tracking array
    custom_cols = conn.execute('SELECT column_name FROM custom_columns').fetchall()
    col_names = [row['column_name'] for row in custom_cols]
    
    # 2. Dynamic runtime table alterations parsing safety synchronization block
    for col in col_names:
        try:
            conn.execute(f'ALTER TABLE training_centers ADD COLUMN "{col}" TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Structural mutation exists, passing pipeline execution safely
            
    # 3. Select complete training record row set matrix arrays
    centers = conn.execute('SELECT * FROM training_centers').fetchall()
    conn.close()
    
    return render_template('dashboard.html', centers=centers, custom_columns=col_names, user_role=session.get('role'))

@app.route('/admin/add_center', methods=['POST'])
@admin_required
def add_center():
    conn = get_db_connection()
    s_no = request.form.get('s_no')
    ddo_code = request.form.get('ddo_code')
    center_name = request.form.get('center_name')
    status = request.form.get('status')
    ctype = request.form.get('type')
    ddo_name = request.form.get('ddo_name')
    
    fields = ['s_no', 'ddo_code', 'center_name', 'status', 'type', 'ddo_name']
    values = [s_no, ddo_code, center_name, status, ctype, ddo_name]
    
    # Process dynamically inserted metadata schema inputs safely
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
@admin_required
def add_column():
    column_name = request.form.get('new_column_name').strip()
    if column_name:
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO custom_columns (column_name) VALUES (?)', (column_name,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass # Avoid duplicate custom headers
        conn.close()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/logout')
def logout():
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)
