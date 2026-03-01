import sqlite3
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import json
import os
import shutil
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

# --- CONFIG ---
if os.path.exists("/app/data"):
    DB_FOLDER = "/app/data"
else:
    DB_FOLDER = "."

# SWITCHING TO V3 DB TO FORCE CLEAN SCHEMA
DB_NAME = os.path.join(DB_FOLDER, "signet_studio_v3.db")

ph = PasswordHasher()

# --- SEAT LIMIT CONFIGURATION ---
# SUPERSEDED by tier_config.TIER_CONFIG — kept for legacy compatibility only
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

    run_migrations()


def run_migrations():
    """Apply schema migrations idempotently. Backs up DB on first run."""
    conn = sqlite3.connect(DB_NAME)

    # Check which user columns already exist
    cursor = conn.execute("PRAGMA table_info(users)")
    user_columns = {row[1] for row in cursor.fetchall()}
    first_migration = 'subscription_tier' not in user_columns

    if first_migration and os.path.exists(DB_NAME):
        shutil.copy(DB_NAME, DB_NAME + ".bak")
        logging.info(f"DB backed up to {DB_NAME}.bak before first migration")

    # --- Add new columns to users ---
    new_user_cols = [
        ("subscription_tier", "TEXT DEFAULT 'solo'"),
        ("org_role", "TEXT DEFAULT 'member'"),
        ("lemon_squeezy_subscription_id", "TEXT DEFAULT NULL"),
        ("lemon_squeezy_variant_id", "TEXT DEFAULT NULL"),
        ("last_subscription_sync", "TEXT DEFAULT NULL"),
        ("last_login", "TIMESTAMP DEFAULT NULL"),
        ("comp_expires_at", "TIMESTAMP DEFAULT NULL"),
        ("comp_reason", "TEXT DEFAULT NULL"),
        ("subscription_override_until", "TIMESTAMP DEFAULT NULL"),
    ]
    for col_name, col_def in new_user_cols:
        if col_name not in user_columns:
            try:
                conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
            except sqlite3.OperationalError:
                pass

    # --- Add is_sample_brand to profiles ---
    cursor = conn.execute("PRAGMA table_info(profiles)")
    profile_columns = {row[1] for row in cursor.fetchall()}
    if 'is_sample_brand' not in profile_columns:
        try:
            conn.execute("ALTER TABLE profiles ADD COLUMN is_sample_brand BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass

    # --- Create organizations table ---
    conn.execute('''
        CREATE TABLE IF NOT EXISTS organizations (
            org_id TEXT PRIMARY KEY,
            org_name TEXT NOT NULL,
            subscription_tier TEXT NOT NULL DEFAULT 'agency',
            owner_username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- Create usage_tracking table ---
    conn.execute('''
        CREATE TABLE IF NOT EXISTS usage_tracking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            org_id TEXT,
            module TEXT NOT NULL,
            action_weight INTEGER DEFAULT 1,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            billing_month TEXT NOT NULL
        )
    ''')

    # --- Add is_impersonated to usage_tracking ---
    cursor = conn.execute("PRAGMA table_info(usage_tracking)")
    ut_columns = {row[1] for row in cursor.fetchall()}
    if 'is_impersonated' not in ut_columns:
        try:
            conn.execute("ALTER TABLE usage_tracking ADD COLUMN is_impersonated BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass

    # --- Create admin_audit_log table ---
    conn.execute('''
        CREATE TABLE IF NOT EXISTS admin_audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_username TEXT NOT NULL,
            action_type TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # --- Create platform_settings table ---
    conn.execute('''
        CREATE TABLE IF NOT EXISTS platform_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT
        )
    ''')

    conn.commit()

    # --- One-time data migration for existing users ---
    if first_migration:
        STATUS_MAP = {
            'retainer':  ('retainer',    'active'),
            'admin':     ('super_admin', 'active'),
            'lifetime':  ('enterprise',  'active'),
            'active':    ('solo',        'active'),
            'trial':     ('solo',        'inactive'),
            'inactive':  ('solo',        'inactive'),
        }
        cursor = conn.execute("SELECT username, subscription_status FROM users")
        users = cursor.fetchall()
        for username, old_status in users:
            old_key = (old_status or 'trial').lower()
            tier, status = STATUS_MAP.get(old_key, ('solo', 'inactive'))
            conn.execute(
                "UPDATE users SET subscription_tier = ?, subscription_status = ? WHERE username = ?",
                (tier, status, username)
            )
        conn.commit()
        logging.info(f"Migrated {len(users)} existing users to new tier/status schema")

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

def get_user_status(username):
    """Retrieves the subscription status for a given user."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT subscription_status FROM users WHERE username = ?", (username,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else "trial"


# --- 6. TIER & USAGE (new) ---

def get_user_full(username):
    """Returns all user fields as a dict, or None if user not found."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    result = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return dict(result) if result else None


def set_user_subscription(username, tier, status, ls_sub_id=None, ls_variant_id=None):
    """Updates subscription_tier, subscription_status, LS fields, and last_subscription_sync."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''
        UPDATE users SET
            subscription_tier = ?,
            subscription_status = ?,
            lemon_squeezy_subscription_id = ?,
            lemon_squeezy_variant_id = ?,
            last_subscription_sync = ?
        WHERE username = ?
    ''', (tier, status, ls_sub_id, ls_variant_id, datetime.now().isoformat(), username))
    conn.commit()
    conn.close()


def get_org_tier(org_id):
    """Returns the subscription_tier for an org."""
    conn = sqlite3.connect(DB_NAME)
    # Check organizations table first
    org = conn.execute(
        "SELECT subscription_tier FROM organizations WHERE org_id = ?", (org_id,)
    ).fetchone()
    if org:
        conn.close()
        return org[0]
    # Fallback: derive from org admin's tier
    result = conn.execute(
        "SELECT subscription_tier FROM users WHERE org_id = ? AND is_admin = 1", (org_id,)
    ).fetchone()
    conn.close()
    return result[0] if result else 'solo'


def count_user_brands(org_id, exclude_sample=True):
    """Count profiles belonging to an org, optionally excluding sample brands."""
    conn = sqlite3.connect(DB_NAME)
    if exclude_sample:
        count = conn.execute(
            "SELECT COUNT(*) FROM profiles WHERE org_id = ? AND (is_sample_brand = 0 OR is_sample_brand IS NULL)",
            (org_id,)
        ).fetchone()[0]
    else:
        count = conn.execute(
            "SELECT COUNT(*) FROM profiles WHERE org_id = ?", (org_id,)
        ).fetchone()[0]
    conn.close()
    return count


def record_usage_action(username, org_id, module, action_weight, billing_month):
    """Records an AI action in the usage_tracking table."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''
        INSERT INTO usage_tracking (username, org_id, module, action_weight, billing_month)
        VALUES (?, ?, ?, ?, ?)
    ''', (username, org_id, module, action_weight, billing_month))
    conn.commit()
    conn.close()


def get_monthly_usage(org_id, billing_month):
    """Returns total action_weight for an org in a billing month (agency/enterprise)."""
    conn = sqlite3.connect(DB_NAME)
    result = conn.execute(
        "SELECT COALESCE(SUM(action_weight), 0) FROM usage_tracking WHERE org_id = ? AND billing_month = ?",
        (org_id, billing_month)
    ).fetchone()
    conn.close()
    return result[0] if result else 0


def get_monthly_usage_user(username, billing_month):
    """Returns total action_weight for a solo user in a billing month."""
    conn = sqlite3.connect(DB_NAME)
    result = conn.execute(
        "SELECT COALESCE(SUM(action_weight), 0) FROM usage_tracking WHERE username = ? AND billing_month = ?",
        (username, billing_month)
    ).fetchone()
    conn.close()
    return result[0] if result else 0


def create_organization(org_id, org_name, tier, owner_username):
    """Creates a new organization record. Returns True on success, False if org_id already exists."""
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute('''
            INSERT INTO organizations (org_id, org_name, subscription_tier, owner_username)
            VALUES (?, ?, ?, ?)
        ''', (org_id, org_name, tier, owner_username))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def get_organization(org_id):
    """Returns an organization record as a dict, or None."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    result = conn.execute("SELECT * FROM organizations WHERE org_id = ?", (org_id,)).fetchone()
    conn.close()
    return dict(result) if result else None


def remove_org_member(username):
    """Removes a user from their org (sets org_id=NULL, org_role='member')."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute(
        "UPDATE users SET org_id = NULL, org_role = 'member' WHERE username = ?",
        (username,)
    )
    conn.commit()
    conn.close()


# --- 7. ADMIN PANEL (new) ---

def log_admin_action(admin_username, action_type, target_type, target_id, details=None):
    """Writes an entry to admin_audit_log."""
    conn = sqlite3.connect(DB_NAME)
    details_json = json.dumps(details, default=str) if details else None
    conn.execute('''
        INSERT INTO admin_audit_log (admin_username, action_type, target_type, target_id, details)
        VALUES (?, ?, ?, ?, ?)
    ''', (admin_username, action_type, target_type, target_id, details_json))
    conn.commit()
    conn.close()


def get_admin_audit_log(limit=200, action_type=None, target_type=None, admin_username=None):
    """Returns admin audit log entries as list of dicts."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    query = "SELECT * FROM admin_audit_log WHERE 1=1"
    params = []
    if action_type:
        query += " AND action_type = ?"
        params.append(action_type)
    if target_type:
        query += " AND target_type = ?"
        params.append(target_type)
    if admin_username:
        query += " AND admin_username = ?"
        params.append(admin_username)
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_users_full():
    """Returns all users as a list of dicts."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_all_organizations():
    """Returns all organizations as a list of dicts."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM organizations ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_user_fields(username, **fields):
    """Update arbitrary fields on a user record. Returns True on success."""
    if not fields:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [username]
    conn = sqlite3.connect(DB_NAME)
    conn.execute(f"UPDATE users SET {set_clause} WHERE username = ?", values)
    conn.commit()
    conn.close()
    return True


def update_organization_fields(org_id, **fields):
    """Update arbitrary fields on an organization record."""
    if not fields:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [org_id]
    conn = sqlite3.connect(DB_NAME)
    conn.execute(f"UPDATE organizations SET {set_clause} WHERE org_id = ?", values)
    conn.commit()
    conn.close()
    return True


def delete_user_full(username):
    """Deletes a user and cleans up related data. Returns summary dict."""
    conn = sqlite3.connect(DB_NAME)
    user = conn.execute("SELECT org_id, subscription_tier FROM users WHERE username = ?", (username,)).fetchone()
    if not user:
        conn.close()
        return {"deleted": False, "reason": "User not found"}

    org_id = user[0]
    tier = user[1]

    if tier == 'super_admin':
        conn.close()
        return {"deleted": False, "reason": "Cannot delete super_admin accounts through UI"}

    # Reassign solo brands to org owner if user is in an org
    if org_id:
        org = conn.execute("SELECT owner_username FROM organizations WHERE org_id = ?", (org_id,)).fetchone()
        owner = org[0] if org else None
        if owner and owner != username:
            # Profiles belong to the org, no reassignment needed — they stay with org_id
            pass
        # Remove org membership
        conn.execute("UPDATE users SET org_id = NULL, org_role = 'member' WHERE username = ?", (username,))
    else:
        # Solo user — delete their personal profiles
        conn.execute("DELETE FROM profiles WHERE org_id = ?", (username,))

    # Remove usage_tracking
    conn.execute("DELETE FROM usage_tracking WHERE username = ?", (username,))

    # Remove the user
    conn.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()
    return {"deleted": True, "reason": "OK", "org_cleaned": org_id}


def delete_organization_full(org_id):
    """Deletes an org, disassociates members, reassigns brands to owner."""
    conn = sqlite3.connect(DB_NAME)
    org = conn.execute("SELECT owner_username FROM organizations WHERE org_id = ?", (org_id,)).fetchone()
    if not org:
        conn.close()
        return {"deleted": False, "reason": "Org not found"}

    owner = org[0]
    member_count = conn.execute("SELECT COUNT(*) FROM users WHERE org_id = ?", (org_id,)).fetchone()[0]

    # Reassign profiles to owner's personal account
    conn.execute("UPDATE profiles SET org_id = ? WHERE org_id = ?", (owner, org_id))

    # Disassociate all members
    conn.execute("UPDATE users SET org_id = NULL, org_role = 'member' WHERE org_id = ?", (org_id,))

    # Delete the org
    conn.execute("DELETE FROM organizations WHERE org_id = ?", (org_id,))
    conn.commit()
    conn.close()
    return {"deleted": True, "member_count": member_count, "brands_reassigned_to": owner}


def get_platform_setting(key):
    """Returns a platform setting value, or None."""
    conn = sqlite3.connect(DB_NAME)
    result = conn.execute("SELECT value FROM platform_settings WHERE key = ?", (key,)).fetchone()
    conn.close()
    return result[0] if result else None


def set_platform_setting(key, value, updated_by="system"):
    """Sets a platform setting (upsert)."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''
        INSERT INTO platform_settings (key, value, updated_at, updated_by)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = ?, updated_by = ?
    ''', (key, value, datetime.now().isoformat(), updated_by,
          value, datetime.now().isoformat(), updated_by))
    conn.commit()
    conn.close()


