from flask import Flask, render_template, request, redirect, url_for, jsonify
import os

app = Flask(__name__, template_folder='templates')

# Mock storage to hold submitted trainees without needing a heavy SQL cluster configuration right away
TRAINEE_DATABASE = []

@app.route('/')
def public_intake_portal():
    # Serves the high-fidelity styled government intake layout form
    return render_template('dashboard.html')

@app.route('/admin-secure-gateway-matrix')
def secure_admin_view():
    # Serves a dedicated admin control interface view to display saved student records
    return render_template('admin.html', trainees=TRAINEE_DATABASE)

@app.route('/submit-enrollment', methods=['POST'])
def process_enrollment():
    try:
        data = {
            "center_unit": request.form.get('center_unit_name'),
            "full_name": request.form.get('full_name'),
            "father_name": request.form.get('father_name'),
            "cnic": request.form.get('cnic_number'),
            "mobile": request.form.get('mobile_contact'),
            "batch": request.form.get('session_batch'),
            "email": request.form.get('email_address'),
            "course": request.form.get('assigned_course'),
            "gender": request.form.get('gender_classification'),
            "residency": request.form.get('local_residency'),
            "disability": request.form.get('disability_status'),
            "minority": request.form.get('minority_status'),
            "vendor_id": request.form.get('vendor_id') or "N/A",
            "iban": request.form.get('bank_iban') or "N/A",
            "stipend": request.form.get('monthly_stipend') or "N/A",
            "wallet": request.form.get('mobile_wallet_number') or "N/A"
        }
        TRAINEE_DATABASE.append(data)
        return """
        <script>
            alert("Enrollment data successfully submitted to Small Industries Wing Portal.");
            window.location.href = "/";
        </script>
        """
    except Exception as e:
        return f"Form intake exception occurred: {str(e)}", 400

if __name__ == '__main__':
    # Binds server execution interface safely to Render environments
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
