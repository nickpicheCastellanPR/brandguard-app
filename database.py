import sqlite3
import hashlib
import json
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
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    
    # 2. Profiles Table (Now with a 'content' column for JSON data)
    c.execute('''
        CREATE TABLE IF NOT EXISTS brand_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            name TEXT,
            content TEXT, 
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def create_user(username, password):
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
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    c.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_pw))
    data = c.fetchall()
    conn.close()
    return len(data) > 0

# --- UPDATED PROFILE FUNCTIONS ---

def create_profile(username, profile_name, profile_data):
    """Saves a profile with its full data (JSON)."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Convert the Python dictionary (profile_data) into a JSON string
    json_content = json.dumps(profile_data)
    
    # Check for duplicates
    c.execute('SELECT * FROM brand_profiles WHERE username = ? AND name = ?', (username, profile_name))
    if c.fetchone():
        # Update existing if found
        c.execute('UPDATE brand_profiles SET content = ? WHERE username = ? AND name = ?', 
                  (json_content, username, profile_name))
    else:
        # Create new
        c.execute('INSERT INTO brand_profiles (username, name, content) VALUES (?, ?, ?)', 
                  (username, profile_name, json_content))
                  
    conn.commit()
    conn.close()
    return True

def get_profiles(username):
    """Returns a DICTIONARY of {name: data}."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT name, content FROM brand_profiles WHERE username = ?', (username,))
    rows = c.fetchall()
    conn.close()
    
    # Convert list of rows back into a Dictionary: {'Brand A': {data...}, 'Brand B': {data...}}
    results = {}
    for name, content in rows:
        try:
            results[name] = json.loads(content)
        except:
            results[name] = {} # Handle empty/bad data gracefully
            
    return results

def delete_profile(username, profile_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM brand_profiles WHERE username = ? AND name = ?', (username, profile_name))
    conn.commit()
    conn.close()