def get_usage_analytics(billing_month=None):
    """Returns per-user usage summary for the admin analytics dashboard."""
    if not billing_month:
        billing_month = datetime.now().strftime("%Y-%m")
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    rows = conn.execute('''
        SELECT
            u.username,
            u.email,
            u.subscription_tier,
            u.org_id,
            u.subscription_status,
            COALESCE(curr.total_actions, 0) as actions_this_month,
            COALESCE(prev.total_actions, 0) as actions_last_month
        FROM users u
        LEFT JOIN (
            SELECT username, SUM(action_weight) as total_actions
            FROM usage_tracking
            WHERE billing_month = ? AND (is_impersonated = 0 OR is_impersonated IS NULL)
            GROUP BY username
        ) curr ON u.username = curr.username
        LEFT JOIN (
            SELECT username, SUM(action_weight) as total_actions
            FROM usage_tracking
            WHERE billing_month = ?
            GROUP BY username
        ) prev ON u.username = prev.username
        ORDER BY COALESCE(curr.total_actions, 0) DESC
    ''', (billing_month, _prev_month(billing_month))).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def _prev_month(billing_month):
    """Returns the previous billing month string (YYYY-MM)."""
    year, month = map(int, billing_month.split('-'))
    if month == 1:
        return f"{year - 1}-12"
    return f"{year}-{month - 1:02d}"


