#!/usr/bin/env python

import os
import time
from flask import Flask, abort, request, jsonify, g, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from sqlalchemy import inspect
from waitress import serve
import bcrypt
import re
from datetime import datetime
from flask_cors import CORS

# initialization
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost:3306/backend'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# extensions
db = SQLAlchemy(app)
auth = HTTPBasicAuth()

def hash_password(password):
    # Generate a salt and hash the password
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')
def check_password(plain_password, hashed_password):
    # Check if the plain text password matches the hashed password
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

placeholder_data = {
    "water": {
        "rainfall": 0.5,  # Placeholder value for rainfall sensor (in inches)
        "humidity": 45,   # Placeholder value for humidity sensor (in percentage)
        "soil_moisture": 60,  # Placeholder value for soil moisture sensor (in percentage)
        "pump_status": 0,  # Placeholder value for pump status
        "temperature": 25  # Placeholder value for temperature sensor (in Celsius)
    },
    "fert": {
        "soil_moisture": 55,  # Placeholder value for soil moisture sensor (in percentage)
        "ph": 6.5,  # Placeholder value for pH sensor
        "humidity": 50  # Placeholder value for humidity sensor (in percentage)
    },
    "electricity": {
        "temperature": 27,  # Placeholder value for temperature sensor (in Celsius)
        "light": 400,  # Placeholder value for light sensor (in lux)
        "conductivity": 300  # Placeholder value for conductivity sensor (in microsiemens per centimeter)
    }
}

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
class Sensor(db.Model):
    __tablename__ = 'sensors'

    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    sensor_name = db.Column(db.String(50), nullable=False)
    data = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __init__(self, category, sensor_name, data):
        self.category = category
        self.sensor_name = sensor_name
        self.data = data

    def __repr__(self):
        return f"<Sensor(category='{self.category}', sensor_name='{self.sensor_name}', data={self.data}, timestamp={self.timestamp})>"
@app.route('/')
def welcome():
    return "Hello world!"

@app.route('/api/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.json.get('email') 
        password = request.json.get('password')

        # Query the database for a user with either the given email or username
        user = User.query.filter((User.email == email)).first()
        if user:
            if check_password(password, user.password):
                return jsonify({'success': True}), 200
            else:
                return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route("/api/<category>")
def get_sensor_data(category):
    if category not in placeholder_data:
        return jsonify({"error": "Category not found"}), 404

    return jsonify(placeholder_data[category])

# POST route for controlling sensor data
@app.route("/apt/control/<sensor_name>/<sensor_data>", methods=["POST"])
def control_sensor_data(sensor_name, sensor_data):
    # Check if the sensor name exists in the placeholder data
    if sensor_name in placeholder_data:
        # Update the sensor data with the provided value
        placeholder_data[sensor_name] = float(sensor_data)
        return jsonify({"message": f"Sensor {sensor_name} data updated successfully."}), 200
    else:
        return jsonify({"error": f"Sensor {sensor_name} not found."}), 404
@app.route('/api/adduser', methods=['POST'])
def new_user():
    password = request.json.get('password')
    email = request.json.get('email')
    first_name = request.json.get('first_name')
    last_name = request.json.get('last_name')

    errors = []

    if password is None:
        errors.append("Password is missing")
    elif len(password) < 8:
        errors.append("Password should have at least 8 characters")
    elif not re.search("[A-Z]", password):
        errors.append("Password should contain at least one capital letter")
    if email is None:
        errors.append("Email is missing")
    if first_name is None:
        errors.append("First name is missing")
    if last_name is None:
        errors.append("Last name is missing")

    if errors:
        return jsonify({'success': False, 'errors': errors}), 400

    if User.query.filter_by(email=email).first() is not None:
        errors.append("email already exists")

    if errors:
        print(errors)
        return jsonify({'success': False, 'errors': errors}), 400

    # Hash the password before storing it
    hashed_password = hash_password(password)

    # Create a new User object with the hashed password
    new_user = User(password=hashed_password, email=email, first_name=first_name, last_name=last_name)

    # Add the new user to the session and commit changes to the database
    db.session.add(new_user)
    db.session.commit()

    # Return a response indicating success
    return (jsonify({'success':True}), 201)

@app.route('/api/users/<int:id>')
def get_user(id):
    user = User.query.get(id)
    if not user:
        abort(400)
    return jsonify({'username': user.username})

@app.route('/api/dashboard')
@auth.login_required
def get_resource():
    return jsonify({'data': 'Hello, %s!' % g.user.username})

if __name__ == '__main__':
    with app.app_context():
        # Inspect the database
        inspector = inspect(db.engine)

        # Check if the User table (or any other tables) exists
        if not inspector.has_table('user'):
            # Create all tables if the User table doesn't exist
            db.create_all()
    serve(app, host='0.0.0.0', port=5000)