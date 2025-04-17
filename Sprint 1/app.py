from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key'

def get_user(username):
    conn = sqlite3.connect('database/medbot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)
        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['role'] = user[3]
            if user[3] == 'provider':
                return redirect('/provider_dashboard')
            elif user[3] == 'patient':
                return redirect('/patient_dashboard')
        else:
            error = "Invalid username or password"
    return render_template('login.html', error=error)


@app.route('/provider_dashboard')
def provider_dashboard():
    return "<h2>Welcome, Provider!</h2>"

@app.route('/patient_dashboard')
def patient_dashboard():
    return "<h2>Welcome, Patient!</h2>"

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    return "<h2>Registration page coming soon!</h2>"


if __name__ == '__main__':
    app.run(debug=True)
