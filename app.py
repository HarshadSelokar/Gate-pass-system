from flask import Flask, render_template, request, jsonify, send_file, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import qrcode
import os

from utils.crypto_utils import encrypt_uid, decrypt_uid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///gatepass.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# =======================[ Models ]=======================
class Student(db.Model):
    uid = db.Column(db.String(20), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    year = db.Column(db.String(20), nullable=False)
    branch = db.Column(db.String(50), nullable=False)

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    uid = db.Column(db.String(20), db.ForeignKey('student.uid'), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# =======================[ Utility ]=======================
def cleanup_old_logs():
    cutoff = datetime.utcnow() - timedelta(days=3)
    Log.query.filter(Log.timestamp < cutoff).delete()
    db.session.commit()

def get_active_entries():
    entries_today = db.session.query(Log.uid).filter(
        Log.status == 'IN',
        Log.timestamp >= datetime.utcnow().date()
    ).all()
    exited_today = db.session.query(Log.uid).filter(
        Log.status == 'OUT',
        Log.timestamp >= datetime.utcnow().date()
    ).all()
    active = set(uid for (uid,) in entries_today) - set(uid for (uid,) in exited_today)
    return Student.query.filter(Student.uid.in_(active)).all()

# =======================[ Routes ]=======================
@app.route('/')
def landing():
    return redirect('/scan')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        uid = request.form['uid']
        name = request.form['name']
        year = request.form['year']
        branch = request.form['branch']

        if not Student.query.get(uid):
            student = Student(uid=uid, name=name, year=year, branch=branch)
            db.session.add(student)
            db.session.commit()

            encrypted_uid = encrypt_uid(uid)
            qr_img = qrcode.make(encrypted_uid)
            os.makedirs('qr_codes', exist_ok=True)
            qr_path = f'qr_codes/{uid}.png'
            qr_img.save(qr_path)
            return send_file(qr_path, as_attachment=True)
        else:
            return "Student already exists", 400

    return render_template('register.html')

@app.route('/scan')
def scan():
    return render_template('scan.html')

@app.route('/log_entry', methods=['POST'])
def log_entry():
    data = request.get_json()
    try:
        encrypted_uid = data['uid']
        status = data['status']
        uid = decrypt_uid(encrypted_uid)
    except Exception as e:
        return jsonify({"status": "error", "message": "Decryption failed or invalid UID"}), 400

    student = Student.query.get(uid)
    if not student:
        return jsonify({"status": "error", "message": "Student not found"}), 404

    new_log = Log(uid=uid, status=status)
    db.session.add(new_log)
    db.session.commit()
    return jsonify({"status": "success", "message": f"{status} logged for UID: {uid}."})

@app.route('/admin')
def admin():
    cleanup_old_logs()
    today = datetime.utcnow().date()
    date_options = [(today - timedelta(days=i)) for i in range(3)]
    return render_template('admin_panel.html', dates=date_options)

@app.route('/logs/<date_str>')
def logs_by_date(date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d")
    next_day = date + timedelta(days=1)
    logs = Log.query.filter(Log.timestamp >= date, Log.timestamp < next_day).all()

    entry_exit_map = {}
    for log in logs:
        if log.uid not in entry_exit_map:
            entry_exit_map[log.uid] = {'in': None, 'out': None, 'name': Student.query.get(log.uid).name}
        if log.status == 'IN':
            entry_exit_map[log.uid]['in'] = log.timestamp
        elif log.status == 'OUT':
            entry_exit_map[log.uid]['out'] = log.timestamp

    return render_template('logs_by_date.html', date=date_str, data=entry_exit_map)

@app.route('/live_entries')
def live_entries():
    entries = get_active_entries()
    return render_template('live_entries.html', students=entries)

if __name__ == '__main__':
    os.makedirs('qr_codes', exist_ok=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)