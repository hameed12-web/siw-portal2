import os
from flask import Flask, request, redirect, url_for, render_template_string

app = Flask(__name__)

# --- FAILSAFE DATABASE CONTEXT ---
RAW_DATABASE_URL = os.environ.get('DATABASE_URL', '')
if not RAW_DATABASE_URL:
    DATABASE_URI = 'sqlite:///siw_balochistan_standalone.db'
else:
    if RAW_DATABASE_URL.startswith("postgres://"):
        DATABASE_URI = RAW_DATABASE_URL.replace("postgres://", "postgresql://", 1)
    else:
        DATABASE_URI = RAW_DATABASE_URL

app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

# --- SYSTEM DATA ENGINE MODEL ---
class TrainingCenter(db.Model):
    __tablename__ = 'siw_training_centers_central'
    
    s_no = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ddo_code = db.Column(db.String(100), nullable=False)
    center_name = db.Column(db.String(250), nullable=False)
    status = db.Column(db.String(100), nullable=False)        # Functional / Non-Functional
    governance_type = db.Column(db.String(100), nullable=False) # Govt / Private
    ddo_name = db.Column(db.String(200), nullable=False)
    extra_data = db.Column(db.JSON, default=dict)

# Global tracking array for extra columns
DYNAMIC_COLUMNS = ['S.No.', 'DDO Code', 'Name of Center', 'Functional/Non-Functional', 'Govt/Private', 'DDO Name']

# --- CENTRALIZED HTML INTERFACE BLOCKED AS A STRING ---
DASHBOARD_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Small Industries Wing, Balochistan</title>
    <script src="https://tailwindcss.com"></script>
