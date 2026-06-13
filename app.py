import os
import random
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'siw_balochistan_secure_prod_key_2026')

# --- ROBUST FAILSAFE DATABASE ROUTING ENGINE ---
RAW_DATABASE_URL = os.environ.get('DATABASE_URL', '')
if not RAW_DATABASE_URL:
    DATABASE_URI = 'sqlite:///siw_balochistan_enterprise.db'
else:
    if RAW_DATABASE_URL.startswith("postgres://"):
        DATABASE_URI = RAW_DATABASE_URL.replace("postgres://", "postgresql://", 1)
    else:
        DATABASE_URI = RAW_DATABASE_URL

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

# --- PRODUCTION DATA SCHEMAS & TABLES ---
class TrainingCenter(db.Model):
    __tablename__ = 'siw_centers'
    s_no = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ddo_code = db.Column(db.String(50), unique=True, nullable=False)
    center_name = db.Column(db.String(250), nullable=False)
    status = db.Column(db.String(50), default='Functional')  # Functional / Non-Functional
    governance_type = db.Column(db.String(50), default='Govt')  # Govt / Private
    ddo_name = db.Column(db.String(200), nullable=False)
    extra_data = db.Column(db.JSON, default=dict)

class Trainee(db.Model):
    __tablename__ = 'siw_trainees'
    id = db.Column(db.Integer, primary_key=True)
    trainee_id = db.Column(db.String(100), unique=True, nullable=False) # SIW-2026-XXXX
    name = db.Column(db.String(200), nullable=False)
    cnic = db.Column(db.String(20), nullable=False)
    trade = db.Column(db.String(150), nullable=False)
    allocated_center_code = db.Column(db.String(50), nullable=False)
    verification_status = db.Column(db.String(50), default='Pending Review')

class DocumentRegistry(db.Model):
    __tablename__ = 'siw_documents'
    id = db.Column(db.Integer, primary_key=True)
    direction = db.Column(db.String(100), nullable=False) # 'directorate_to_center' or 'center_to_directorate'
    title = db.Column(db.String(300), nullable=False)
    reference_no = db.Column(db.String(100), nullable=False)
    origin_center_code = db.Column(db.String(50), nullable=False) # DDO code mapping identifier

class DDOUser(db.Model):
    __tablename__ = 'siw_ddo_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False) # Production Plain-Hash Fallback
    allocated_ddo_code = db.Column(db.String(50), nullable=False)

# Track custom headers persistently
DYNAMIC_COLUMNS = ['S.No.', 'DDO Code', 'Name of Center', 'Functional/Non-Functional', 'Govt/Private', 'DDO Name']

# --- WEB FLOW ENDPOINTS & ROUTING CONTROLLERS ---

@app.route('/')
def index():
    # Public facing workspace containing Registration Module + Secure Gateway Portals
    centers = TrainingCenter.query.all()
    return render_template('dashboard.html', view_context='public_enrollment', centers=centers, columns=DYNAMIC_COLUMNS)

@app.route('/public-register', methods=['POST'])
def public_register():
    name = request.form.get('name', '').strip()
    cnic = request.form.get('cnic', '').strip()
    trade = request.form.get('trade', '').strip()
    center_code = request.form.get('center_code', '').strip()
    
    if name and cnic and center_code:
        # Generate clean sequential randomized ID parameters: SIW-2026-XXXX
        generated_id = f"SIW-2026-{random.randint(1000, 9999)}"
        new_student = Trainee(
            trainee_id=generated_id, name=name, cnic=cnic, trade=trade, allocated_center_code=center_code
        )
        db.session.add(new_student)
        db.session.commit()
        flash(f"Registration Submitted Successfully! Your Special ID is: {generated_id}", "success")
    else:
        flash("Registration failed. Please complete all field entry points.", "danger")
    return redirect(url_for('index'))