def get_monthly_usage_all(billing_month=None):
    """Returns total actions across all users for a billing month."""
    if not billing_month:
        billing_month = datetime.now().strftime("%Y-%m")
    conn = sqlite3.connect(DB_NAME)
    result = conn.execute(
        "SELECT COALESCE(SUM(action_weight), 0) FROM usage_tracking WHERE billing_month = ?",
        (billing_month,)
    ).fetchone()
    conn.close()
    return result[0] if result else 0


def get_monthly_usage_trend(months=6):
    """Returns list of (billing_month, total_actions) for the last N months."""
    conn = sqlite3.connect(DB_NAME)
    now = datetime.now()
    results = []
    for i in range(months - 1, -1, -1):
        y = now.year
        m = now.month - i
        while m <= 0:
            m += 12
            y -= 1
        bm = f"{y}-{m:02d}"
        total = conn.execute(
            "SELECT COALESCE(SUM(action_weight), 0) FROM usage_tracking WHERE billing_month = ?",
            (bm,)
        ).fetchone()[0]
        results.append({"month": bm, "actions": total})
    conn.close()
    return results


def record_usage_action_impersonated(username, org_id, module, action_weight, billing_month):
    """Records an AI action flagged as impersonated (does not count toward soft cap)."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''
        INSERT INTO usage_tracking (username, org_id, module, action_weight, billing_month, is_impersonated)
        VALUES (?, ?, ?, ?, ?, 1)
    ''', (username, org_id, module, action_weight, billing_month))
    conn.commit()
    conn.close()


def get_table_row_counts():
    """Returns dict of table_name → row_count for admin health check."""
    conn = sqlite3.connect(DB_NAME)
    tables = ['users', 'profiles', 'usage_tracking', 'organizations', 'activity_log', 'admin_audit_log', 'platform_settings']
    counts = {}
    for t in tables:
        try:
            counts[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except sqlite3.OperationalError:
            counts[t] = 0
    conn.close()
    return counts


def update_last_login(username):
    """Updates last_login to now for a user."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("UPDATE users SET last_login = ? WHERE username = ?",
                 (datetime.now().isoformat(), username))
    conn.commit()
    conn.close()


def create_user_admin(username, email, password, tier='solo', org_id=None, org_role='member'):
    """Admin user creation — bypasses seat limits."""
    hashed = ph.hash(password)
    conn = sqlite3.connect(DB_NAME)
    try:
        conn.execute('''
            INSERT INTO users (username, email, password_hash, org_id, is_admin, subscription_tier,
                               subscription_status, org_role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
        ''', (username, email, hashed, org_id, 1 if org_role == 'owner' else 0,
              tier, org_role, datetime.now().isoformat()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()
