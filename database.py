import sqlite3
import json
import hashlib
import os

DB_NAME = "signet.db"

def init_db():
    """Initializes the database with Users and Profiles tables."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Users Table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  username TEXT UNIQUE NOT NULL, 
                  password_hash TEXT NOT NULL)''')
    
    # 2. Profiles Table (Stores the JSON blob of the profile)
    c.execute('''CREATE TABLE IF NOT EXISTS profiles
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  user_id INTEGER, 
                  name TEXT NOT NULL, 
                  data TEXT NOT NULL, 
                  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')
    
    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(username, password):
    """Registers a new user. Returns True if successful."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                  (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # Username taken
    finally:
        conn.close()

def verify_user(username, password):
    """Checks credentials. Returns user_id if valid, else None."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ? AND password_hash = ?", 
              (username, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user[0] if user else None

def save_profile(user_id, profile_name, profile_data):
    """Saves or updates a profile for a specific user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Check if exists to update, else insert
    # Serialize dict to JSON string for storage
    data_str = json.dumps(profile_data)
    
    c.execute("SELECT id FROM profiles WHERE user_id = ? AND name = ?", (user_id, profile_name))
    exists = c.fetchone()
    
    if exists:
        c.execute("UPDATE profiles SET data = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (data_str, exists[0]))
    else:
        c.execute("INSERT INTO profiles (user_id, name, data) VALUES (?, ?, ?)", (user_id, profile_name, data_str))
        
    conn.commit()
    conn.close()

def get_profiles(user_id):
    """Returns a dict of {name: data} for a user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT name, data FROM profiles WHERE user_id = ?", (user_id,))
    rows = c.fetchall()
    conn.close()
    
    # Convert list of tuples back to dict
    profiles = {}
    for name, data_str in rows:
        profiles[name] = json.loads(data_str)
    return profiles

def delete_profile(user_id, profile_name):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM profiles WHERE user_id = ? AND name = ?", (user_id, profile_name))
    conn.commit()
    conn.close()
