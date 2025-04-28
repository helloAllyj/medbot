import sqlite3
import os

os.makedirs('database', exist_ok=True)

db_path = os.path.join('database', 'medbot.db')
conn = sqlite3.connect(db_path)


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
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    dob TEXT,
    license_id TEXT,
    phone_number TEXT
)
''')

conn.commit()
conn.close()

print("Database initialized: medbot.db with updated users table")
