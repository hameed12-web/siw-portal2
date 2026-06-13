import os
from flask import Flask, render_template, request, redirect, url_for, session, flash

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'siw_balochistan_secure_key_9911')

# --- FAILSAFE DATABASE ENVIRONMENT ---
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

# --- ENTERPRISE SYSTEM DATABASE MODELS ---

class TrainingCenter(db.Model):
    __tablename__ = 'siw_centers'
    s_no = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ddo_code = db.Column(db.String(50), unique=True, nullable=False)
    center_name = db.Column(db.String(250), nullable=False)
    status = db.Column(db.String(50), nullable=False)          # Functional / Non-Functional
    governance_type = db.Column(db.String(50), nullable=False)  # Govt / Private
    ddo_name = db.Column(db.String(200), nullable=False)
    extra_data = db.Column(db.JSON, default=dict)

class UserAccount(db.Model):
    __tablename__ = 'siw_users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(50), nullable=False)             # 'admin' or 'ddo'
    assigned_ddo_code = db.Column(db.String(50), nullable=True) # Maps DDO users to their center

class Trainee(db.Model):
    __tablename__ = 'siw_trainees'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    special_id = db.Column(db.String(50), unique=True, nullable=False) # Auto-generated Unique ID
    fullname = db.Column(db.String(200), nullable=False)
    cnic = db.Column(db.String(20), nullable=False)
    trade_course = db.Column(db.String(150), nullable=False)
    ddo_code = db.Column(db.String(50), nullable=False)         # Center where enrolled
    enrollment_date = db.Column(db.String(50), nullable=False)

class DocumentRoute(db.Model):
    __tablename__ = 'siw_documents'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    direction = db.Column(db.String(100), nullable=False)       # 'Directorate to Center' or 'Center to Directorate'
    target_ddo_code = db.Column(db.String(50), nullable=False)
    document_date = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(50), default='Pending')

# Dynamic table schema state columns mapping tracking array
DYNAMIC_COLUMNS = ['S.No.', 'DDO Code', 'Name of Center', 'Functional/Non-Functional', 'Govt/Private', 'DDO Name']

# --- APPLICATIVE ACCESS CONTEXT ROUTES ---

@app.route('/')
def public_enrollment():
    # Public Trainee Enrollment Form view (Default Landing)
    centers = TrainingCenter.query.filter_by(status='Functional').all()
    return render_template('dashboard.html', view='public', centers=centers)

@app.route('/enroll-trainee', methods=['POST'])
def enroll_trainee():
    fullname = request.form.get('fullname', '').strip()
    cnic = request.form.get('cnic', '').strip()
    trade_course = request.form.get('trade_course')
    ddo_code = request.form.get('ddo_code')
    import datetime
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    # Generate next sequential Special ID assignment safely
    total_count = Trainee.query.count()
    special_id = f"SIW-{datetime.date.today().year}-{1001 + total_count}"

    new_trainee = Trainee(
        special_id=special_id, fullname=fullname, cnic=cnic,
        trade_course=trade_course, ddo_code=ddo_code, enrollment_date=today_str
    )
    db.session.add(new_trainee)
    db.session.commit()
    
    flash(f"Enrollment Successful! Your Unique Trainee Special ID is: {special_id}", "success")
    return redirect(url_for('public_enrollment'))

@app.route('/login', methods=['POST'])
def auth_login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    user = UserAccount.query.filter_by(username=username, password=password).first()
    
    if user:
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        session['assigned_ddo_code'] = user.assigned_ddo_code
        return redirect(url_for('portal_dashboard'))
    
    flash("Invalid Identification Credentials. Access Refused.", "danger")
    return redirect(url_for('public_enrollment'))

@app.route('/logout')
def auth_logout():
    session.clear()
    return redirect(url_for('public_enrollment'))

@app.route('/portal')
def portal_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('public_enrollment'))
        
    role = session.get('role')
    assigned_ddo = session.get('assigned_ddo_code')

    # Security Query Filters based on Account Access Roles
    if role == 'admin':
        centers = TrainingCenter.query.order_by(TrainingCenter.s_no.asc()).all()
        trainees = Trainee.query.all()
        users = UserAccount.query.filter(UserAccount.role != 'admin').all()
        docs = DocumentRoute.query.all()
    else:
        # Strict DDO isolation: only load data belonging to their assigned DDO Code
        centers = TrainingCenter.query.filter_by(ddo_code=assigned_ddo).all()
        trainees = Trainee.query.filter_by(ddo_code=assigned_ddo).all()
        users = []
        docs = DocumentRoute.query.filter_by(target_ddo_code=assigned_ddo).all()

    return render_template(
        'dashboard.html', view='portal', role=role, centers=centers, 
        columns=DYNAMIC_COLUMNS, trainees=trainees, users=users, docs=docs, assigned_ddo=assigned_ddo
    )

# --- ADMIN SYSTEM UTILITIES CONTROL ENDPOINTS ---

@app.route('/add-center', methods=['POST'])
def add_center():
    if session.get('role') != 'admin': return "Access Unauthorised", 403
    ddo_code = request.form.get('ddo_code', '').strip()
    center_name = request.form.get('center_name', '').strip()
    status = request.form.get('status')
    governance_type = request.form.get('governance_type')
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
    return redirect(url_for('portal_dashboard'))

@app.route('/add-column', methods=['POST'])
def add_column():
    if session.get('role') != 'admin': return "Access Unauthorised", 403
    col_name = request.form.get('column_name', '').strip()
    if col_name and col_name not in DYNAMIC_COLUMNS:
        DYNAMIC_COLUMNS.append(col_name)
    return redirect(url_for('portal_dashboard'))

@app.route('/create-ddo-user', methods=['POST'])
def create_ddo_user():
    if session.get('role') != 'admin': return "Access Unauthorised", 403
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    ddo_code = request.form.get('ddo_code')
    
    new_user = UserAccount(username=username, password=password, role='ddo', assigned_ddo_code=ddo_code)
    db.session.add(new_user)
    db.session.commit()
    flash(f"User access created for DDO Code: {ddo_code}", "success")
    return redirect(url_for('portal_dashboard'))

@app.route('/route-document', methods=['POST'])
def route_document():
    if 'user_id' not in session: return "Access Unauthorised", 403
    title = request.form.get('title', '').strip()
    direction = request.form.get('direction')
    import datetime
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    if session.get('role') == 'admin':
        target_ddo_code = request.form.get('target_ddo_code')
    else:
        target_ddo_code = session.get('assigned_ddo_code')
        direction = 'Center to Directorate' # Enforce direction for DDOs

    new_doc = DocumentRoute(title=title, direction=direction, target_ddo_code=target_ddo_code, document_date=today_str)
    db.session.add(new_doc)
    db.session.commit()
    flash("Document filed and routed successfully.", "success")
    return redirect(url_for('portal_dashboard'))

# --- FORCE STRUCTURAL SYSTEM SEED SEUQUENCE ARCHITECTURE ---
with app.app_context():
    db.create_all()
    # Auto-seed core default system Master Admin User Account if clean boot environment
    if not UserAccount.query.filter_by(username='admin').first():
        admin_seed = UserAccount(username='admin', password='siwadminportalbalochistan', role='admin')
        db.session.add(admin_seed)
        db.session.commit()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
