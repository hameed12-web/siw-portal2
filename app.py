from flask import Flask, render_template, jsonify, request
import os

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# In-Memory Database Simulation configured for Small Industries Wing, Balochistan
TRAINING_CENTERS = [
    {
        "s_no": 1,
        "ddo_code": "QA-4052",
        "center_name": "Vocational Training Institute, Quetta",
        "status": "Functional",
        "type": "Govt",
        "ddo_name": "Mr. Khan Baloch",
        "extra_fields": {}
    },
    {
        "s_no": 2,
        "ddo_code": "WZ-2219",
        "center_name": "Handicrafts Development Centre, Khuzdar",
        "status": "Functional",
        "type": "Govt",
        "ddo_name": "Sarfraz Ahmed",
        "extra_fields": {}
    },
    {
        "s_no": 3,
        "ddo_code": "SIW-009",
        "center_name": "Balochistan Technical Academy",
        "status": "Non-Functional",
        "type": "Private",
        "ddo_name": "Ali Shah",
        "extra_fields": {}
    }
]

DYNAMIC_COLUMNS = []

@app.route('/')
def dashboard():
    # Primary application dashboard endpoint 
    return render_template('dashboard.html', 
                           title="Small Industries Wing, Balochistan", 
                           centers=TRAINING_CENTERS, 
                           columns=DYNAMIC_COLUMNS)

@app.route('/api/centers', methods=['GET', 'POST'])
def manage_centers():
    if request.method == 'POST':
        data = request.json
        new_center = {
            "s_no": len(TRAINING_CENTERS) + 1,
            "ddo_code": data.get('ddo_code'),
            "center_name": data.get('center_name'),
            "status": data.get('status', 'Functional'),
            "type": data.get('type', 'Govt'),
            "ddo_name": data.get('ddo_name'),
            "extra_fields": data.get('extra_fields', {})
        }
        TRAINING_CENTERS.append(new_center)
        return jsonify({"success": True, "data": new_center})
    return jsonify(TRAINING_CENTERS)

@app.route('/api/columns', methods=['POST'])
def add_custom_column():
    data = request.json
    column_name = data.get('column_name', '').strip()
    
    if column_name and column_name not in DYNAMIC_COLUMNS:
        DYNAMIC_COLUMNS.append(column_name)
        # Structural migration fallback loop over stored rows
        for center in TRAINING_CENTERS:
            if column_name not in center["extra_fields"]:
                center["extra_fields"][column_name] = "N/A"
        return jsonify({"success": True, "columns": DYNAMIC_COLUMNS})
    
    # Line 216 - Resolved Indentation Error structural safeguard placement
    else:
        return jsonify({"success": False, "error": "Invalid or duplicate column name"}), 400

if __name__ == '__main__':
    # Dynamic port allocation optimized for Render container environment bindings
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
