from flask import Flask, render_template, request, redirect, jsonify
import qrcode
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
DB_PATH = "database.db"

# QR Code generator
@app.route('/generate_qr', methods=['POST'])
def generate_qr():
    uid = request.form['uid']
    qr = qrcode.make(uid)
    path = f"qr_codes/{uid}.png"
    qr.save(path)
    return jsonify({"status": "success", "path": path})

# Student registration
@app.route('/register', methods=['POST'])
def register_student():
    data = request.form
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO students (uid, name, year, branch) VALUES (?, ?, ?, ?)",
                  (data['uid'], data['name'], data['year'], data['branch']))
        conn.commit()
    return redirect('/')

# QR Scan result handler
@app.route('/log_entry', methods=['POST'])
def log_entry():
    uid = request.json['uid']
    status = request.json['status']
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("INSERT INTO logs (uid, status) VALUES (?, ?)", (uid, status))
        conn.commit()
    return jsonify({"status": "logged"})

# Admin view
@app.route('/logs')
def view_logs():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM logs ORDER BY timestamp DESC")
        logs = c.fetchall()
    return render_template("admin.html", logs=logs)

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        with sqlite3.connect(DB_PATH) as conn:
            conn.executescript(open("schema.sql").read())
    app.run(debug=True)
