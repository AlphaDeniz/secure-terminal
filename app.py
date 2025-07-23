from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os, json, random

app = Flask(__name__)
app.secret_key = os.urandom(24)

# ========== CONFIG ==========
PASSWORD = "admin123"  # Change this as needed
PASSWORD_HASH = generate_password_hash(PASSWORD)

MEMORY_FILE = "machine_memory.json"

CLASSIFICATIONS = ["MONITORED", "IRRELEVANT THREAT", "RELEVANT THREAT"]
CITIES = ["New York", "Los Angeles", "Chicago", "London"]
ASSOCIATES = ["Unknown", "Flagged", "Former Asset", "Civilian"]

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print("Error loading memory:", e)
        return {}

def save_memory(data):
    with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def generate_profile():
    return {
        "name": f"Subject {random.randint(1000,9999)}",
        "age": random.randint(20, 70),
        "city": random.choice(CITIES),
        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "associate": random.choice(ASSOCIATES)
    }

def generate_classification(profile):
    score = 0
    if profile['age'] < 30:
        score += 2
    if profile['city'] == "Chicago":
        score += 2
    if profile['associate'] == "Flagged":
        score += 4
    elif profile['associate'] == "Former Asset":
        score += 3

    if score >= 6:
        return "RELEVANT THREAT"
    elif 3 <= score < 6:
        return "IRRELEVANT THREAT"
    else:
        return "MONITORED"

@app.route('/')
def index():
    return redirect(url_for('boot'))

@app.route('/boot')
def boot():
    return render_template("boot.html")

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    memory = load_memory()
    if request.method == 'POST':
        ssn = request.form['ssn'].strip()
        if ssn and ssn not in memory:
            profile = generate_profile()
            classification = generate_classification(profile)
            memory[ssn] = {
                "classification": classification,
                "profile": profile,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            save_memory(memory)
        return redirect(url_for('dashboard'))
    return render_template("dashboard.html", memory=memory)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if check_password_hash(PASSWORD_HASH, request.form['password']):
            session['logged_in'] = True
            return redirect(url_for('admin'))
    return render_template("login.html")

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get("logged_in"):
        return redirect(url_for("login"))
    memory = load_memory()
    if request.method == 'POST':
        ssn = request.form['ssn']
        classification = request.form['classification']
        if ssn in memory:
            memory[ssn]['classification'] = classification
            save_memory(memory)
        return redirect(url_for('admin'))
    return render_template("admin.html", memory=memory, classifications=CLASSIFICATIONS)

if __name__ == '__main__':
    app.run(debug=True)
