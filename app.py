from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key'

def get_user(username):
    conn = sqlite3.connect('database/medbot.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role, first_name, last_name FROM users WHERE username = ?", (username,))
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
            session['first_name'] = user[4]
            session['last_name'] = user[5]
            if user[3] == 'provider':
                return redirect('/provider_dashboard')
            elif user[3] == 'patient':
                return redirect('/patient_dashboard')
        else:
            error = "Invalid username or password"
    return render_template('login.html', error=error)


@app.route('/provider_dashboard')
def provider_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    full_name = f"{session.get('first_name', '')} {session.get('last_name', '')}"
    return render_template('provider_dashboard.html', full_name=full_name)


@app.route('/patient_dashboard')
def patient_dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    full_name = f"{session.get('first_name', '')} {session.get('last_name', '')}"
    return render_template('patient_dashboard.html', full_name=full_name)



@app.route('/')
def home():
    return render_template('home.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        role = request.form['role']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        dob = request.form['dob'] if role == 'patient' else None
        license_id = request.form['license_id'] if role == 'provider' else None
        username = request.form['username']
        password = request.form['password']
        phone_number = request.form[phone_number]

        if not username or not password or not role or not first_name or not last_name:
            error = "All fields are required."
        elif len(password) > 20:
            error = "Password must be less than 20 characters."
        elif role == 'provider' and not license_id:
            error = "License ID is required for providers."
        else:
            conn = sqlite3.connect('database/medbot.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                error = "Username already exists."
            else:
                password_hash = generate_password_hash(password)

                cursor.execute("""
                    INSERT INTO users (username, password_hash, role, first_name, last_name, dob)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (username, password_hash, role, first_name, last_name, dob))
                
                conn.commit()
                conn.close()
                return redirect(url_for('login'))

            conn.close()

    return render_template('register.html', error=error)


@app.route('/logout')
def logout():
    session.clear()  
    return redirect(url_for('home'))  



if __name__ == '__main__':
    app.run(debug=True)