@app.route('/login-gateway', methods=['POST'])
def login_gateway():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    
    if username == 'admin' and password == 'admin123':
        session['user_role'] = 'admin'
        session['user_identity'] = 'Super Directorate'
        return redirect(url_for('admin_panel'))
        
    ddo_check = DDOUser.query.filter_by(username=username, password=password).first()
    if ddo_check:
        session['user_role'] = 'ddo'
        session['user_identity'] = ddo_check.allocated_ddo_code
        return redirect(url_for('ddo_panel'))
        
    flash("Invalid Authorization Credentials.", "danger")
    return redirect(url_for('index'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# --- AUTHENTICATED ACCESS DOMAINS ---

@app.route('/admin-portal')
def admin_panel():
    if session.get('user_role') != 'admin':
        return "Unauthorized Access Area.", 403
    centers = TrainingCenter.query.order_by(TrainingCenter.s_no.asc()).all()
    trainees = Trainee.query.all()
    documents = DocumentRegistry.query.all()
    ddo_users = DDOUser.query.all()
    return render_template('dashboard.html', view_context='admin_dashboard', centers=centers, trainees=trainees, documents=documents, ddo_users=ddo_users, columns=DYNAMIC_COLUMNS)

@app.route('/ddo-portal')
def ddo_panel():
    if session.get('user_role') != 'ddo':
        return "Unauthorized Access Area.", 403
    ddo_code = session.get('user_identity')
    center_info = TrainingCenter.query.filter_by(ddo_code=ddo_code).first()
    assigned_trainees = Trainee.query.filter_by(allocated_center_code=ddo_code).all()
    shared_documents = DocumentRegistry.query.filter((DocumentRegistry.origin_center_code == ddo_code) | (DocumentRegistry.direction == 'directorate_to_center')).all()
    return render_template('dashboard.html', view_context='ddo_dashboard', center=center_info, trainees=assigned_trainees, documents=shared_documents)

# --- ENGINE DATA ALTERATION SUB-ENDPOINTS ---

@app.route('/add-center', methods=['POST'])
def add_center():
    if session.get('user_role') != 'admin': return "Forbidden", 403
    ddo_code = request.form.get('ddo_code', '').strip()
    center_name = request.form.get('center_name', '').strip()
    status = request.form.get('status', 'Functional')
    governance_type = request.form.get('governance_type', 'Govt')
    ddo_name = request.form.get('ddo_name', '').strip()
    
    extra_fields = {}
    for col in DYNAMIC_COLUMNS[6:]:
        form_key = f"extra_{col.lower().replace(' ', '_')}"
        extra_fields[col] = request.form.get(form_key, '').strip()

    new_center = TrainingCenter(ddo_code=ddo_code, center_name=center_name, status=status, governance_type=governance_type, ddo_name=ddo_name, extra_data=extra_fields)
    db.session.add(new_center)
    db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/add-column', methods=['POST'])
def add_column():
    if session.get('user_role') != 'admin': return "Forbidden", 403
    col_name = request.form.get('column_name', '').strip()
    if col_name and col_name not in DYNAMIC_COLUMNS:
        DYNAMIC_COLUMNS.append(col_name)
    return redirect(url_for('admin_panel'))

@app.route('/create-ddo-account', methods=['POST'])
def create_ddo_account():
    if session.get('user_role') != 'admin': return "Forbidden", 403
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    ddo_code = request.form.get('ddo_code', '').strip()
    
    if username and password and ddo_code:
        new_user = DDOUser(username=username, password=password, allocated_ddo_code=ddo_code)
        db.session.add(new_user)
        db.session.commit()
    return redirect(url_for('admin_panel'))

@app.route('/dispatch-document', methods=['POST'])
def dispatch_document():
    if not session.get('user_role'): return "Forbidden", 403
    direction = request.form.get('direction')
    title = request.form.get('title', '').strip()
    ref_no = request.form.get('ref_no', '').strip()
    
    center_code = session.get('user_identity') if session.get('user_role') == 'ddo' else request.form.get('center_code', 'DIRECTORATE')
    
    new_doc = DocumentRegistry(direction=direction, title=title, reference_no=ref_no, origin_center_code=center_code)
    db.session.add(new_doc)
    db.session.commit()
    
    return redirect(url_for('admin_panel') if session.get('user_role') == 'admin' else url_for('ddo_panel'))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
