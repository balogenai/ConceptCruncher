import sqlite3
import os

os.makedirs("data", exist_ok=True)
conn = sqlite3.connect("data/concept_cruncher.db")
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    progress TEXT
)
''')
conn.commit()
conn.close()
print("Database initialized.")
