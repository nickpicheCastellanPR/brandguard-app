import sqlite3
import bcrypt
import json
import os
from datetime import datetime

# --- CRITICAL: POINT TO THE SAFE VOLUME ---
if os.path.exists("/app/data"):
    DB_FOLDER = "/app/data"
else:
    DB_FOLDER = "."

DB_NAME = os.path.join(DB_FOLDER, "users.db")

# --- 1. SETUP & MIGRATION ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. USERS TABLE
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

    # 2. PROFILES TABLE (Restored Functionality)
    c.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT,
            name TEXT,
            data TEXT, -- JSON storage
            created_at TEXT,
            UNIQUE(user_id, name)
        )
    ''')

    # 3. LOGS TABLE
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

# --- 2. SECURITY (BCRYPT) ---
def create_user(username, email, password, is_admin=False):
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
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
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT password_hash, is_admin, subscription_status FROM users WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()

    if data:
        stored_hash = data[0]
        # Verify Password
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return {"username": username, "is_admin": bool(data[1]), "status": data[2]}
    return None

def get_user_count():
    conn = sqlite3.connect(DB_NAME)
    try:
        count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    except:
        count = 0
    conn.close()
    return count

# --- 3. PROFILE MANAGEMENT (Restored) ---
def save_profile(username, profile_name, profile_data):
    conn = sqlite3.connect(DB_NAME)
    data_json = json.dumps(profile_data)
    # Upsert logic (Insert or Replace)
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
        profiles[row[0]] = json.loads(row[1])
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
