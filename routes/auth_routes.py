from flask import Blueprint, render_template, request, redirect, url_for, session

auth_routes = Blueprint('auth_routes', __name__)

# Dummy user database (Replace with actual DB logic)
users = {"admin": "password123"}

@auth_routes.route('/')
def home():
    return render_template("home.html")

@auth_routes.route('/auth')
def auth():
    return render_template("auth.html")

@auth_routes.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username in users and users[username] == password:
        session['user'] = username  # Store user session
        return redirect(url_for('auth_routes.index'))  # Redirect to the index route in auth_routes
    return "Invalid credentials. Try again."

@auth_routes.route('/signup')
def signup():
    return "Signup Page (Functionality to be added later)"

@auth_routes.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('auth_routes.home'))

@auth_routes.route('/index')
def index():
    if 'user' not in session:
        return redirect(url_for('auth_routes.auth'))  # Redirect unauthorized users to login
    return render_template("index.html")