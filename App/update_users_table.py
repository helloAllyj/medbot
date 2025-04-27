import sqlite3

conn = sqlite3.connect('database/medbot.db')
cursor = conn.cursor()

try:
    cursor.execute("ALTER TABLE users ADD COLUMN first_name TEXT")
except sqlite3.OperationalError:
    print("'first_name' already exists.")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN last_name TEXT")
except sqlite3.OperationalError:
    print("'last_name' already exists.")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN dob TEXT")
except sqlite3.OperationalError:
    print("'dob' already exists.")

try:
    cursor.execute("ALTER TABLE users ADD COLUMN license_id TEXT")
except sqlite3.OperationalError:
    print("'license_id' already exists.")

conn.commit()
conn.close()

print("Users table updated with license_id")


