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
    
    # 2. Profiles Table (Stores full JSON content)
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

def save_profile(username, profile_name, profile_data):
    """Saves a profile (Smart version: handles Objects, Strings, and Dicts)."""
    
    # --- ROBUSTNESS LAYER: NORMALIZE DATA TO DICT ---
    # This fixes the issues with 'profile_obj' and 'new_raw' from Brand Manager
    if not isinstance(profile_data, dict):
        if hasattr(profile_data, 'dict') and callable(profile_data.dict):
            # Pydantic models
            profile_data = profile_data.dict()
        elif hasattr(profile_data, '__dict__'):
            # Standard Python objects
            profile_data = profile_data.__dict__
        elif isinstance(profile_data, str):
            try:
                # Try to parse string as JSON
                profile_data = json.loads(profile_data)
            except ValueError:
                # If it's just raw text, wrap it so it doesn't break
                profile_data = {"raw_content": profile_data}
        else:
            # Fallback for lists or other types
            profile_data = {"data": profile_data}
    # ------------------------------------------------

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Convert the NOW NORMALIZED dictionary into a JSON string
    json_content = json.dumps(profile_data)
    
    # Check if profile already exists for this user
    c.execute('SELECT * FROM brand_profiles WHERE username = ? AND name = ?', (username, profile_name))
    if c.fetchone():
        # Update existing
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
    
    # Convert rows back into a Dictionary: {'Brand A': {data...}}
    results = {}
    for name, content in rows:
        try:
            results[name] = json.loads(content)
        except:
            results[name] = {} 
            
    return results

def delete_profile(username, profile_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('DELETE FROM brand_profiles WHERE username = ? AND name = ?', (username, profile_name))
    conn.commit()
    conn.close()