</head>
<body class="bg-gray-100 text-gray-900 antialiased min-h-screen">

    <!-- Header Panel Banner Branding -->
    <header class="bg-emerald-800 text-white shadow-md border-b-4 border-emerald-950 px-6 py-4 flex flex-col sm:flex-row justify-between items-center gap-4">
        <div>
            <h1 class="text-2xl font-black tracking-wide">Small Industries Wing, Balochistan</h1>
            <p class="text-xs text-emerald-200 font-medium">Government of Balochistan — Admin Access Management Portal</p>
        </div>
        <div class="bg-emerald-900 border border-emerald-700 rounded-full px-4 py-1.5 text-xs font-bold tracking-wider uppercase shadow-inner">
            ⚡ Live Portal
        </div>
    </header>

    <main class="max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
        
        <!-- Table Actions Toolbar -->
        <div class="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6 flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
            <div>
                <h2 class="text-lg font-bold text-gray-900">Training Centers Directory</h2>
                <p class="text-xs text-gray-500">Manage operational parameters and extend table schema.</p>
            </div>
            
            <!-- Dynamic Column Form Extender Input -->
            <form action="/add-column" method="POST" class="w-full md:w-auto flex flex-wrap gap-2">
                <input 
                    type="text" 
                    name="column_name" 
                    placeholder="Extra Column Name..." 
                    required 
                    class="flex-1 md:w-64 border border-gray-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-600 focus:outline-none"
                />
                <button type="submit" class="bg-emerald-700 hover:bg-emerald-800 text-white font-bold text-sm px-5 py-2.5 rounded-lg tracking-wide transition shadow-sm">
                    + Add Column
                </button>
            </form>
        </div>

        <!-- Dynamic Registry Data Table View Grid -->
        <div class="bg-white rounded-xl shadow-md border border-gray-200 overflow-hidden mb-8">
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200 text-left text-sm">
                    <thead class="bg-gray-50 text-gray-700 font-bold uppercase tracking-wider text-xs border-b">
                        <tr>
                            {% for col in columns %}
                            <th class="px-6 py-4 border-r last:border-r-0 border-gray-200 bg-gray-50 font-semibold">{{ col }}</th>
                            {% endfor %}
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-gray-200 bg-white">
                        {% for center in centers %}
                        <tr class="hover:bg-slate-50 transition-colors">
                            <td class="px-6 py-4 whitespace-nowrap font-bold text-gray-600 bg-gray-50/50">{{ center.s_no }}</td>
                            <td class="px-6 py-4 whitespace-nowrap font-mono font-medium text-emerald-800">{{ center.ddo_code }}</td>
                            <td class="px-6 py-4 whitespace-nowrap font-bold text-gray-900">{{ center.center_name }}</td>
                            <td class="px-6 py-4 whitespace-nowrap">
                                <span class="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wide 
                                    {{ 'bg-green-100 text-green-800 border border-green-200' if center.status == 'Functional' else 'bg-red-100 text-red-800 border border-red-200' }}">
                                    {{ center.status }}
                                </span>
                            </td>
                            <td class="px-6 py-4 whitespace-nowrap"><span class="font-medium">{{ center.governance_type }}</span></td>
                            <td class="px-6 py-4 whitespace-nowrap text-gray-700">{{ center.ddo_name }}</td>
                            
                            <!-- Custom Extra Column Value Direct Mapper Loop -->
                            {% for col in columns[6:] %}
                            <td class="px-6 py-4 whitespace-nowrap text-gray-600 bg-amber-50/20 italic">
                                {{ center.extra_data.get(col, '—') }}
                            </td>
                            {% endfor %}
                        </tr>
                        {% else %}
                        <tr>
                            <td colspan="{{ columns|length }}" class="px-6 py-16 text-center text-gray-400 font-medium italic">
                                No centers registered inside this portal workspace yet.
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- Dynamic Entry Creation Form Processing Panel -->
        <div class="bg-white p-6 rounded-xl shadow-md border border-gray-200">
            <h3 class="text-base font-bold uppercase tracking-wider text-gray-900 mb-4 border-b pb-2 border-gray-100">Add New Center File Entry</h3>
            
            <form action="/add-center" method="POST" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
                <div class="flex flex-col">
                    <label class="text-xs font-bold uppercase text-gray-600 mb-1.5 tracking-wide">DDO Code</label>
                    <input type="text" name="ddo_code" required class="border border-gray-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-600 focus:outline-none bg-gray-50/50">
                </div>
                
                <div class="flex flex-col">
                    <label class="text-xs font-bold uppercase text-gray-600 mb-1.5 tracking-wide">Name of Center</label>
                    <input type="text" name="center_name" required class="border border-gray-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-600 focus:outline-none bg-gray-50/50">
                </div>

                <div class="flex flex-col">
                    <label class="text-xs font-bold uppercase text-gray-600 mb-1.5 tracking-wide">Functional / Non-Functional</label>
                    <select name="status" required class="border border-gray-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-600 focus:outline-none bg-white">
                        <option value="Functional">Functional</option>
                        <option value="Non-Functional">Non-Functional</option>
                    </select>
                </div>

                <div class="flex flex-col">
                    <label class="text-xs font-bold uppercase text-gray-600 mb-1.5 tracking-wide">Govt / Private</label>
                    <select name="governance_type" required class="border border-gray-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-600 focus:outline-none bg-white">
                        <option value="Govt">Govt</option>
                        <option value="Private">Private</option>
                    </select>
                </div>

                <div class="flex flex-col">
                    <label class="text-xs font-bold uppercase text-gray-600 mb-1.5 tracking-wide">DDO Name</label>
                    <input type="text" name="ddo_name" required class="border border-gray-300 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-emerald-600 focus:outline-none bg-gray-50/50">
                </div>

                <!-- Custom User Row Element Appender Interfacing Fields -->
                {% for col in columns[6:] %}
                <div class="flex flex-col bg-amber-50/40 p-2.5 rounded-lg border border-dashed border-amber-200">
                    <label class="text-xs font-bold uppercase text-amber-900 mb-1.5 tracking-wide">{{ col }} (Custom)</label>
                    <input type="text" name="extra_{{ col.lower().replace(' ', '_') }}" class="border border-amber-200 rounded-lg p-2.5 text-sm focus:ring-2 focus:ring-amber-500 focus:outline-none bg-white">
                </div>
                {% endfor %}

