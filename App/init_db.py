import sqlite3

# Make sure the current folder (App/) has the database
db_path = 'medbot.db'  # Since it's now in the same folder

# Create (connect to) the database
conn = sqlite3.connect(db_path)

# Create tables if they don't exist
conn.execute('''
CREATE TABLE IF NOT EXISTS medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    name TEXT,
    dosage TEXT,
    frequency TEXT,
    start_date TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

conn.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,  -- Fixed column name to 'id'
    username TEXT UNIQUE NOT NULL,         -- Username for login
    password_hash TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    phone_number TEXT,
    role TEXT NOT NULL,                   -- Changed ENUM to TEXT
    license_id TEXT,
    dob TEXT
)
''')

conn.execute('''
CREATE TABLE IF NOT EXISTS patient_providers (
    patient_id INTEGER,
    provider_id INTEGER,
    PRIMARY KEY (patient_id, provider_id),
    FOREIGN KEY (patient_id) REFERENCES users(id),
    FOREIGN KEY (provider_id) REFERENCES users(id)
)
''')

conn.execute('''
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    alert_text TEXT,
    seen BOOLEAN DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id)
)
''')

conn.commit()
conn.close()

print("Database initialized: medbot.db with updated users table")
