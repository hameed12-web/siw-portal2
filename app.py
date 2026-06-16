from flask import Flask, render_template, request, Response
import os

app = Flask(__name__)

# Security feature: Prevent browsers from caching old, broken form variations
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/')
def main_intake_portal():
    return render_template('dashboard.html')

@app.route('/admin-secure-gateway-matrix')
def secure_admin_view():
    return "<h1>Administrative Board Live Records Matrix View</h1>"

@app.route('/submit-enrollment', methods=['POST'])
def process_enrollment():
    form_payload = request.form.to_dict()
    print("Logged Student Data Payload:", form_payload)
    return "<h3>Registration Submitted Successfully!</h3>"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
