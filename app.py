from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

import pytz  # Importing pytz for timezone handling

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///D:/my_coding_projects_(raw)/project_p/Gate_pass_project (Modification)/instance/gatepasses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Define your local timezone
local_tz = pytz.timezone('Asia/Kolkata')  #tag for timezone and local host set

# Model for the Gate Pass
class GatePass(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    entry_time = db.Column(db.DateTime, default=None, nullable=True)
    exit_time = db.Column(db.DateTime, default=None, nullable=True)

# Route to the home page
@app.route('/')
def home():
    return render_template('index.html')

# Route to add a new gate pass manually
@app.route('/add', methods=['GET', 'POST'])
def add_gate_pass():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']

        # Create and save the new gate pass to the database
        new_gate_pass = GatePass(student_id=student_id, name=name)
        db.session.add(new_gate_pass)
        db.session.commit()

        return redirect(url_for('view_entries'))

    return render_template('add_gate_pass.html')

# Route to mark entry or exit based on student_id from URL
@app.route('/mark_entry_exit/<student_id>', methods=['POST'])
def mark_entry_exit_by_id(student_id):
    gatepass = GatePass.query.filter_by(student_id=student_id).first()
    if not gatepass:
        return f"No gate pass found for Student ID: {student_id}"

    if gatepass.entry_time is None:
        gatepass.entry_time = datetime.now(local_tz)  # Using local time
    elif gatepass.exit_time is None:
        gatepass.exit_time = datetime.now(local_tz)  # Using local time
    else:
        return f"Both entry and exit times are already marked for Student ID: {student_id}"

    db.session.commit()
    return redirect(url_for('view_entries'))

# Route to mark entry or exit via a form submission
@app.route('/mark_entry_exit', methods=['GET', 'POST'])
def mark_entry_exit():
    if request.method == 'POST':
        student_id = request.form['student_id']
        gatepass = GatePass.query.filter_by(student_id=student_id).first()

        if not gatepass:
            return f"No gate pass found for Student ID: {student_id}"

        if gatepass.entry_time is None:
            gatepass.entry_time = datetime.now(local_tz)  # Using local time
        elif gatepass.exit_time is None:
            gatepass.exit_time = datetime.now(local_tz)  # Using local time
        else:
            return f"Both entry and exit times are already marked for Student ID: {student_id}"

        db.session.commit()
        return redirect(url_for('view_entries'))

    return render_template('mark_entry_exit.html')

# Route to view all entries
@app.route('/entries')
def view_entries():
    entries = GatePass.query.all()
    for entry in entries:
        if entry.entry_time:
            entry.entry_time = entry.entry_time.astimezone(local_tz).strftime("%H-%M-%S %d-%m-%Y")  # Format entry time
        if entry.exit_time:
            entry.exit_time = entry.exit_time.astimezone(local_tz).strftime("%H-%M-%S %d-%m-%Y")  # Format exit time

    return render_template('entries.html', entries=entries)

# Initialize database tables
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
