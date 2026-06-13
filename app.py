import os
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# 🟩 FIX: The standard variable name is DATABASE_URL on Render, 
# but it must match exactly with SQLALCHEMY_DATABASE_URI inside Flask
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///siw_balochistan.db')

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# 🟩 FIX: Changed SQLALCHEMY_DATABASE_URL -> SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Model for training centers
class TrainingCenter(db.Model):
    __tablename__ = 'training_centers'
    
    s_no = db.Column(db.Integer, primary_key=True)
    ddo_code = db.Column(db.String(50), nullable=False)
    center_name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    center_type = db.Column(db.String(50), nullable=False)
    ddo_name = db.Column(db.String(150), nullable=False)
    extra_data = db.Column(db.JSON, default=dict)

# Track dynamic columns across session page reloads
DYNAMIC_COLUMNS = ['S.No.', 'DDO Code', 'Name of Center', 'Functional/Non-Functional', 'Govt/Private', 'DDO Name']

@app.route('/')
def index():
    centers = TrainingCenter.query.order_by(TrainingCenter.s_no.asc()).all()
    return render_template('admin.html', centers=centers, columns=DYNAMIC_COLUMNS)

@app.route('/add-center', methods=['POST'])
def add_center():
    ddo_code = request.form.get('ddo_code')
    center_name = request.form.get('center_name')
    status = request.form.get('status')
    center_type = request.form.get('center_type')
    ddo_name = request.form.get('ddo_name')
    
    extra_fields = {}
    for col in DYNAMIC_COLUMNS[6:]:
        form_key = f"extra_{col.lower().replace(' ', '_')}"
        extra_fields[col] = request.form.get(form_key, '')

    new_center = TrainingCenter(
        ddo_code=ddo_code,
        center_name=center_name,
        status=status,
        center_type=center_type,
        ddo_name=ddo_name,
        extra_data=extra_fields
    )
    db.session.add(new_center)
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/add-column', methods=['POST'])
def add_column():
    col_name = request.form.get('column_name').strip()
    if col_name and col_name not in DYNAMIC_COLUMNS:
        DYNAMIC_COLUMNS.append(col_name)
    return redirect(url_for('index'))

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
