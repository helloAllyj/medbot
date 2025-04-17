import sqlite3
import os

os.makedirs('database', exist_ok=True)
conn = sqlite3.connect(os.path.join('database', 'medbot.db'))

conn.execute('''
CREATE TABLE IF NOT EXISTS medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
''')

conn.commit()
conn.close()
print("Database initialized.")