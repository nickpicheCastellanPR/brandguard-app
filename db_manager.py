import sqlite3
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import json
import os
from datetime import datetime

# --- CONFIG ---
if os.path.exists("/app/data"):
    DB_FOLDER = "/app/data"
else:
    DB_FOLDER = "."

DB_NAME = os.path.join(DB_FOLDER, "users.db")

# Initialize Argon2 Hasher
ph = PasswordHasher()

# --- 1. SETUP & MIGRATION ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Users Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT,
            password_hash TEXT,
            is_admin BOOLEAN DEFAULT 0,
            subscription_status TEXT DEFAULT 'trial',
            created_at TEXT
        )
    ''')

    # Profiles Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            name TEXT,
            data TEXT,
            created_at TEXT,
            UNIQUE(user_id, name)
        )
    ''')

    # Logs Table
    c.execute('''
        CREATE TABLE IF NOT EXISTS generation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            timestamp TEXT,
            inputs_json TEXT,
            output_text TEXT,
            estimated_cost REAL
        )
    ''')
    
    conn.commit()
    conn.close()

# --- 2. SECURITY (ARGON2) ---
def create_user(username, email, password, is_admin=False):
    """Creates a new user with ARGON2 hashing."""
    # Hash the password (Argon2 handles salt automatically)
    hashed = ph.hash(password)
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO users (username, email, password_hash, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, email, hashed, is_admin, datetime.now()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def check_login(username, password):
    """Verifies password using Argon2 and returns user info + email."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Critical: Fetch Email for the Paywall check
    c.execute('SELECT password_hash, is_admin, subscription_status, email FROM users WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()

    if data:
        stored_hash = data[0]
        try:
            # Verify the password
            ph.verify(stored_hash, password)
            
            # Check if hash needs updating (Argon2 feature)
            if ph.check_needs_rehash(stored_hash):
                # We could update it here, but skipping for simplicity
                pass
                
            return {
                "username": username, 
                "is_admin": bool(data[1]), 
                "status": data[2],
                "email": data[3]
            }
        except VerifyMismatchError:
            # Password wrong
            return None
        except Exception as e:
            print(f"Auth Error: {e}")
            return None
    return None

def get_user_count():
    conn = sqlite3.connect(DB_NAME)
    try:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    except:
        count = 0
    conn.close()
    return count

# --- 3. PROFILE MANAGEMENT ---
def save_profile(username, profile_name, profile_data):
    conn = sqlite3.connect(DB_NAME)
    data_json = json.dumps(profile_data)
    conn.execute('''
        INSERT OR REPLACE INTO profiles (user_id, name, data, created_at)
        VALUES (?, ?, ?, ?)
    ''', (username, profile_name, data_json, datetime.now()))
    conn.commit()
    conn.close()

def get_profiles(username):
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("SELECT name, data FROM profiles WHERE user_id = ?", (username,)).fetchall()
    conn.close()
    
    profiles = {}
    for row in rows:
        try:
            profiles[row[0]] = json.loads(row[1])
        except:
            pass
    return profiles

def delete_profile(username, profile_name):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("DELETE FROM profiles WHERE user_id = ? AND name = ?", (username, profile_name))
    conn.commit()
    conn.close()

# --- 4. LOGGING ---
def log_generation(username, inputs_dict, output_text, token_usage_est):
    conn = sqlite3.connect(DB_NAME)
    inputs_json = json.dumps(inputs_dict)
    conn.execute('''
        INSERT INTO generation_logs (username, timestamp, inputs_json, output_text, estimated_cost)
        VALUES (?, ?, ?, ?, ?)
    ''', (username, datetime.now(), inputs_json, output_text, token_usage_est))
    conn.commit()
    conn.close()

# --- 5. ADMIN VIEWS ---
def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    users = conn.execute("SELECT username, email, is_admin, subscription_status, created_at FROM users").fetchall()
    conn.close()
    return users

def get_all_logs():
    conn = sqlite3.connect(DB_NAME)
    logs = conn.execute("SELECT username, timestamp, inputs_json, estimated_cost FROM generation_logs ORDER BY id DESC LIMIT 50").fetchall()
    conn.close()
    return logs

# --- 6. SUBSCRIPTION HELPERS ---
def get_user_status(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT subscription_status FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else "trial"

def update_user_status(username, new_status):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET subscription_status = ? WHERE username = ?", (new_status, username))
    conn.commit()
    conn.close()
