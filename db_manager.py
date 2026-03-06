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
        ("is_beta_tester", "BOOLEAN DEFAULT 0"),
        ("is_suspended", "BOOLEAN DEFAULT 0"),
        ("suspended_at", "TIMESTAMP DEFAULT NULL"),
        ("suspended_reason", "TEXT DEFAULT NULL"),
        ("suspended_by", "TEXT DEFAULT NULL"),
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
    if 'action_detail' not in ut_columns:
        try:
            conn.execute("ALTER TABLE usage_tracking ADD COLUMN action_detail TEXT DEFAULT NULL")
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

    # --- Create product_events table (analytics layer) ---
    conn.execute('''
        CREATE TABLE IF NOT EXISTS product_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            username TEXT NOT NULL,
            org_id TEXT,
            brand_id INTEGER,
            metadata_json TEXT,
            session_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    # Indices for product_events
    for idx_sql in [
        "CREATE INDEX IF NOT EXISTS idx_pe_type ON product_events(event_type)",
        "CREATE INDEX IF NOT EXISTS idx_pe_user ON product_events(username)",
        "CREATE INDEX IF NOT EXISTS idx_pe_session ON product_events(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_pe_timestamp ON product_events(timestamp)",
    ]:
        try:
            conn.execute(idx_sql)
        except sqlite3.OperationalError:
            pass

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
    if not profile_name or not profile_name.strip():
        return False

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


def _resolve_org_id(conn, username):
    """Internal helper — resolve org_id from username (fallback to username)."""
    org_res = conn.execute("SELECT org_id FROM users WHERE username = ?", (username,)).fetchone()
    return org_res[0] if org_res and org_res[0] else username


def load_sample_brand(username):
    """Load the Meridian Labs sample brand for a user/org. Returns True on success."""
    from sample_brand_data import SAMPLE_BRAND
    conn = sqlite3.connect(DB_NAME)
    org_id = _resolve_org_id(conn, username)
    profile_name = SAMPLE_BRAND["profile_name"]

    # Check if already loaded
    existing = conn.execute(
        "SELECT id FROM profiles WHERE org_id = ? AND name = ?",
        (org_id, profile_name)
    ).fetchone()
    if existing:
        conn.close()
        return False  # Already loaded

    data_json = json.dumps(SAMPLE_BRAND["profile_data"])
    conn.execute('''
        INSERT INTO profiles (org_id, name, data, created_at, updated_by, is_sample_brand)
        VALUES (?, ?, ?, ?, ?, 1)
    ''', (org_id, profile_name, data_json, datetime.now(), username))
    conn.commit()
    conn.close()
    return True


def has_sample_brand(username):
    """Check if the user's org already has the sample brand loaded."""
    conn = sqlite3.connect(DB_NAME)
    org_id = _resolve_org_id(conn, username)
    result = conn.execute(
        "SELECT id FROM profiles WHERE org_id = ? AND is_sample_brand = 1",
        (org_id,)
    ).fetchone()
    conn.close()
    return result is not None


def delete_sample_brand(username):
    """Remove the sample brand from a user's org."""
    conn = sqlite3.connect(DB_NAME)
    org_id = _resolve_org_id(conn, username)
    conn.execute(
        "DELETE FROM profiles WHERE org_id = ? AND is_sample_brand = 1",
        (org_id,)
    )
    conn.commit()
    conn.close()


def get_brand_owner_info(username):
    """Returns (org_id, org_role, subscription_tier) for permission checks on brand deletion."""
    conn = sqlite3.connect(DB_NAME)
    row = conn.execute(
        "SELECT org_id, org_role, subscription_tier FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()
    if not row:
        return None, 'member', 'solo'
    return row[0] or username, row[1] or 'member', row[2] or 'solo'


def is_profile_sample(username, profile_name):
    """Check whether a specific profile is a sample brand."""
    conn = sqlite3.connect(DB_NAME)
    org_id = _resolve_org_id(conn, username)
    result = conn.execute(
        "SELECT is_sample_brand FROM profiles WHERE org_id = ? AND name = ?",
        (org_id, profile_name)
    ).fetchone()
    conn.close()
    return bool(result and result[0])


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


def record_usage_action(username, org_id, module, action_weight, billing_month, action_detail=None):
    """Records an AI action in the usage_tracking table."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''
        INSERT INTO usage_tracking (username, org_id, module, action_weight, billing_month, action_detail)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (username, org_id, module, action_weight, billing_month, action_detail))
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


def reset_user_password(username, new_password):
    """Reset a user's password. Returns True on success."""
    hashed = ph.hash(new_password)
    conn = sqlite3.connect(DB_NAME)
    conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hashed, username))
    conn.commit()
    conn.close()
    return True


def get_user_by_email(email):
    """Look up a username by email address. Returns username or None."""
    conn = sqlite3.connect(DB_NAME)
    row = conn.execute("SELECT username FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row[0] if row else None


def suspend_user(username, reason, admin_username):
    """Suspend a user account. Returns True on success, False if target is super_admin."""
    conn = sqlite3.connect(DB_NAME)
    row = conn.execute("SELECT subscription_tier FROM users WHERE username = ?", (username,)).fetchone()
    if row and row[0] == "super_admin":
        conn.close()
        return False
    conn.execute(
        "UPDATE users SET is_suspended = 1, suspended_at = ?, suspended_reason = ?, suspended_by = ? WHERE username = ?",
        (datetime.now().isoformat(), reason, admin_username, username)
    )
    conn.commit()
    conn.close()
    return True


def unsuspend_user(username):
    """Unsuspend a user account. Returns True on success."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute(
        "UPDATE users SET is_suspended = 0, suspended_at = NULL, suspended_reason = NULL, suspended_by = NULL WHERE username = ?",
        (username,)
    )
    conn.commit()
    conn.close()
    return True


def is_user_suspended(username):
    """Check if a user is suspended. Returns (is_suspended, reason) tuple."""
    conn = sqlite3.connect(DB_NAME)
    result = conn.execute(
        "SELECT is_suspended, suspended_reason FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()
    if result:
        return bool(result[0]), result[1]
    return False, None


def get_daily_usage_platform(billing_month):
    """Returns daily usage across all users for platform-level analytics."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    rows = conn.execute('''
        SELECT DATE(timestamp) as day, SUM(action_weight) as actions
        FROM usage_tracking
        WHERE billing_month = ?
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp)
    ''', (billing_month,)).fetchall()
    conn.close()
    return [dict(row) for row in rows]


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


def record_usage_action_impersonated(username, org_id, module, action_weight, billing_month, action_detail=None):
    """Records an AI action flagged as impersonated (does not count toward soft cap)."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute('''
        INSERT INTO usage_tracking (username, org_id, module, action_weight, billing_month, is_impersonated, action_detail)
        VALUES (?, ?, ?, ?, ?, 1, ?)
    ''', (username, org_id, module, action_weight, billing_month, action_detail))
    conn.commit()
    conn.close()


def update_last_login(username):
    """Updates last_login to now for a user."""
    conn = sqlite3.connect(DB_NAME)
    conn.execute("UPDATE users SET last_login = ? WHERE username = ?",
                 (datetime.now().isoformat(), username))
    conn.commit()
    conn.close()


def get_table_row_counts():
    """Returns dict of table_name → row_count for admin health check."""
    conn = sqlite3.connect(DB_NAME)
    tables = ['users', 'profiles', 'usage_tracking', 'organizations',
              'activity_log', 'admin_audit_log', 'platform_settings', 'product_events']
    counts = {}
    for t in tables:
        try:
            counts[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except sqlite3.OperationalError:
            counts[t] = 0
    conn.close()
    return counts


# ── 8. PRODUCT ANALYTICS (event tracking) ────────────────────────────────────

# API cost constants — update when Anthropic changes pricing
_API_PRICING = {
    "claude-opus-4-6":   {"input_per_m": 5.00,  "output_per_m": 25.00},
    "claude-sonnet-4-6": {"input_per_m": 3.00,  "output_per_m": 15.00},
    "claude-haiku-4-5":  {"input_per_m": 1.00,  "output_per_m": 5.00},
}


def estimate_api_cost(input_tokens, output_tokens, model="claude-opus-4-6"):
    """Estimate USD cost from Anthropic API token usage."""
    pricing = _API_PRICING.get(model, _API_PRICING["claude-opus-4-6"])
    cost = (input_tokens / 1_000_000 * pricing["input_per_m"]) + \
           (output_tokens / 1_000_000 * pricing["output_per_m"])
    return round(cost, 6)


def track_event(event_type, username, metadata=None, brand_id=None,
                session_id=None, org_id=None):
    """Record a product analytics event. Fails silently — tracking never breaks the app."""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.execute(
            """INSERT INTO product_events
               (event_type, username, org_id, brand_id, metadata_json, session_id)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (event_type, username, org_id, brand_id,
             json.dumps(metadata) if metadata else None,
             session_id)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logging.warning(f"Event tracking failed ({event_type}): {e}")


def check_milestone(username, step_name, session_id=None, org_id=None):
    """Fire onboarding milestone only if not already recorded for this user."""
    try:
        conn = sqlite3.connect(DB_NAME)
        existing = conn.execute(
            "SELECT 1 FROM product_events WHERE event_type='onboarding_step' "
            "AND username=? AND metadata_json LIKE ?",
            (username, f'%"{step_name}"%')
        ).fetchone()
        if not existing:
            conn.execute(
                """INSERT INTO product_events
                   (event_type, username, org_id, metadata_json, session_id)
                   VALUES (?, ?, ?, ?, ?)""",
                ("onboarding_step", username, org_id,
                 json.dumps({"step": step_name}), session_id)
            )
            conn.commit()
        conn.close()
    except Exception:
        pass


# ── Analytics query functions ─────────────────────────────────────────────────

def get_active_users(days=7):
    """Returns count of users with at least 1 module_action in last N days."""
    conn = sqlite3.connect(DB_NAME)
    result = conn.execute(
        """SELECT COUNT(DISTINCT username) FROM product_events
           WHERE event_type='module_action'
           AND timestamp >= datetime('now', ?)""",
        (f'-{days} days',)
    ).fetchone()
    conn.close()
    return result[0] if result else 0


def get_user_sessions_per_week(days=28):
    """Returns avg sessions per active user per week over last N days."""
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute(
        """SELECT username, COUNT(DISTINCT session_id) as sessions
           FROM product_events
           WHERE event_type='session_start'
           AND timestamp >= datetime('now', ?)
           GROUP BY username""",
        (f'-{days} days',)
    ).fetchall()
    conn.close()
    if not rows:
        return 0.0
    weeks = max(days / 7, 1)
    total_sessions = sum(r[1] for r in rows)
    return round(total_sessions / len(rows) / weeks, 1)


def get_user_return_table():
    """Returns per-user retention data for the return table."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT
            u.username,
            u.created_at as signed_up,
            u.subscription_tier,
            MAX(pe.timestamp) as last_active,
            COUNT(DISTINCT CASE WHEN pe.event_type='module_action' THEN pe.id END) as total_actions,
            COUNT(DISTINCT strftime('%W', pe.timestamp)) as weeks_active
        FROM users u
        LEFT JOIN product_events pe ON u.username = pe.username
            AND pe.event_type = 'module_action'
        WHERE u.subscription_tier != 'super_admin'
        GROUP BY u.username
        ORDER BY MAX(pe.timestamp) DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_module_engagement():
    """Returns module engagement data for the analytics dashboard."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT
            json_extract(metadata_json, '$.module') as module,
            COUNT(*) as total_actions,
            COUNT(DISTINCT username) as unique_users
        FROM product_events
        WHERE event_type = 'module_action'
        AND json_extract(metadata_json, '$.module') IS NOT NULL
        GROUP BY json_extract(metadata_json, '$.module')
        ORDER BY total_actions DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_module_engagement_week(weeks_ago=0):
    """Returns module action counts for a specific week."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    start = f'-{(weeks_ago + 1) * 7} days'
    end = f'-{weeks_ago * 7} days'
    rows = conn.execute("""
        SELECT
            json_extract(metadata_json, '$.module') as module,
            COUNT(*) as actions
        FROM product_events
        WHERE event_type = 'module_action'
        AND timestamp >= datetime('now', ?)
        AND timestamp < datetime('now', ?)
        GROUP BY json_extract(metadata_json, '$.module')
    """, (start, end)).fetchall()
    conn.close()
    return {r['module']: r['actions'] for r in rows}


def get_session_action_distribution():
    """Returns distribution of actions per session."""
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("""
        SELECT session_id, COUNT(*) as actions
        FROM product_events
        WHERE event_type = 'module_action'
        AND session_id IS NOT NULL
        GROUP BY session_id
    """).fetchall()
    conn.close()

    # Also count sessions with zero module actions
    all_sessions = conn if False else None  # placeholder
    conn2 = sqlite3.connect(DB_NAME)
    total_sessions = conn2.execute(
        "SELECT COUNT(DISTINCT session_id) FROM product_events WHERE event_type='session_start'"
    ).fetchone()[0]
    conn2.close()

    action_sessions = len(rows)
    zero_sessions = max(total_sessions - action_sessions, 0)

    buckets = {"0": zero_sessions, "1": 0, "2-3": 0, "4+": 0}
    for _, count in rows:
        if count == 1:
            buckets["1"] += 1
        elif count <= 3:
            buckets["2-3"] += 1
        else:
            buckets["4+"] += 1

    return buckets, total_sessions


def get_api_costs(days=30):
    """Returns API cost data for the last N days."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    # Total cost
    total = conn.execute("""
        SELECT COALESCE(SUM(json_extract(metadata_json, '$.estimated_cost_usd')), 0) as total_cost,
               COUNT(*) as total_actions
        FROM product_events
        WHERE event_type = 'api_cost'
        AND timestamp >= datetime('now', ?)
    """, (f'-{days} days',)).fetchone()

    # Cost per module
    per_module = conn.execute("""
        SELECT json_extract(metadata_json, '$.module') as module,
               SUM(json_extract(metadata_json, '$.estimated_cost_usd')) as cost,
               COUNT(*) as actions
        FROM product_events
        WHERE event_type = 'api_cost'
        AND timestamp >= datetime('now', ?)
        GROUP BY json_extract(metadata_json, '$.module')
        ORDER BY cost DESC
    """, (f'-{days} days',)).fetchall()

    # Daily trend
    daily = conn.execute("""
        SELECT DATE(timestamp) as day,
               SUM(json_extract(metadata_json, '$.estimated_cost_usd')) as cost
        FROM product_events
        WHERE event_type = 'api_cost'
        AND timestamp >= datetime('now', ?)
        GROUP BY DATE(timestamp)
        ORDER BY DATE(timestamp)
    """, (f'-{days} days',)).fetchall()

    conn.close()
    return {
        "total_cost": total['total_cost'] if total else 0,
        "total_actions": total['total_actions'] if total else 0,
        "per_module": [dict(r) for r in per_module],
        "daily": [dict(r) for r in daily],
    }


def get_active_user_count(days=30):
    """Returns count of distinct active users (with module_action) in last N days."""
    conn = sqlite3.connect(DB_NAME)
    result = conn.execute(
        """SELECT COUNT(DISTINCT username) FROM product_events
           WHERE event_type='module_action'
           AND timestamp >= datetime('now', ?)""",
        (f'-{days} days',)
    ).fetchone()
    conn.close()
    return result[0] if result else 0


def get_calibration_distribution():
    """Returns calibration score distribution across all non-sample brands."""
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("""
        SELECT data FROM profiles
        WHERE is_sample_brand = 0 OR is_sample_brand IS NULL
    """).fetchall()
    conn.close()

    buckets = {"0-25": 0, "26-50": 0, "51-75": 0, "76-100": 0}
    scores = []
    for row in rows:
        try:
            data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            score = data.get('calibration_score', 0) if isinstance(data, dict) else 0
            scores.append(score)
            if score <= 25:
                buckets["0-25"] += 1
            elif score <= 50:
                buckets["26-50"] += 1
            elif score <= 75:
                buckets["51-75"] += 1
            else:
                buckets["76-100"] += 1
        except (json.JSONDecodeError, TypeError):
            buckets["0-25"] += 1
    return buckets, scores


def get_avg_calibration_trend(weeks=8):
    """Returns weekly average calibration score from calibration_change events."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT strftime('%Y-W%W', timestamp) as week,
               AVG(json_extract(metadata_json, '$.new_score')) as avg_score
        FROM product_events
        WHERE event_type = 'calibration_change'
        AND timestamp >= datetime('now', ?)
        GROUP BY week
        ORDER BY week
    """, (f'-{weeks * 7} days',)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_profile_completion_stats():
    """Returns profile completion breakdown across all non-sample brands."""
    conn = sqlite3.connect(DB_NAME)
    rows = conn.execute("""
        SELECT data FROM profiles
        WHERE is_sample_brand = 0 OR is_sample_brand IS NULL
    """).fetchall()
    conn.close()

    total = len(rows)
    if total == 0:
        return {}

    stats = {
        "strategy_fields": 0,
        "voice_samples": 0,
        "voice_3plus": 0,
        "message_house": 0,
        "visual_identity": 0,
        "social_samples": 0,
    }

    for row in rows:
        try:
            data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
            if not isinstance(data, dict):
                continue
            inputs = data.get('inputs', {})

            # Strategy fields: name + mission + values + archetype
            strat_count = sum(1 for k in ['wiz_name', 'wiz_mission', 'wiz_values', 'wiz_archetype']
                              if inputs.get(k))
            if strat_count >= 3:
                stats["strategy_fields"] += 1

            if len(inputs.get('voice_dna', '')) > 20 or '[ASSET:' in inputs.get('voice_dna', ''):
                stats["voice_samples"] += 1
                # Count individual voice assets
                voice_count = inputs.get('voice_dna', '').count('[ASSET:')
                if voice_count >= 3:
                    stats["voice_3plus"] += 1

            if any(inputs.get(k) for k in ['mh_brand_promise', 'mh_pillars_json', 'mh_boilerplate']):
                stats["message_house"] += 1

            if len(inputs.get('visual_dna', '')) > 20 or '[ASSET:' in inputs.get('visual_dna', ''):
                stats["visual_identity"] += 1

            if len(inputs.get('social_dna', '')) > 20 or '[ASSET:' in inputs.get('social_dna', ''):
                stats["social_samples"] += 1

        except (json.JSONDecodeError, TypeError):
            pass

    return {k: round(v / total * 100) for k, v in stats.items()} if total > 0 else stats


def get_onboarding_funnel():
    """Returns onboarding funnel data."""
    conn = sqlite3.connect(DB_NAME)
    total_users = conn.execute(
        "SELECT COUNT(*) FROM users WHERE subscription_tier != 'super_admin'"
    ).fetchone()[0]

    steps = [
        "account_created", "first_brand_created", "first_voice_sample",
        "first_module_run", "message_house_started",
        "calibration_crossed_60", "calibration_crossed_90"
    ]
    funnel = {}
    for step in steps:
        count = conn.execute(
            "SELECT COUNT(DISTINCT username) FROM product_events "
            "WHERE event_type='onboarding_step' AND metadata_json LIKE ?",
            (f'%"{step}"%',)
        ).fetchone()[0]
        funnel[step] = count

    conn.close()
    return funnel, total_users


def get_inactive_user_diagnostics(days_threshold=14):
    """Returns diagnostics for users inactive for N+ days."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row

    users = conn.execute("""
        SELECT u.username, u.created_at,
            MAX(pe.timestamp) as last_active,
            COUNT(DISTINCT CASE WHEN pe.event_type='module_action' THEN pe.id END) as total_actions
        FROM users u
        LEFT JOIN product_events pe ON u.username = pe.username
        WHERE u.subscription_tier != 'super_admin'
        GROUP BY u.username
        HAVING last_active IS NULL OR last_active < datetime('now', ?)
    """, (f'-{days_threshold} days',)).fetchall()

    results = []
    for u in users:
        username = u['username']

        # Get modules used
        modules = conn.execute(
            """SELECT DISTINCT json_extract(metadata_json, '$.module')
               FROM product_events
               WHERE username=? AND event_type='module_action'""",
            (username,)
        ).fetchall()
        modules_used = [m[0] for m in modules if m[0]]
        all_modules = {"content_generator", "copy_editor", "social_assistant", "visual_audit"}
        modules_never = all_modules - set(modules_used)

        # Get onboarding steps completed
        steps = conn.execute(
            """SELECT json_extract(metadata_json, '$.step')
               FROM product_events
               WHERE username=? AND event_type='onboarding_step'""",
            (username,)
        ).fetchall()
        steps_done = [s[0] for s in steps if s[0]]

        # Get last calibration score from profiles
        org_id = conn.execute(
            "SELECT org_id FROM users WHERE username=?", (username,)
        ).fetchone()
        org = org_id['org_id'] if org_id and org_id['org_id'] else username
        profiles = conn.execute(
            "SELECT data FROM profiles WHERE org_id=? AND (is_sample_brand=0 OR is_sample_brand IS NULL)",
            (org,)
        ).fetchall()

        max_confidence = 0
        has_voice = False
        has_mh = False
        for p in profiles:
            try:
                d = json.loads(p[0]) if isinstance(p[0], str) else p[0]
                if isinstance(d, dict):
                    max_confidence = max(max_confidence, d.get('calibration_score', 0))
                    inp = d.get('inputs', {})
                    if len(inp.get('voice_dna', '')) > 20:
                        has_voice = True
                    if any(inp.get(k) for k in ['mh_brand_promise', 'mh_pillars_json']):
                        has_mh = True
            except (json.JSONDecodeError, TypeError):
                pass

        missing = []
        if not has_voice:
            missing.append("No voice samples")
        if not has_mh:
            missing.append("No message house")
        for m in sorted(modules_never):
            missing.append(f"Never tried {m.replace('_', ' ').title()}")

        results.append({
            "username": username,
            "last_active": u['last_active'] or "Never",
            "total_actions": u['total_actions'],
            "confidence": max_confidence,
            "missing": ", ".join(missing) if missing else "Complete",
        })

    conn.close()
    return results


def get_acquisition_sources():
    """Returns acquisition source breakdown."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT json_extract(metadata_json, '$.source') as source,
               COUNT(*) as count
        FROM product_events
        WHERE event_type = 'user_registered'
        GROUP BY source
        ORDER BY count DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_revenue_metrics():
    """Returns revenue and conversion metrics."""
    conn = sqlite3.connect(DB_NAME)

    # Count by tier
    tier_counts = {}
    rows = conn.execute(
        "SELECT subscription_tier, COUNT(*) FROM users "
        "WHERE subscription_tier != 'super_admin' GROUP BY subscription_tier"
    ).fetchall()
    for tier, count in rows:
        tier_counts[tier] = count

    # Count paying users (active status, non-free tiers)
    paying = conn.execute(
        "SELECT COUNT(*) FROM users WHERE subscription_status='active' "
        "AND subscription_tier IN ('solo', 'agency', 'enterprise')"
    ).fetchone()[0]

    total_non_admin = conn.execute(
        "SELECT COUNT(*) FROM users WHERE subscription_tier != 'super_admin'"
    ).fetchone()[0]

    # Avg days to conversion
    avg_days = conn.execute("""
        SELECT AVG(julianday(pe.timestamp) - julianday(u.created_at))
        FROM product_events pe
        JOIN users u ON pe.username = u.username
        WHERE pe.event_type = 'subscription_changed'
        AND json_extract(pe.metadata_json, '$.new_tier') IN ('solo', 'agency', 'enterprise')
    """).fetchone()[0]

    conn.close()
    return {
        "tier_counts": tier_counts,
        "paying_users": paying,
        "total_users": total_non_admin,
        "conversion_rate": round(paying / total_non_admin * 100, 1) if total_non_admin > 0 else 0,
        "avg_days_to_conversion": round(avg_days, 1) if avg_days else None,
    }


def get_product_events_csv():
    """Returns all product_events as CSV string for export."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM product_events ORDER BY timestamp DESC").fetchall()
    conn.close()

    if not rows:
        return "id,event_type,username,org_id,brand_id,metadata_json,session_id,timestamp\n"

    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(rows[0].keys())
    for row in rows:
        writer.writerow(tuple(row))
    return output.getvalue()


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
