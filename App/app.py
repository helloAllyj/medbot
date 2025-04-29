from flask import Flask, render_template, request, redirect, session, url_for, jsonify
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import requests


app = Flask(__name__)
app.secret_key = 'your-secret-key'

def get_user(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, password_hash, role, first_name, last_name, dob, license_id, phone_number FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_db_connection():
    conn = sqlite3.connect('medbot.db')
    conn.row_factory = sqlite3.Row  # Allows column access by name
    return conn

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = get_user(username)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['first_name'] = user['first_name']
            session['last_name'] = user['last_name']
            if user['role'] == 'provider':
                return redirect('/provider_dashboard')
            elif user['role'] == 'patient':
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
        password_hash = request.form['password_hash']
        phone_number = request.form['phone_number']
        
        if not username or not password_hash or not role or not first_name or not last_name:
            error = "All fields are required."
        elif len(password_hash) > 20:
            error = "Password must be less than 20 characters."
        elif role == 'provider' and not license_id:
            error = "License ID is required for providers."
        else:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
            existing_user = cursor.fetchone()

            if existing_user:
                error = "Username already exists."
            else:
                password_hash = generate_password_hash(password_hash)

                cursor.execute(""" 
                    INSERT INTO users (username, password_hash, role, first_name, last_name, dob, license_id, phone_number)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (username, password_hash, role, first_name, last_name, dob, license_id, phone_number))
                
                conn.commit()
                conn.close()
                return redirect(url_for('login'))

            conn.close()

    return render_template('register.html', error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route('/medications', methods=['GET', 'POST'])
def medications():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        name = request.form['name']
        dosage = request.form['dosage']
        frequency = request.form['frequency']
        start_date = request.form['start_date']

        cursor.execute('''INSERT INTO medications (user_id, name, dosage, frequency, start_date) 
                          VALUES (?, ?, ?, ?, ?)''', 
                       (user_id, name, dosage, frequency, start_date))
        conn.commit()

    cursor.execute('''SELECT id, name, dosage, frequency, start_date 
                      FROM medications WHERE user_id = ?''', (user_id,))
    medications = cursor.fetchall()
    conn.close()

    return render_template('medications.html', medications=medications)


@app.route('/delete_medication/<int:med_id>', methods=['POST'])
def delete_medication(med_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    # First get the medication name before deleting it
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM medications WHERE id = ? AND user_id = ?', (med_id, user_id))
    med = cursor.fetchone()

    if med:
        med_name = med['name']

        # Delete the medication
        cursor.execute('DELETE FROM medications WHERE id = ? AND user_id = ?', (med_id, user_id))
        conn.commit()

        # Delete any alerts that mention this medication
        cursor.execute('DELETE FROM alerts WHERE user_id = ? AND alert_text LIKE ?', 
                       (user_id, f"%{med_name}%"))
        conn.commit()

    conn.close()

    return redirect(url_for('medications'))


@app.route('/suggest_medication')
def suggest_medication():
    query = request.args.get('query')
    if not query:
        return jsonify([])

    try:
        url = f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:{query}*&limit=10"
        response = requests.get(url)
        data = response.json()

        suggestions = []
        for item in data.get('results', []):
            names = item.get('openfda', {}).get('brand_name', [])
            suggestions.extend(names)

        suggestions = list(set(suggestions))  # Remove duplicates
        return jsonify(suggestions[:10])

    except Exception as e:
        print("OpenFDA API Error:", e)
        return jsonify([]) 


@app.route('/add_medication', methods=['GET', 'POST'])
def add_medication():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        dosage = request.form['dosage']
        frequency = request.form['frequency']
        start_date = request.form['start_date']

        user_id = session['user_id']

        conn = get_db_connection()
        cursor = conn.cursor()

        # Insert the new medication
        cursor.execute('''INSERT INTO medications (user_id, name, dosage, frequency, start_date) 
                          VALUES (?, ?, ?, ?, ?)''', 
                       (user_id, name, dosage, frequency, start_date))
        conn.commit()

        # Fetch all medications again
        cursor.execute('SELECT name FROM medications WHERE user_id = ?', (user_id,))
        medications = [row['name'] for row in cursor.fetchall()]
        conn.close()

        alerts_to_add = []
        for i in range(len(medications)):
            for j in range(i + 1, len(medications)):
                med1, med2 = medications[i], medications[j]
                interaction = check_interaction(med1, med2)
                if interaction:
                    alert_text = f"Conflict between {med1} and {med2}: {interaction}"
                    alerts_to_add.append(alert_text)

        conn = get_db_connection()
        cursor = conn.cursor()
        for alert_text in set(alerts_to_add):
            cursor.execute('SELECT 1 FROM alerts WHERE user_id = ? AND alert_text = ?', (user_id, alert_text))
            if not cursor.fetchone():
                cursor.execute('INSERT INTO alerts (user_id, alert_text) VALUES (?, ?)', (user_id, alert_text))
        conn.commit()
        conn.close()

        return redirect(url_for('medications'))

    return render_template('add_medication.html')

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        new_first = request.form['first_name']
        new_last = request.form['last_name']
        new_phone = request.form['phone']

        cursor.execute("""
            UPDATE users
            SET first_name = ?, last_name = ?, phone_number = ?
            WHERE id = ?
        """, (new_first, new_last, new_phone, user_id))
        conn.commit()

        # Update session data too
        session['first_name'] = new_first
        session['last_name'] = new_last

        conn.close()
        return redirect(url_for('patient_dashboard'))

    # GET request: fetch existing user data
    cursor.execute("SELECT first_name, last_name, phone_number FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()

    if user:
        user_data = {
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'phone': user['phone_number']
        }
        return render_template('edit_profile.html', user=user_data)
    else:
        return redirect(url_for('login'))
    
import requests
def check_interaction(med1, med2):
    try:
        # Helper function to query OpenFDA and find interaction text
        def query_fda(med):
            url = f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:\"{med}\"&limit=1"
            response = requests.get(url)
            data = response.json()
            results = data.get('results', [])
            if results:
                return results[0].get('drug_interactions', [])
            return []

        # Check if med2 appears in med1's drug_interactions
        interactions1 = query_fda(med1)
        if interactions1:
            combined_text = ' '.join(interactions1).lower()
            if med2.lower() in combined_text:
                return f"{med1} may interact with {med2}"

        # Also check the reverse: med1 appears in med2's drug_interactions
        interactions2 = query_fda(med2)
        if interactions2:
            combined_text = ' '.join(interactions2).lower()
            if med1.lower() in combined_text:
                return f"{med2} may interact with {med1}"

        return None  # No interaction found

    except Exception as e:
        print(f"Error checking interaction: {e}")
        return None


@app.route('/alerts')
def alerts():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    conn = get_db_connection()
    cursor = conn.cursor()

    # Mark alerts as seen
    cursor.execute('UPDATE alerts SET seen = 1 WHERE user_id = ?', (user_id,))
    conn.commit()

    # Fetch alerts
    cursor.execute('SELECT alert_text FROM alerts WHERE user_id = ?', (user_id,))
    alerts = [ {'alert_text': row[0]} for row in cursor.fetchall() ]  # <<< FIXED HERE
    conn.close()
    return render_template('alerts.html', alerts=alerts)


@app.route('/provider')
def provider():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT id, first_name, last_name FROM users WHERE role = "provider"')
    providers = cursor.fetchall()

    conn.close()
    return render_template('provider.html', providers=providers)

@app.route('/add_provider', methods=['POST'])
def add_provider():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    patient_id = session['user_id']
    data = request.get_json()

    license_id = data.get('license_id')  # <-- use license_id instead

    if not license_id:
        return jsonify({'error': 'License ID is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Find the provider's user ID based on license ID
        cursor.execute('SELECT id FROM users WHERE license_id = ?', (license_id,))
        provider = cursor.fetchone()

        if provider is None:
            return jsonify({'error': 'Provider not found'}), 404

        provider_id = provider['id']  # Now you have the actual provider's user ID

        cursor.execute('''
            INSERT INTO patient_providers (patient_id, provider_id)
            VALUES (?, ?)
        ''', (patient_id, provider_id))

        conn.commit()
        return jsonify({'message': 'Provider added successfully'}), 201

    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


@app.route('/search_provider', methods=['GET'])
def search_provider():
    query = request.args.get('query')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT id, first_name, last_name, license_id
        FROM users
        WHERE (first_name LIKE ? OR last_name LIKE ?) AND role = ?
    ''', (f'%{query}%', f'%{query}%', 'provider'))

    providers = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            'id': provider[0],
            'name': f'{provider[1]} {provider[2]}',
            'license_id': provider[3]  # Now include license_id!
        }
        for provider in providers
    ])
@app.route('/my_providers')
def my_providers():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    patient_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT u.id, u.first_name, u.last_name, u.license_id
        FROM patient_providers pp
        JOIN users u ON pp.provider_id = u.id
        WHERE pp.patient_id = ?
    ''', (patient_id,))

    providers = cursor.fetchall()
    conn.close()

    return jsonify([
        {
            'id': provider[0],   # <--- Return ID too
            'name': f'{provider[1]} {provider[2]}',
            'license_id': provider[3]
        }
        for provider in providers
    ])

from flask import request, jsonify
@app.route('/delete_provider/<int:provider_id>', methods=['POST'])
def delete_provider(provider_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # ONLY delete the patient-provider relationship, NOT the provider user itself
        cursor.execute('''
            DELETE FROM patient_providers 
            WHERE patient_id = ? AND provider_id = ?
        ''', (user_id, provider_id))
        
        conn.commit()
        return jsonify({'message': 'Provider removed successfully.'})  # <-- JSON response
    except Exception as e:
        conn.rollback()
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()


if __name__ == '__main__':
    app.run(debug=True)
