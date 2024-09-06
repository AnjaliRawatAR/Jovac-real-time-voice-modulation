from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_migrate import Migrate, migrate
from voice_modulator import voice_modulator
import random


app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///employee.db'
app.secret_key = 'my_secret_key'


# initialize the database connection
db = SQLAlchemy(app)
migrate = Migrate(app,db)

voice_modulator = voice_modulator()

correct_otp = str(random.randint(100000, 999999))

# create db model
class Employee(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login')
def login():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        return redirect(url_for('dashboard'))
    return render_template('Login.html')

@app.route('/voice-modulator')
def voice_modulator():
    return render_template('dashboard.html')


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
        session['name'] = employee.name
        session['email'] = employee.email
        session['password'] = employee.password
        return redirect(url_for('dashboard'))
    else:
         flash('Account doesnt exist or username/password incorrect')
         return render_template('Login.html')
    
    
@app.route('/profiles')
def index():
    profiles = Employee.query.all()
    return render_template('profiles.html', profiles=profiles)

@app.route('/signup2', methods=['POST'])
def signup2():
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')

    existing_employee = Employee.query.filter_by(email=email, password=password).first()
    if existing_employee:
        flash('Email already exists. Please login.')
        return render_template('signup.html')

    # store data into database
    profile = Employee(name=name, email=email,password=password)
    db.session.add(profile)
    db.session.commit()

    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# function to call the voice modulator
@app.route('/modulate', methods=['POST'])
def modulate():
    text = request.form.get('text')
    voice_modulator.modulate(text)
    return jsonify({'message': 'success'})



    
if __name__ == '__main__':
    app.run(debug=True)