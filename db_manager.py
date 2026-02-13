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

# SWITCHING TO V3 DB TO FORCE CLEAN SCHEMA
DB_NAME = os.path.join(DB_FOLDER, "signet_studio_v3.db")

ph = PasswordHasher()

# --- SEAT LIMIT CONFIGURATION ---
# usage: checks 'subscription_status' of the Org Admin
SEAT_LIMITS = {
    "trial": 1,
    "solo": 1,
    "agency": 5,
    "enterprise": 20,
    "active": 5  # Fallback for generic active status
}

# --- 1. SETUP & SCHEMA ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # USERS: Added 'org_id'
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT,
            password_hash TEXT,
            is_admin BOOLEAN DEFAULT 0,
            org_id TEXT,
            subscription_status TEXT DEFAULT 'trial',
            created_at TEXT
        )
    ''')

    # PROFILES: Added 'org_id' (Shared Ownership)
    c.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id TEXT,
            name TEXT,
            data TEXT,
            created_at TEXT,
            updated_by TEXT,
            UNIQUE(org_id, name)
        )
    ''')

    # RICH LOGS: The "God View" Data Structure
    c.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id TEXT,
            username TEXT,
            timestamp TEXT,
            activity_type TEXT,   -- e.g. "VISUAL AUDIT", "COPY EDIT"
            asset_name TEXT,      -- e.g. "Q3 Report.pdf"
            score INTEGER,        -- e.g. 85
            verdict TEXT,         -- e.g. "APPROVED", "FAILED"
            metadata_json TEXT,   -- The full result data
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

# --- 2. AUTH & USER MANAGEMENT ---

def check_seat_availability(org_id):
    """Returns True if the Org has space for a new user."""
    conn = sqlite3.connect(DB_NAME)
    
    # 1. Count current users
    cursor = conn.execute("SELECT COUNT(*) FROM users WHERE org_id = ?", (org_id,))
    current_count = cursor.fetchone()[0]
    
    # 2. Get Org Tier (via Admin's status)
    # We assume the user with is_admin=1 defines the tier
    cursor = conn.execute("SELECT subscription_status FROM users WHERE org_id = ? AND is_admin = 1", (org_id,))
    result = cursor.fetchone()
    conn.close()
    
    # Default to trial limits if no admin found (shouldn't happen)
    status = result[0] if result else "trial"
    limit = SEAT_LIMITS.get(status.lower(), 1) # Default to 1 seat if status unknown
    
    return current_count < limit

def create_user(username, email, password, org_id=None, is_admin=False):
    """Creates a user. Enforces seat limits if adding to an existing Org."""
    hashed = ph.hash(password)
    
    # SEAT CHECK
    if org_id:
        # If this is a new Org (count is 0), this check passes (0 < limit).
        # If adding to existing Org, it enforces the limit.
        if not check_seat_availability(org_id):
            return False

    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute('''
            INSERT INTO users (username, email, password_hash, org_id, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, email, hashed, org_id, is_admin, datetime.now()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def check_login(username, password):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('SELECT password_hash, is_admin, subscription_status, email, org_id FROM users WHERE username = ?', (username,))
    data = c.fetchone()
    conn.close()

    if data:
        stored_hash = data[0]
        try:
            ph.verify(stored_hash, password)
            return {
                "username": username, 
                "is_admin": bool(data[1]), 
                "status": data[2],
                "email": data[3],
                "org_id": data[4]
            }
        except VerifyMismatchError:
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

def get_users_by_org(org_id):
    """Returns list of users belonging to a specific Org."""
    conn = sqlite3.connect(DB_NAME)
    users = conn.execute("SELECT username, email, is_admin, created_at FROM users WHERE org_id = ?", (org_id,)).fetchall()
    conn.close()
    return users

# --- 3. STUDIO PROFILE MANAGEMENT (Org-Based) ---
def save_profile(user_id, profile_name, profile_data):
    conn = sqlite3.connect(DB_NAME)
    
    # 1. Resolve Org ID from User
    org_res = conn.execute("SELECT org_id FROM users WHERE username = ?", (user_id,)).fetchone()
    # Fallback to user_id itself if no Org exists (Solo Mode)
    org_id = org_res[0] if org_res and org_res[0] else user_id 
    
    data_json = json.dumps(profile_data)
    
    # 2. Save to Org (Not just User)
    conn.execute('''
        INSERT OR REPLACE INTO profiles (org_id, name, data, created_at, updated_by)
        VALUES (?, ?, ?, ?, ?)
    ''', (org_id, profile_name, data_json, datetime.now(), user_id))
    
    conn.commit()
    conn.close()

def get_profiles(username):
    # Fetch profiles for the USER'S ORGANIZATION
    conn = sqlite3.connect(DB_NAME)
    
    # 1. Find User's Org
    org_res = conn.execute("SELECT org_id FROM users WHERE username = ?", (username,)).fetchone()
    org_id = org_res[0] if org_res and org_res[0] else username
    
    # 2. Fetch All Profiles for that Org
    rows = conn.execute("SELECT name, data FROM profiles WHERE org_id = ?", (org_id,)).fetchall()
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
    # Get Org
    org_res = conn.execute("SELECT org_id FROM users WHERE username = ?", (username,)).fetchone()
    org_id = org_res[0] if org_res and org_res[0] else username
    
    conn.execute("DELETE FROM profiles WHERE org_id = ? AND name = ?", (org_id, profile_name))
    conn.commit()
    conn.close()

# --- 4. THE GOD VIEW (Rich Logging) ---
def log_event(org_id, username, activity_type, asset_name, score, verdict, metadata):
    """Logs an event to the persistent Studio timeline."""
    conn = sqlite3.connect(DB_NAME)
    meta_json = json.dumps(metadata, default=str) # safe serialization
    
    conn.execute('''
        INSERT INTO activity_log (org_id, username, timestamp, activity_type, asset_name, score, verdict, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (org_id, username, datetime.now().strftime("%H:%M"), activity_type, asset_name, score, verdict, meta_json))
    
    conn.commit()
    conn.close()

def get_org_logs(org_id, limit=20):
    """Fetches the timeline for the entire agency."""
    conn = sqlite3.connect(DB_NAME)
    # Return as list of dictionaries
    conn.row_factory = sqlite3.Row
    rows = conn.execute('''
        SELECT * FROM activity_log 
        WHERE org_id = ? 
        ORDER BY id DESC LIMIT ?
    ''', (org_id, limit)).fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

# --- 5. SUBSCRIPTION ---
def update_user_status(username, new_status):
    conn = sqlite3.connect(DB_NAME)
    conn.execute("UPDATE users SET subscription_status = ? WHERE username = ?", (new_status, username))
    conn.commit()
    conn.close()
