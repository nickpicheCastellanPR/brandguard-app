import sqlite3
import hashlib
import os

# --- RAILWAY PERSISTENCE SETUP ---
if os.environ.get("RAILWAY_ENVIRONMENT"):
    DB_FOLDER = "/app/data"
else:
    DB_FOLDER = "."

os.makedirs(DB_FOLDER, exist_ok=True)
DB_NAME = os.path.join(DB_FOLDER, "signet.db")
# ---------------------------------

def init_db():
    """Initializes the database with Users and Profiles tables."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Create Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    
    # 2. Create Profiles Table (The missing piece!)
    c.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def create_user(username, password):
    """Creates a new user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    """Checks if username/password match (Renamed to match your app)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_pw))
    data = c.fetchall()
    conn.close()
    return len(data) > 0

# --- NEW FUNCTIONS FOR PROFILES ---

def create_profile(username, profile_name):
    """Saves a new profile for a specific user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Check if profile already exists for this user to avoid duplicates
    c.execute('SELECT * FROM profiles WHERE username = ? AND name = ?', (username, profile_name))
    if c.fetchone():
        conn.close()
        return False # Profile exists
        
    c.execute('INSERT INTO profiles (username, name) VALUES (?, ?)', (username, profile_name))
    conn.commit()
    conn.close()
    return True

def get_profiles(username):
    """Returns a list of profile names for the user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT name FROM profiles WHERE username = ?', (username,))
    data = c.fetchall()
    conn.close()
    # Convert list of tuples [('Brand A',), ('Brand B',)] into a simple list ['Brand A', 'Brand B']
    return [item[0] for item in data]

def delete_profile(username, profile_name):
    """Deletes a profile."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM profiles WHERE username = ? AND name = ?', (username, profile_name))
    conn.commit()
    conn.close()
