from flask import Flask, render_template, request
import json
import os
import random
from datetime import datetime
import re

app = Flask(__name__)

DATA_FILE = "machine_memory.json"
SECRET_KEY = b"MySecretKey123"  # Change this to your secret key!
LABELS = ["threat", "irrelevant", "under surveillance", "asset", "missing", "target neutralized"]
SSN_PATTERN = re.compile(r"^\d{3}-\d{2}-\d{4}$")


def xor_encrypt_decrypt(data: bytes, key: bytes) -> bytes:
    return bytes([b ^ key[i % len(key)] for i, b in enumerate(data)])


def save_memory(memory):
    data = json.dumps(memory, indent=2).encode()
    encrypted = xor_encrypt_decrypt(data, SECRET_KEY)
    with open(DATA_FILE, "wb") as f:
        f.write(encrypted)


def load_memory():
    if os.path.exists(DATA_FILE):
        if os.path.getsize(DATA_FILE) == 0:
            return {}
        with open(DATA_FILE, "rb") as f:
            encrypted = f.read()
        decrypted = xor_encrypt_decrypt(encrypted, SECRET_KEY)
        try:
            return json.loads(decrypted.decode())
        except Exception as e:
            print("Failed to load or parse data:", e)
            return {}
    else:
        return {}


memory = load_memory()


def is_valid_ssn(ssn):
    if not SSN_PATTERN.match(ssn):
        return False

    area, group, serial = ssn.split('-')

    # Invalid area numbers
    if area == "000" or area == "666" or (900 <= int(area) <= 999):
        return False
    # Invalid group number
    if group == "00":
        return False
    # Invalid serial number
    if serial == "0000":
        return False
    # Reject all zeros SSN
    if ssn == "000-00-0000":
        return False

    return True


def classify_ssn(ssn):
    if ssn in memory:
        return memory[ssn]
    else:
        label = random.choice(LABELS)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        memory[ssn] = {"label": label, "timestamp": timestamp}
        save_memory(memory)
        return memory[ssn]


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None

    if request.method == "POST":
        ssn = request.form.get("ssn", "").strip()
        if is_valid_ssn(ssn):
            result = classify_ssn(ssn)
            result["ssn"] = ssn
        else:
            error = "Invalid SSN format or invalid number. Use format XXX-XX-XXXX with valid values."

    return render_template("index.html", result=result, error=error)


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", memory=memory)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000)

