import sqlite3
import os

def get_connection():
    # Use a test database if running tests
    if os.getenv("TESTING") == "true":
        return sqlite3.connect("data/test_concept_cruncher.db")
    return sqlite3.connect("data/concept_cruncher.db")

def register_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('INSERT INTO users (username, password, progress) VALUES (?, ?, ?)', (username, password, "{}"))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password))
    user = c.fetchone()
    conn.close()
    return user is not None

def get_user_id(username):
    """Fetch the user_id for a given username."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return user[0] if user else None

def initialize_database():
    """Initialize the database with required tables."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        progress TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS summaries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        chat_id INTEGER NOT NULL,
        summary TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    """)
    conn.commit()
    conn.close()

initialize_database()  # Call this function to ensure the database is initialized

