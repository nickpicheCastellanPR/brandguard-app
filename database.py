import sqlite3
import hashlib
import os

# --- RAILWAY PERSISTENCE SETUP ---
if os.environ.get("RAILWAY_ENVIRONMENT"):
    DB_FOLDER = "/app/data"
else:
    DB_FOLDER = "."  # Local testing

os.makedirs(DB_FOLDER, exist_ok=True)
DB_NAME = os.path.join(DB_FOLDER, "signet.db")
# ---------------------------------

def init_db():
    """Initializes the database with a Users table."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Create Users table if it doesn't exist
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    conn.commit()
    conn.close()

def create_user(username, password):
    """Creates a new user with a hashed password."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Hash the password for security
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists
    finally:
        conn.close()

def verify_user(username, password):
    """Checks if username/password match."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_pw))
    data = c.fetchall()
    conn.close()
    
    return len(data) > 0
