import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)
DB_FILE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    # Table for training centers
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
    # Table to track custom dynamic columns added by admin
    conn.execute('''
        CREATE TABLE IF NOT EXISTS custom_columns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            column_name TEXT UNIQUE
        )
    ''')
    conn.commit()
    conn.close()

# Initialize the database immediately
init_db()

@app.route('/admin/dashboard')
def admin_dashboard():
    conn = get_db_connection()
    
    # 1. Fetch all custom column headers
    custom_cols = conn.execute('SELECT column_name FROM custom_columns').fetchall()
    col_names = [row['column_name'] for row in custom_cols]
    
    # 2. Add columns to the table if they don't exist in SQLite schema
    for col in col_names:
        try:
            conn.execute(f'ALTER TABLE training_centers ADD COLUMN "{col}" TEXT')
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Column already exists
            
    # 3. Fetch all center records
    centers = conn.execute('SELECT * FROM training_centers').fetchall()
    conn.close()
    
    # Render template with dynamic data
    return render_template('dashboard.html', centers=centers, custom_columns=col_names)

@app.route('/admin/add_center', methods=['POST'])
def add_center():
    conn = get_db_connection()
    s_no = request.form.get('s_no')
    ddo_code = request.form.get('ddo_code')
    center_name = request.form.get('center_name')
    status = request.form.get('status')
    ctype = request.form.get('type')
    ddo_name = request.form.get('ddo_name')
    
    # Core fields
    fields = ['s_no', 'ddo_code', 'center_name', 'status', 'type', 'ddo_name']
    values = [s_no, ddo_code, center_name, status, ctype, ddo_name]
    
    # Handle any dynamic custom fields submitted
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
def add_column():
    column_name = request.form.get('new_column_name').strip()
    if column_name:
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO custom_columns (column_name) VALUES (?)', (column_name,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Avoid duplicates
        conn.close()
    return redirect(url_for('admin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
