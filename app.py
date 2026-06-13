import os
import random
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'siw_balochistan_secure_key_2026')

# --- CONFIGURABLE DATABASE CONNECTION OR FAILSAFE LOCAL STORE ---
RAW_DATABASE_URL = os.environ.get('DATABASE_URL', '')
if not RAW_DATABASE_URL:
    DATABASE_URI = 'sqlite:///siw_balochistan_master.db'
else:
    if RAW_DATABASE_URL.startswith("postgres://"):
        DATABASE_URI = RAW_DATABASE_URL.replace("postgres://", "postgresql://", 1)
    else:
        DATABASE_URI = RAW_DATABASE_URL

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

# =========================================================================
#                    DATABASE CORE LAYOUT SCHEMAS
# =========================================================================

# 1. Training Centers Setup Data
class TrainingCenter(db.Model):
    __tablename__ = 'siw_centers'
    s_no = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ddo_code = db.Column(db.String(100), unique=True, nullable=False)
    center_name = db.Column(db.String(250), nullable=False)
    status = db.Column(db.String(100), nullable=False)        # Functional / Non-Functional
    governance_type = db.Column(db.String(100), nullable=False) # Govt / Private
    ddo_name = db.Column(db.String(200), nullable=False)
    extra_data = db.Column(db.JSON, default=dict)

# 2. Public Trainees Registration Storage Node
class Trainee(db.Model):
    __tablename__ = 'siw_trainees'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    special_id = db.Column(db.String(100), unique=True, nullable=False) # Auto ID Code: SIW-2026-XXXX
    name = db.Column(db.String(200), nullable=False)
    father_name = db.Column(db.String(200), nullable=False)
    cnic = db.Column(db.String(50), nullable=False)
    trade_course = db.Column(db.String(150), nullable=False)
    assigned_ddo_code = db.Column(db.String(100), nullable=False) # Links profile view access control boundary

# 3. Official Document Tracking Communications
class OfficialDocument(db.Model):
    __tablename__ = 'siw_documents'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(250), nullable=False)
    direction = db.Column(db.String(100), nullable=False) # 'Directorate to Center' OR 'Center to Directorate'
    origin_ddo_code = db.Column(db.String(100), nullable=False) # 'SUPER_ADMIN' or specific Center Code
    target_ddo_code = db.Column(db.String(100), nullable=False) # 'ALL_CENTERS' or specific Center Code
    timestamp = db.Column(db.String(100), nullable=False)

# 4. User Credential Directory for Admins & DDOs
class SystemUser(db.Model):
    __tablename__ = 'siw_users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False) # 'ADMIN' or 'DDO'
    assigned_ddo_code = db.Column(db.String(100), nullable=True) # Null for Super Admin

# Standard training center layout properties state tracker container
DYNAMIC_COLUMNS = ['S.No.', 'DDO Code', 'Name of Center', 'Functional/Non-Functional', 'Govt/Private', 'DDO Name']

# =========================================================================
#                    APPLICATION ROUTINGS CONTROLLERS
# =========================================================================

@app.route('/')
def public_portal():
    centers = TrainingCenter.query.order_by(TrainingCenter.s_no.asc()).all()
    return render_template('dashboard.html', centers=centers, columns=DYNAMIC_COLUMNS, current_view='PUBLIC')

@app.route('/register-trainee', methods=['POST'])
def register_trainee():
    name = request.form.get('name', '').strip()
    father_name = request.form.get('father_name', '').strip()
    cnic = request.form.get('cnic', '').strip()
    trade_course = request.form.get('trade_course', '').strip()
    assigned_ddo_code = request.form.get('assigned_ddo_code', '').strip()
    
    if not name or not cnic or not assigned_ddo_code:
        flash("Invalid entry submission data profiles.", "error")
        return redirect(url_for('public_portal'))
        
    # Generate unique identification code algorithm sequence format
    rand_seq = random.randint(1000, 9999)
    special_id = f"SIW-2026-{rand_seq}"
    
    new_trainee = Trainee(
        special_id=special_id, name=name, father_name=father_name,
        cnic=cnic, trade_course=trade_course, assigned_ddo_code=assigned_ddo_code
    )
    db.session.add(new_trainee)
    db.session.commit()
    
    flash(f"Registration Submitted Successfully! Assigned Special ID: {special_id}", "success")
    return redirect(url_for('public_portal'))

