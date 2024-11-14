from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate
from voice_modulator import VoiceModulator
import random


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employee.db'
app.secret_key = 'my_secret_key'

# initialize the database connection
db = SQLAlchemy(app)
migrate = Migrate(app,db)

# create db model
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), nullable=False, unique=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    phone_number = db.Column(db.String(15), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        employee = Employee.query.filter_by(email=email, password=password).first()
        if employee:
            session['name'] = employee.username
            session['email'] = employee.email
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.')
            return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('name', None)
    return redirect(url_for('login'))

@app.route('/signup')
def signup():
    return render_template('signup.html')

@app.route('/submit', methods=['POST'])
def submit():
    email = request.form.get('email')
    name = request.form.get('name') 
    password = request.form.get('password')
    employee = Employee.query.filter_by(email=email, password=password).first()
    if employee:
        session['name'] = employee.full_name
        session['email'] = employee.email
        session['password'] = employee.password
        return redirect(url_for('dashboard'))
    else:
         flash('Account doesnt exist or username/password incorrect')
         return render_template('login.html')
    
    
@app.route('/profiles')
def index():
    profiles = Employee.query.all()
    return render_template('profiles.html', profiles=profiles)

@app.route('/signup2', methods=['POST'])
def signup2():
    full_name = request.form.get('full_name')
    username = request.form.get('username')
    email = request.form.get('email')
    phone_number = request.form.get('phone_number')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if password != confirm_password:
        flash("Passwords do not match.")
        return redirect(url_for('signup'))

    existing_employee = Employee.query.filter((Employee.email == email) | (Employee.username == username)).first()
    if existing_employee:
        flash('Username or email already exists. Please login.')
        return redirect(url_for('signup'))

    # store data into database
    profile = Employee(
        full_name=full_name,
        username=username,
        email=email,
        phone_number=phone_number,
        password=password  # Consider hashing the password for security
    )
    db.session.add(profile)
    db.session.commit()

    session['name'] = profile.full_name
    session['username'] = profile.username
    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard')

# Initialize the voice modulator instance
voice_modulator = VoiceModulator()

@app.route('/modulator/control', methods=['POST'])
def modulator_control():
    data = request.get_json()
    action = data.get("action")
    
    if action == "start":
        voice_modulator.start()
    elif action == "stop":
        voice_modulator.stop()
    else:
        # Adjust effects based on received data
        voice_modulator.pitch_shift = float(data.get("pitch", 1.0))
        voice_modulator.reverb = float(data.get("reverb", 0.0))
        voice_modulator.distortion = float(data.get("distortion", 0.0))
        voice_modulator.voice_type = data.get("voice", "normal")
        voice_modulator.is_encrypted = data.get("encrypt", "off") == "on"

    return jsonify({"message": "Voice modulator settings updated successfully"})

    
if __name__ == '__main__':
    app.run(debug=True)