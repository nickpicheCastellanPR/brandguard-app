import sqlite3
import json
import os
import auth

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
    """Create new user with Argon2 password hash."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    hashed_pw = auth.hash_password(password)
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_pw))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(username, password):
    """
    Verify user credentials.
    Supports both legacy SHA256 and new Argon2 passwords.
    Automatically upgrades legacy passwords to Argon2 on successful login.

    Returns:
        True if credentials valid, False otherwise
    """
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    # Get the stored hash for this username
    c.execute('SELECT password FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()

    if not result:
        # Username doesn't exist
        return False

    stored_hash = result[0]

    # Verify password using our auth module (handles both formats)
    if auth.verify_password(password, stored_hash):
        # Password is correct! Now check if we should upgrade it
        if auth.should_rehash_password(stored_hash):
            # Upgrade legacy password to Argon2
            def save_new_hash(uname, new_hash):
                conn = sqlite3.connect(DB_NAME)
                c = conn.cursor()
                c.execute('UPDATE users SET password = ? WHERE username = ?', (new_hash, uname))
                conn.commit()
                conn.close()
                return True

            auth.upgrade_password_on_login(username, password, stored_hash, save_new_hash)
            # Note: We don't check if upgrade succeeded - login still works either way

        return True

    return False

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
