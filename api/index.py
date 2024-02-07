#!/usr/bin/env python

import os
import time
from flask import Flask, abort, request, jsonify, g, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPBasicAuth
from sqlalchemy import inspect
import bcrypt


# initialization
app = Flask(__name__)
app.config['SECRET_KEY'] = 'the quick brown fox jumps over the lazy dog'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://sql8682485:HAGEakjp9M@sql8.freemysqlhosting.net:3306/sql8682485'
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


class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

@app.route('/')
def welcome():
    return "hellow world"

@app.route('/api/login', methods=['POST'])
def login():
    if request.method == 'POST':
        username = request.json.get('username')
        password = request.json.get('password')

        user = User.query.filter_by(username=username).first()
        if user:
            if check_password(password, user.password):
                return jsonify({'success': True}), 200
            else:
                return jsonify({'success': False, 'error': 'Invalid credentials'}), 401
        else:
            return jsonify({'success': False, 'error': 'Invalid credentials'}), 401

@app.route('/api/adduser', methods=['POST'])
def new_user():
    username = request.json.get('username')
    password = request.json.get('password')

    if username is None or password is None:
        abort(400)  # Missing arguments

    if User.query.filter_by(username=username).first() is not None:
        abort(400)  # Existing user

    # Hash the password before storing it
    hashed_password = hash_password(password)

    # Create a new User object with the hashed password
    new_user = User(username=username, password=hashed_password)

    # Add the new user to the session and commit changes to the database
    db.session.add(new_user)
    db.session.commit()

    # Return a response indicating success
    return (jsonify({'username': new_user.username}), 201,
            {'Location': url_for('get_user', id=new_user.id, _external=True)})

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
    app.run(debug=True)