@app.route('/login', methods=['POST'])
def system_login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    user = SystemUser.query.filter_by(username=username, password=password).first()
    if user:
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        session['ddo_code'] = user.assigned_ddo_code
        return redirect(url_for('admin_portal'))
    else:
        flash("Access Denied: Invalid Security Credentials.", "error")
        return redirect(url_for('public_portal'))

@app.route('/logout')
def system_logout():
    session.clear()
    return redirect(url_for('public_portal'))

@app.route('/admin-panel')
def admin_portal():
    if 'user_id' not in session:
        return redirect(url_for('public_portal'))
        
    role = session.get('role')
    ddo_code = session.get('ddo_code')
    
    # Scoping views boundary data query layers depending on login role permissions
    if role == 'ADMIN':
        centers = TrainingCenter.query.order_by(TrainingCenter.s_no.asc()).all()
        trainees = Trainee.query.all()
        ddo_users = SystemUser.query.filter_by(role='DDO').all()
        docs_to_centers = OfficialDocument.query.filter_by(direction='Directorate to Center').all()
        docs_from_centers = OfficialDocument.query.filter_by(direction='Center to Directorate').all()
    else:
        # Limited scoped workspace mapping for logged-in DDO user nodes
        centers = TrainingCenter.query.filter_by(ddo_code=ddo_code).all()
        trainees = Trainee.query.filter_by(assigned_ddo_code=ddo_code).all()
        ddo_users = []
        docs_to_centers = OfficialDocument.query.filter(
            (OfficialDocument.direction == 'Directorate to Center') & 
            ((OfficialDocument.target_ddo_code == ddo_code) | (OfficialDocument.target_ddo_code == 'ALL_CENTERS'))
        ).all()
        docs_from_centers = OfficialDocument.query.filter_by(direction='Center to Directorate', origin_ddo_code=ddo_code).all()

    all_registered_centers = TrainingCenter.query.all()
    return render_template(
        'dashboard.html', centers=centers, columns=DYNAMIC_COLUMNS, trainees=trainees, 
        ddo_users=ddo_users, docs_to_centers=docs_to_centers, docs_from_centers=docs_from_centers,
        all_registered_centers=all_registered_centers, current_view='ADMIN', role=role, current_ddo=ddo_code
    )

@app.route('/add-center', methods=['POST'])
def add_center():
    if session.get('role') != 'ADMIN': return "Unauthorized access block.", 403
    ddo_code = request.form.get('ddo_code', '').strip()
    center_name = request.form.get('center_name', '').strip()
    status = request.form.get('status', 'Functional')
    governance_type = request.form.get('governance_type', 'Govt')
    ddo_name = request.form.get('ddo_name', '').strip()
    
    extra_fields = {}
    for col in DYNAMIC_COLUMNS[6:]:
        form_key = f"extra_{col.lower().replace(' ', '_')}"
        extra_fields[col] = request.form.get(form_key, '').strip()

    new_center = TrainingCenter(
        ddo_code=ddo_code, center_name=center_name, status=status,
        governance_type=governance_type, ddo_name=ddo_name, extra_data=extra_fields
    )
    db.session.add(new_center)
    db.session.commit()
    return redirect(url_for('admin_portal'))

@app.route('/add-column', methods=['POST'])
def add_column():
    if session.get('role') != 'ADMIN': return "Unauthorized access block.", 403
    col_name = request.form.get('column_name', '').strip()
    if col_name and col_name not in DYNAMIC_COLUMNS:
        DYNAMIC_COLUMNS.append(col_name)
    return redirect(url_for('admin_portal'))

@app.route('/create-ddo-user', methods=['POST'])
def create_ddo_user():
    if session.get('role') != 'ADMIN': return "Unauthorized access block.", 403
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    assigned_ddo_code = request.form.get('assigned_ddo_code', '').strip()
    
    if username and password and assigned_ddo_code:
        new_user = SystemUser(username=username, password=password, role='DDO', assigned_ddo_code=assigned_ddo_code)
        db.session.add(new_user)
        db.session.commit()
    return redirect(url_for('admin_portal'))

@app.route('/dispatch-document', methods=['POST'])
def dispatch_document():
    if 'user_id' not in session: return "Unauthorized session token.", 403
    title = request.form.get('title', '').strip()
    direction = request.form.get('direction', '')
    
    import datetime
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    if session.get('role') == 'ADMIN':
        target = request.form.get('target_ddo_code', 'ALL_CENTERS')
        new_doc = OfficialDocument(title=title, direction='Directorate to Center', origin_ddo_code='SUPER_ADMIN', target_ddo_code=target, timestamp=now_str)
    else:
