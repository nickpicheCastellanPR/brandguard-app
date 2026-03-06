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
DATABASE_URL = os.environ.get("DATABASE_URL", "")

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


# ── Database abstraction helpers ──────────────────────────────────────────────

def is_postgres():
    """Returns True when DATABASE_URL is set (production Postgres)."""
    return bool(DATABASE_URL)


def _get_connection():
    """Return a DB connection — Postgres if DATABASE_URL is set, else SQLite."""
    if is_postgres():
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(DATABASE_URL)
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return conn
    else:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        return conn


def _q(sql):
    """Convert SQLite-style ? placeholders to Postgres-style %s."""
    if is_postgres():
        return sql.replace("?", "%s")
    return sql


def _dict_row(row):
    """Convert a row to a dict regardless of backend."""
    if row is None:
        return None
    if isinstance(row, dict):
        return row
    return dict(row)


def _fetchone_val(cursor, default=None):
    """Fetch first column of first row from cursor result."""
    row = cursor.fetchone()
    if row is None:
        return default
    if isinstance(row, dict):
        vals = list(row.values())
        return vals[0] if vals else default
    return row[0]


def _execute_plain(conn, sql, params=None):
    """Execute a query through the right cursor type."""
    if is_postgres():
        cur = conn.cursor()
        cur.execute(sql, params)
        return cur
    else:
        return conn.execute(sql, params) if params else conn.execute(sql)


# --- 1. SETUP & SCHEMA ---
def init_db():
    conn = _get_connection()
    try:
        if is_postgres():
            _init_db_postgres(conn)
        else:
            _init_db_sqlite(conn)
        conn.commit()
    finally:
        conn.close()

    run_migrations()


def _init_db_sqlite(conn):
    """Create core tables with SQLite syntax."""
    c = conn.cursor()

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

    c.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            org_id TEXT,
            username TEXT,
            timestamp TEXT,
            activity_type TEXT,
            asset_name TEXT,
            score INTEGER,
            verdict TEXT,
            metadata_json TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')


def _init_db_postgres(conn):
    """Create core tables with Postgres syntax."""
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT,
            password_hash TEXT,
            is_admin BOOLEAN DEFAULT FALSE,
            org_id TEXT,
            subscription_status TEXT DEFAULT 'trial',
            created_at TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            id SERIAL PRIMARY KEY,
            org_id TEXT,
            name TEXT,
            data TEXT,
            created_at TEXT,
            updated_by TEXT,
            UNIQUE(org_id, name)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS activity_log (
            id SERIAL PRIMARY KEY,
            org_id TEXT,
            username TEXT,
            timestamp TEXT,
            activity_type TEXT,
            asset_name TEXT,
            score INTEGER,
            verdict TEXT,
            metadata_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')


def run_migrations():
    """Apply schema migrations idempotently. Backs up DB on first run (SQLite only)."""
    conn = _get_connection()
    try:
        if is_postgres():
            _run_migrations_postgres(conn)
        else:
            _run_migrations_sqlite(conn)
        conn.commit()
    finally:
        conn.close()


def _get_existing_columns_pg(conn, table):
    """Get set of column names from a Postgres table."""
    cur = conn.cursor()
    cur.execute(
        "SELECT column_name FROM information_schema.columns WHERE table_name = %s",
        (table,)
    )
    rows = cur.fetchall()
    return {r['column_name'] if isinstance(r, dict) else r[0] for r in rows}


def _run_migrations_postgres(conn):
    """Postgres-compatible migrations."""
    cur = conn.cursor()
    user_columns = _get_existing_columns_pg(conn, 'users')

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
        ("is_beta_tester", "BOOLEAN DEFAULT FALSE"),
        ("is_suspended", "BOOLEAN DEFAULT FALSE"),
        ("suspended_at", "TIMESTAMP DEFAULT NULL"),
        ("suspended_reason", "TEXT DEFAULT NULL"),
        ("suspended_by", "TEXT DEFAULT NULL"),
        ("trial_start_date", "TIMESTAMP DEFAULT NULL"),
        ("trial_expired", "BOOLEAN DEFAULT FALSE"),
        ("renews_at", "TIMESTAMP DEFAULT NULL"),
        ("ends_at", "TIMESTAMP DEFAULT NULL"),
    ]
    for col_name, col_def in new_user_cols:
        if col_name not in user_columns:
            try:
                cur.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                conn.commit()
            except Exception:
                conn.rollback()

    # Create password_reset_tokens table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            token TEXT NOT NULL UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()

    # Add is_sample_brand to profiles
    profile_columns = _get_existing_columns_pg(conn, 'profiles')
    if 'is_sample_brand' not in profile_columns:
        try:
            cur.execute("ALTER TABLE profiles ADD COLUMN is_sample_brand BOOLEAN DEFAULT FALSE")
            conn.commit()
        except Exception:
            conn.rollback()

    # Create organizations table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS organizations (
            org_id TEXT PRIMARY KEY,
            org_name TEXT NOT NULL,
            subscription_tier TEXT NOT NULL DEFAULT 'agency',
            owner_username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create usage_tracking table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS usage_tracking (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            org_id TEXT,
            module TEXT NOT NULL,
            action_weight INTEGER DEFAULT 1,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            billing_month TEXT NOT NULL
        )
    ''')

    # Add columns to usage_tracking
    ut_columns = _get_existing_columns_pg(conn, 'usage_tracking')
    if 'is_impersonated' not in ut_columns:
        try:
            cur.execute("ALTER TABLE usage_tracking ADD COLUMN is_impersonated BOOLEAN DEFAULT FALSE")
            conn.commit()
        except Exception:
            conn.rollback()
    if 'action_detail' not in ut_columns:
        try:
            cur.execute("ALTER TABLE usage_tracking ADD COLUMN action_detail TEXT DEFAULT NULL")
            conn.commit()
        except Exception:
            conn.rollback()

    # Create admin_audit_log table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS admin_audit_log (
            id SERIAL PRIMARY KEY,
            admin_username TEXT NOT NULL,
            action_type TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create platform_settings table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS platform_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT
        )
    ''')

    # Create product_events table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS product_events (
            id SERIAL PRIMARY KEY,
            event_type TEXT NOT NULL,
            username TEXT NOT NULL,
            org_id TEXT,
            brand_id INTEGER,
            metadata_json TEXT,
            session_id TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    for idx_sql in [
        "CREATE INDEX IF NOT EXISTS idx_pe_type ON product_events(event_type)",
        "CREATE INDEX IF NOT EXISTS idx_pe_user ON product_events(username)",
        "CREATE INDEX IF NOT EXISTS idx_pe_session ON product_events(session_id)",
        "CREATE INDEX IF NOT EXISTS idx_pe_timestamp ON product_events(timestamp)",
    ]:
        try:
            cur.execute(idx_sql)
        except Exception:
            conn.rollback()

    conn.commit()


def _run_migrations_sqlite(conn):
    """SQLite-compatible migrations (original logic preserved)."""
    cursor = conn.execute("PRAGMA table_info(users)")
    user_columns = {row[1] if not isinstance(row, dict) else row['name'] for row in cursor.fetchall()}
    first_migration = 'subscription_tier' not in user_columns

    if first_migration and os.path.exists(DB_NAME):
        shutil.copy(DB_NAME, DB_NAME + ".bak")
        logging.info(f"DB backed up to {DB_NAME}.bak before first migration")

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
        ("trial_start_date", "TIMESTAMP DEFAULT NULL"),
        ("trial_expired", "BOOLEAN DEFAULT 0"),
        ("renews_at", "TIMESTAMP DEFAULT NULL"),
        ("ends_at", "TIMESTAMP DEFAULT NULL"),
    ]
    for col_name, col_def in new_user_cols:
        if col_name not in user_columns:
            try:
                conn.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
            except sqlite3.OperationalError:
                pass

    conn.execute('''
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            token TEXT NOT NULL UNIQUE,
            expires_at TIMESTAMP NOT NULL,
            used BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor = conn.execute("PRAGMA table_info(profiles)")
    profile_columns = {row[1] if not isinstance(row, dict) else row['name'] for row in cursor.fetchall()}
    if 'is_sample_brand' not in profile_columns:
        try:
            conn.execute("ALTER TABLE profiles ADD COLUMN is_sample_brand BOOLEAN DEFAULT 0")
        except sqlite3.OperationalError:
            pass

    conn.execute('''
        CREATE TABLE IF NOT EXISTS organizations (
            org_id TEXT PRIMARY KEY,
            org_name TEXT NOT NULL,
            subscription_tier TEXT NOT NULL DEFAULT 'agency',
            owner_username TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

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

    cursor = conn.execute("PRAGMA table_info(usage_tracking)")
    ut_columns = {row[1] if not isinstance(row, dict) else row['name'] for row in cursor.fetchall()}
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

    conn.execute('''
        CREATE TABLE IF NOT EXISTS platform_settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by TEXT
        )
    ''')

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

    # One-time data migration for existing users
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
        for row in users:
            uname = row[0] if not isinstance(row, dict) else row['username']
            old_status = row[1] if not isinstance(row, dict) else row['subscription_status']
            old_key = (old_status or 'trial').lower()
            tier, status = STATUS_MAP.get(old_key, ('solo', 'inactive'))
            conn.execute(
                "UPDATE users SET subscription_tier = ?, subscription_status = ? WHERE username = ?",
                (tier, status, uname)
            )
        conn.commit()
        logging.info(f"Migrated {len(users)} existing users to new tier/status schema")


# --- 2. AUTH & USER MANAGEMENT ---

def check_seat_availability(org_id):
    """Returns True if the Org has space for a new user."""
    conn = _get_connection()
    try:
        current_count = _fetchone_val(
            _execute_plain(conn, _q("SELECT COUNT(*) FROM users WHERE org_id = ?"), (org_id,)), 0)
        _admin_true = "TRUE" if is_postgres() else "1"
        result = _execute_plain(
            conn, _q(f"SELECT subscription_status FROM users WHERE org_id = ? AND is_admin = {_admin_true}"),
            (org_id,)).fetchone()
        status = "trial"
        if result:
            status = (result['subscription_status'] if isinstance(result, dict) else result[0]) or "trial"
        limit = SEAT_LIMITS.get(status.lower(), 1)
        return current_count < limit
    finally:
        conn.close()


def create_user(username, email, password, org_id=None, is_admin=False):
    """Creates a user. Enforces seat limits if adding to an existing Org."""
    hashed = ph.hash(password)

    if org_id:
        if not check_seat_availability(org_id):
            return False

    conn = _get_connection()
    try:
        _execute_plain(conn, _q('''
            INSERT INTO users (username, email, password_hash, org_id, is_admin, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        '''), (username, email, hashed, org_id, is_admin, datetime.now().isoformat()))
        conn.commit()
        return True
    except (sqlite3.IntegrityError if not is_postgres() else Exception) as e:
        if is_postgres():
            conn.rollback()
            err_str = str(e).lower()
            if 'unique' in err_str or 'duplicate' in err_str:
                return False
            raise
        return False
    finally:
        conn.close()


def check_login(username, password):
    conn = _get_connection()
    try:
        row = _execute_plain(
            conn, _q('SELECT password_hash, is_admin, subscription_status, email, org_id FROM users WHERE username = ?'),
            (username,)).fetchone()
        if row:
            if isinstance(row, dict):
                stored_hash = row['password_hash']
                try:
                    ph.verify(stored_hash, password)
                    return {
                        "username": username,
                        "is_admin": bool(row['is_admin']),
                        "status": row['subscription_status'],
                        "email": row['email'],
                        "org_id": row['org_id']
                    }
                except VerifyMismatchError:
                    return None
            else:
                stored_hash = row[0]
                try:
                    ph.verify(stored_hash, password)
                    return {
                        "username": username,
                        "is_admin": bool(row[1]),
                        "status": row[2],
                        "email": row[3],
                        "org_id": row[4]
                    }
                except VerifyMismatchError:
                    return None
        return None
    finally:
        conn.close()


def get_user_count():
    conn = _get_connection()
    try:
        return _fetchone_val(_execute_plain(conn, "SELECT COUNT(*) FROM users"), 0)
    except Exception:
        return 0
    finally:
        conn.close()


def get_users_by_org(org_id):
    """Returns list of users belonging to a specific Org."""
    conn = _get_connection()
    try:
        rows = _execute_plain(
            conn, _q("SELECT username, email, is_admin, created_at FROM users WHERE org_id = ?"),
            (org_id,)).fetchall()
        return rows
    finally:
        conn.close()


# --- 3. STUDIO PROFILE MANAGEMENT (Org-Based) ---
def save_profile(user_id, profile_name, profile_data):
    if not profile_name or not profile_name.strip():
        return False

    conn = _get_connection()
    try:
        org_id = _resolve_org_id(conn, user_id)
        data_json = json.dumps(profile_data)

        if is_postgres():
            _execute_plain(conn, '''
                INSERT INTO profiles (org_id, name, data, created_at, updated_by)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (org_id, name) DO UPDATE SET data = %s, updated_by = %s
            ''', (org_id, profile_name, data_json, datetime.now().isoformat(), user_id,
                  data_json, user_id))
        else:
            conn.execute('''
                INSERT OR REPLACE INTO profiles (org_id, name, data, created_at, updated_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (org_id, profile_name, data_json, datetime.now().isoformat(), user_id))

        conn.commit()
    finally:
        conn.close()


def get_profiles(username):
    conn = _get_connection()
    try:
        org_id = _resolve_org_id(conn, username)
        rows = _execute_plain(
            conn, _q("SELECT name, data FROM profiles WHERE org_id = ?"), (org_id,)).fetchall()

        profiles = {}
        for row in rows:
            try:
                name = row['name'] if isinstance(row, dict) else row[0]
                data = row['data'] if isinstance(row, dict) else row[1]
                profiles[name] = json.loads(data)
            except Exception:
                pass
        return profiles
    finally:
        conn.close()


def delete_profile(username, profile_name):
    conn = _get_connection()
    try:
        org_id = _resolve_org_id(conn, username)
        _execute_plain(conn, _q("DELETE FROM profiles WHERE org_id = ? AND name = ?"), (org_id, profile_name))
        conn.commit()
    finally:
        conn.close()


def _resolve_org_id(conn, username):
    """Internal helper — resolve org_id from username (fallback to username)."""
    row = _execute_plain(
        conn, _q("SELECT org_id FROM users WHERE username = ?"), (username,)).fetchone()
    if row:
        org = row['org_id'] if isinstance(row, dict) else row[0]
        return org if org else username
    return username


def load_sample_brand(username):
    """Load the Meridian Labs sample brand for a user/org. Returns True on success."""
    from sample_brand_data import SAMPLE_BRAND
    conn = _get_connection()
    try:
        org_id = _resolve_org_id(conn, username)
        profile_name = SAMPLE_BRAND["profile_name"]

        existing = _execute_plain(
            conn, _q("SELECT id FROM profiles WHERE org_id = ? AND name = ?"),
            (org_id, profile_name)).fetchone()
        if existing:
            return False

        data_json = json.dumps(SAMPLE_BRAND["profile_data"])
        _execute_plain(conn, _q('''
            INSERT INTO profiles (org_id, name, data, created_at, updated_by, is_sample_brand)
            VALUES (?, ?, ?, ?, ?, 1)
        '''), (org_id, profile_name, data_json, datetime.now().isoformat(), username))
        conn.commit()
        return True
    finally:
        conn.close()


def has_sample_brand(username):
    """Check if the user's org already has the sample brand loaded."""
    conn = _get_connection()
    try:
        org_id = _resolve_org_id(conn, username)
        _true_val = "TRUE" if is_postgres() else "1"
        result = _execute_plain(
            conn, _q(f"SELECT id FROM profiles WHERE org_id = ? AND is_sample_brand = {_true_val}"),
            (org_id,)).fetchone()
        return result is not None
    finally:
        conn.close()


def delete_sample_brand(username):
    """Remove the sample brand from a user's org."""
    conn = _get_connection()
    try:
        org_id = _resolve_org_id(conn, username)
        _true_val = "TRUE" if is_postgres() else "1"
        _execute_plain(
            conn, _q(f"DELETE FROM profiles WHERE org_id = ? AND is_sample_brand = {_true_val}"),
            (org_id,))
        conn.commit()
    finally:
        conn.close()


def get_brand_owner_info(username):
    """Returns (org_id, org_role, subscription_tier) for permission checks on brand deletion."""
    conn = _get_connection()
    try:
        row = _execute_plain(
            conn, _q("SELECT org_id, org_role, subscription_tier FROM users WHERE username = ?"),
            (username,)).fetchone()
        if not row:
            return None, 'member', 'solo'
        if isinstance(row, dict):
            return row['org_id'] or username, row['org_role'] or 'member', row['subscription_tier'] or 'solo'
        return row[0] or username, row[1] or 'member', row[2] or 'solo'
    finally:
        conn.close()


def is_profile_sample(username, profile_name):
    """Check whether a specific profile is a sample brand."""
    conn = _get_connection()
    try:
        org_id = _resolve_org_id(conn, username)
        result = _execute_plain(
            conn, _q("SELECT is_sample_brand FROM profiles WHERE org_id = ? AND name = ?"),
            (org_id, profile_name)).fetchone()
        if result:
            val = result['is_sample_brand'] if isinstance(result, dict) else result[0]
            return bool(val)
        return False
    finally:
        conn.close()


# --- 4. THE GOD VIEW (Rich Logging) ---
def log_event(org_id, username, activity_type, asset_name, score, verdict, metadata):
    """Logs an event to the persistent Studio timeline."""
    conn = _get_connection()
    try:
        meta_json = json.dumps(metadata, default=str)
        _execute_plain(conn, _q('''
            INSERT INTO activity_log (org_id, username, timestamp, activity_type, asset_name, score, verdict, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''), (org_id, username, datetime.now().strftime("%H:%M"), activity_type, asset_name, score, verdict, meta_json))
        conn.commit()
    finally:
        conn.close()


def get_org_logs(org_id, limit=20):
    """Fetches the timeline for the entire agency."""
    conn = _get_connection()
    try:
        rows = _execute_plain(conn, _q('''
            SELECT * FROM activity_log
            WHERE org_id = ?
            ORDER BY id DESC LIMIT ?
        '''), (org_id, limit)).fetchall()
        return [_dict_row(row) for row in rows]
    finally:
        conn.close()


# --- 5. SUBSCRIPTION ---
def update_user_status(username, new_status):
    conn = _get_connection()
    try:
        _execute_plain(conn, _q("UPDATE users SET subscription_status = ? WHERE username = ?"), (new_status, username))
        conn.commit()
    finally:
        conn.close()


def get_user_status(username):
    """Retrieves the subscription status for a given user."""
    conn = _get_connection()
    try:
        row = _execute_plain(
            conn, _q("SELECT subscription_status FROM users WHERE username = ?"), (username,)).fetchone()
        if row:
            return row['subscription_status'] if isinstance(row, dict) else row[0]
        return "trial"
    finally:
        conn.close()


# --- 6. TIER & USAGE (new) ---

def get_user_full(username):
    """Returns all user fields as a dict, or None if user not found."""
    conn = _get_connection()
    try:
        result = _execute_plain(
            conn, _q("SELECT * FROM users WHERE username = ?"), (username,)).fetchone()
        return _dict_row(result)
    finally:
        conn.close()


def set_user_subscription(username, tier, status, ls_sub_id=None, ls_variant_id=None):
    """Updates subscription_tier, subscription_status, LS fields, and last_subscription_sync."""
    conn = _get_connection()
    try:
        _execute_plain(conn, _q('''
            UPDATE users SET
                subscription_tier = ?,
                subscription_status = ?,
                lemon_squeezy_subscription_id = ?,
                lemon_squeezy_variant_id = ?,
                last_subscription_sync = ?
            WHERE username = ?
        '''), (tier, status, ls_sub_id, ls_variant_id, datetime.now().isoformat(), username))
        conn.commit()
    finally:
        conn.close()


def get_org_tier(org_id):
    """Returns the subscription_tier for an org."""
    conn = _get_connection()
    try:
        row = _execute_plain(
            conn, _q("SELECT subscription_tier FROM organizations WHERE org_id = ?"), (org_id,)).fetchone()
        if row:
            return row['subscription_tier'] if isinstance(row, dict) else row[0]
        _admin_true = "TRUE" if is_postgres() else "1"
        result = _execute_plain(
            conn, _q(f"SELECT subscription_tier FROM users WHERE org_id = ? AND is_admin = {_admin_true}"),
            (org_id,)).fetchone()
        if result:
            return result['subscription_tier'] if isinstance(result, dict) else result[0]
        return 'solo'
    finally:
        conn.close()


def count_user_brands(org_id, exclude_sample=True):
    """Count profiles belonging to an org, optionally excluding sample brands."""
    conn = _get_connection()
    try:
        if exclude_sample:
            _false_val = "FALSE" if is_postgres() else "0"
            count = _fetchone_val(_execute_plain(
                conn, _q(f"SELECT COUNT(*) FROM profiles WHERE org_id = ? AND (is_sample_brand = {_false_val} OR is_sample_brand IS NULL)"),
                (org_id,)), 0)
        else:
            count = _fetchone_val(_execute_plain(
                conn, _q("SELECT COUNT(*) FROM profiles WHERE org_id = ?"), (org_id,)), 0)
        return count
    finally:
        conn.close()


def record_usage_action(username, org_id, module, action_weight, billing_month, action_detail=None):
    """Records an AI action in the usage_tracking table."""
    conn = _get_connection()
    try:
        _execute_plain(conn, _q('''
            INSERT INTO usage_tracking (username, org_id, module, action_weight, billing_month, action_detail)
            VALUES (?, ?, ?, ?, ?, ?)
        '''), (username, org_id, module, action_weight, billing_month, action_detail))
        conn.commit()
    finally:
        conn.close()


def get_monthly_usage(org_id, billing_month):
    """Returns total action_weight for an org in a billing month (agency/enterprise)."""
    conn = _get_connection()
    try:
        return _fetchone_val(_execute_plain(
            conn, _q("SELECT COALESCE(SUM(action_weight), 0) FROM usage_tracking WHERE org_id = ? AND billing_month = ?"),
            (org_id, billing_month)), 0)
    finally:
        conn.close()


def get_monthly_usage_user(username, billing_month):
    """Returns total action_weight for a solo user in a billing month."""
    conn = _get_connection()
    try:
        return _fetchone_val(_execute_plain(
            conn, _q("SELECT COALESCE(SUM(action_weight), 0) FROM usage_tracking WHERE username = ? AND billing_month = ?"),
            (username, billing_month)), 0)
    finally:
        conn.close()


def create_organization(org_id, org_name, tier, owner_username):
    """Creates a new organization record. Returns True on success, False if org_id already exists."""
    conn = _get_connection()
    try:
        _execute_plain(conn, _q('''
            INSERT INTO organizations (org_id, org_name, subscription_tier, owner_username)
            VALUES (?, ?, ?, ?)
        '''), (org_id, org_name, tier, owner_username))
        conn.commit()
        return True
    except (sqlite3.IntegrityError if not is_postgres() else Exception) as e:
        if is_postgres():
            conn.rollback()
            err_str = str(e).lower()
            if 'unique' in err_str or 'duplicate' in err_str:
                return False
            raise
        return False
    finally:
        conn.close()


def get_organization(org_id):
    """Returns an organization record as a dict, or None."""
    conn = _get_connection()
    try:
        result = _execute_plain(
            conn, _q("SELECT * FROM organizations WHERE org_id = ?"), (org_id,)).fetchone()
        return _dict_row(result)
    finally:
        conn.close()


def remove_org_member(username):
    """Removes a user from their org (sets org_id=NULL, org_role='member')."""
    conn = _get_connection()
    try:
        _execute_plain(
            conn, _q("UPDATE users SET org_id = NULL, org_role = 'member' WHERE username = ?"),
            (username,))
        conn.commit()
    finally:
        conn.close()


# --- 7. ADMIN PANEL (new) ---

def log_admin_action(admin_username, action_type, target_type, target_id, details=None):
    """Writes an entry to admin_audit_log."""
    conn = _get_connection()
    try:
        details_json = json.dumps(details, default=str) if details else None
        _execute_plain(conn, _q('''
            INSERT INTO admin_audit_log (admin_username, action_type, target_type, target_id, details)
            VALUES (?, ?, ?, ?, ?)
        '''), (admin_username, action_type, target_type, target_id, details_json))
        conn.commit()
    finally:
        conn.close()


def get_admin_audit_log(limit=200, action_type=None, target_type=None, admin_username=None):
    """Returns admin audit log entries as list of dicts."""
    conn = _get_connection()
    try:
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
        rows = _execute_plain(conn, _q(query), params).fetchall()
        return [_dict_row(row) for row in rows]
    finally:
        conn.close()


def get_all_users_full():
    """Returns all users as a list of dicts."""
    conn = _get_connection()
    try:
        rows = _execute_plain(conn, "SELECT * FROM users ORDER BY created_at DESC").fetchall()
        return [_dict_row(row) for row in rows]
    finally:
        conn.close()


def get_all_organizations():
    """Returns all organizations as a list of dicts."""
    conn = _get_connection()
    try:
        rows = _execute_plain(conn, "SELECT * FROM organizations ORDER BY created_at DESC").fetchall()
        return [_dict_row(row) for row in rows]
    finally:
        conn.close()


def update_user_fields(username, **fields):
    """Update arbitrary fields on a user record. Returns True on success."""
    if not fields:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [username]
    conn = _get_connection()
    try:
        _execute_plain(conn, _q(f"UPDATE users SET {set_clause} WHERE username = ?"), values)
        conn.commit()
        return True
    finally:
        conn.close()


def reset_user_password(username, new_password):
    """Reset a user's password. Returns True on success."""
    hashed = ph.hash(new_password)
    conn = _get_connection()
    try:
        _execute_plain(conn, _q("UPDATE users SET password_hash = ? WHERE username = ?"), (hashed, username))
        conn.commit()
        return True
    finally:
        conn.close()


# ── Password Reset Tokens ────────────────────────────────────────────────────

def create_reset_token(username):
    """Create a password reset token (1-hour expiry). Returns token string."""
    import secrets
    from datetime import timedelta
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.now() + timedelta(hours=1)).isoformat()
    conn = _get_connection()
    try:
        # Invalidate any existing unused tokens for this user
        _used_true = "TRUE" if is_postgres() else "1"
        _used_false = "FALSE" if is_postgres() else "0"
        _execute_plain(conn, _q(
            f"UPDATE password_reset_tokens SET used = {_used_true} WHERE username = ? AND used = {_used_false}"
        ), (username,))
        _execute_plain(conn, _q(
            "INSERT INTO password_reset_tokens (username, token, expires_at) VALUES (?, ?, ?)"
        ), (username, token, expires_at))
        conn.commit()
        return token
    finally:
        conn.close()


def validate_reset_token(token):
    """Check if a reset token is valid. Returns username or None."""
    conn = _get_connection()
    try:
        _used_false = "FALSE" if is_postgres() else "0"
        row = _execute_plain(conn, _q(
            f"SELECT username, expires_at FROM password_reset_tokens WHERE token = ? AND used = {_used_false}"
        ), (token,)).fetchone()
        if not row:
            return None
        username = row['username'] if isinstance(row, dict) else row[0]
        expires_at_str = row['expires_at'] if isinstance(row, dict) else row[1]
        try:
            expires_at = datetime.fromisoformat(str(expires_at_str).replace('Z', ''))
            if datetime.now() > expires_at:
                return None
        except (ValueError, TypeError):
            return None
        return username
    finally:
        conn.close()


def consume_reset_token(token):
    """Mark a reset token as used. Returns True on success."""
    conn = _get_connection()
    try:
        _used_true = "TRUE" if is_postgres() else "1"
        _execute_plain(conn, _q(
            f"UPDATE password_reset_tokens SET used = {_used_true} WHERE token = ?"
        ), (token,))
        conn.commit()
        return True
    finally:
        conn.close()


# ── Trial Management ─────────────────────────────────────────────────────────

def set_trial_start(username):
    """Set the trial start date for a new user."""
    conn = _get_connection()
    try:
        _execute_plain(conn, _q(
            "UPDATE users SET trial_start_date = ?, subscription_status = 'active' WHERE username = ?"
        ), (datetime.now().isoformat(), username))
        conn.commit()
    finally:
        conn.close()


def get_trial_info(username):
    """Returns dict with trial_start_date, trial_expired, days_remaining."""
    conn = _get_connection()
    try:
        row = _execute_plain(conn, _q(
            "SELECT trial_start_date, trial_expired FROM users WHERE username = ?"
        ), (username,)).fetchone()
        if not row:
            return None
        tsd = row['trial_start_date'] if isinstance(row, dict) else row[0]
        te = row['trial_expired'] if isinstance(row, dict) else row[1]
        if not tsd:
            return {"trial_start_date": None, "trial_expired": bool(te), "days_remaining": 0}
        try:
            start = datetime.fromisoformat(str(tsd).replace('Z', ''))
            elapsed = (datetime.now() - start).days
            remaining = max(0, 14 - elapsed)
            return {
                "trial_start_date": str(tsd),
                "trial_expired": bool(te) or remaining <= 0,
                "days_remaining": remaining,
            }
        except (ValueError, TypeError):
            return {"trial_start_date": None, "trial_expired": bool(te), "days_remaining": 0}
    finally:
        conn.close()


def expire_trial(username):
    """Mark a user's trial as expired."""
    _used_true = "TRUE" if is_postgres() else "1"
    conn = _get_connection()
    try:
        _execute_plain(conn, _q(
            f"UPDATE users SET trial_expired = {_used_true}, subscription_status = 'inactive' WHERE username = ?"
        ), (username,))
        conn.commit()
    finally:
        conn.close()


def get_user_by_email(email):
    """Look up a username by email address. Returns username or None."""
    conn = _get_connection()
    try:
        row = _execute_plain(
            conn, _q("SELECT username FROM users WHERE email = ?"), (email,)).fetchone()
        if row:
            return row['username'] if isinstance(row, dict) else row[0]
        return None
    finally:
        conn.close()


def suspend_user(username, reason, admin_username):
    """Suspend a user account. Returns True on success, False if target is super_admin."""
    conn = _get_connection()
    try:
        row = _execute_plain(
            conn, _q("SELECT subscription_tier FROM users WHERE username = ?"), (username,)).fetchone()
        tier = None
        if row:
            tier = row['subscription_tier'] if isinstance(row, dict) else row[0]
        if tier == "super_admin":
            return False
        _suspended_true = "TRUE" if is_postgres() else "1"
        _execute_plain(conn, _q(
            f"UPDATE users SET is_suspended = {_suspended_true}, suspended_at = ?, suspended_reason = ?, suspended_by = ? WHERE username = ?"),
            (datetime.now().isoformat(), reason, admin_username, username))
        conn.commit()
        return True
    finally:
        conn.close()


def unsuspend_user(username):
    """Unsuspend a user account. Returns True on success."""
    conn = _get_connection()
    try:
        _suspended_false = "FALSE" if is_postgres() else "0"
        _execute_plain(conn, _q(
            f"UPDATE users SET is_suspended = {_suspended_false}, suspended_at = NULL, suspended_reason = NULL, suspended_by = NULL WHERE username = ?"),
            (username,))
        conn.commit()
        return True
    finally:
        conn.close()


def is_user_suspended(username):
    """Check if a user is suspended. Returns (is_suspended, reason) tuple."""
    conn = _get_connection()
    try:
        result = _execute_plain(
            conn, _q("SELECT is_suspended, suspended_reason FROM users WHERE username = ?"),
            (username,)).fetchone()
        if result:
            if isinstance(result, dict):
                return bool(result['is_suspended']), result['suspended_reason']
            return bool(result[0]), result[1]
        return False, None
    finally:
        conn.close()


def get_daily_usage_platform(billing_month):
    """Returns daily usage across all users for platform-level analytics."""
    conn = _get_connection()
    try:
        if is_postgres():
            rows = _execute_plain(conn, '''
                SELECT DATE(timestamp)::text as day, SUM(action_weight) as actions
                FROM usage_tracking
                WHERE billing_month = %s
                GROUP BY DATE(timestamp)
                ORDER BY DATE(timestamp)
            ''', (billing_month,)).fetchall()
        else:
            rows = _execute_plain(conn, '''
                SELECT DATE(timestamp) as day, SUM(action_weight) as actions
                FROM usage_tracking
                WHERE billing_month = ?
                GROUP BY DATE(timestamp)
                ORDER BY DATE(timestamp)
            ''', (billing_month,)).fetchall()
        return [_dict_row(row) for row in rows]
    finally:
        conn.close()


def update_organization_fields(org_id, **fields):
    """Update arbitrary fields on an organization record."""
    if not fields:
        return False
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [org_id]
    conn = _get_connection()
    try:
        _execute_plain(conn, _q(f"UPDATE organizations SET {set_clause} WHERE org_id = ?"), values)
        conn.commit()
        return True
    finally:
        conn.close()


def delete_user_full(username):
    """Deletes a user and cleans up related data. Returns summary dict."""
    conn = _get_connection()
    try:
        row = _execute_plain(
            conn, _q("SELECT org_id, subscription_tier FROM users WHERE username = ?"), (username,)).fetchone()
        if not row:
            return {"deleted": False, "reason": "User not found"}

        if isinstance(row, dict):
            org_id, tier = row['org_id'], row['subscription_tier']
        else:
            org_id, tier = row[0], row[1]

        if tier == 'super_admin':
            return {"deleted": False, "reason": "Cannot delete super_admin accounts through UI"}

        if org_id:
            org = _execute_plain(
                conn, _q("SELECT owner_username FROM organizations WHERE org_id = ?"), (org_id,)).fetchone()
            _execute_plain(
                conn, _q("UPDATE users SET org_id = NULL, org_role = 'member' WHERE username = ?"), (username,))
        else:
            _execute_plain(conn, _q("DELETE FROM profiles WHERE org_id = ?"), (username,))

        _execute_plain(conn, _q("DELETE FROM usage_tracking WHERE username = ?"), (username,))
        _execute_plain(conn, _q("DELETE FROM users WHERE username = ?"), (username,))
        conn.commit()
        return {"deleted": True, "reason": "OK", "org_cleaned": org_id}
    finally:
        conn.close()


def delete_organization_full(org_id):
    """Deletes an org, disassociates members, reassigns brands to owner."""
    conn = _get_connection()
    try:
        org = _execute_plain(
            conn, _q("SELECT owner_username FROM organizations WHERE org_id = ?"), (org_id,)).fetchone()
        if not org:
            return {"deleted": False, "reason": "Org not found"}

        owner = org['owner_username'] if isinstance(org, dict) else org[0]
        member_count = _fetchone_val(
            _execute_plain(conn, _q("SELECT COUNT(*) FROM users WHERE org_id = ?"), (org_id,)), 0)

        _execute_plain(conn, _q("UPDATE profiles SET org_id = ? WHERE org_id = ?"), (owner, org_id))
        _execute_plain(conn, _q("UPDATE users SET org_id = NULL, org_role = 'member' WHERE org_id = ?"), (org_id,))
        _execute_plain(conn, _q("DELETE FROM organizations WHERE org_id = ?"), (org_id,))
        conn.commit()
        return {"deleted": True, "member_count": member_count, "brands_reassigned_to": owner}
    finally:
        conn.close()


def get_platform_setting(key):
    """Returns a platform setting value, or None."""
    conn = _get_connection()
    try:
        result = _execute_plain(
            conn, _q("SELECT value FROM platform_settings WHERE key = ?"), (key,)).fetchone()
        if result:
            return result['value'] if isinstance(result, dict) else result[0]
        return None
    finally:
        conn.close()


def set_platform_setting(key, value, updated_by="system"):
    """Sets a platform setting (upsert)."""
    conn = _get_connection()
    try:
        now = datetime.now().isoformat()
        if is_postgres():
            _execute_plain(conn, '''
                INSERT INTO platform_settings (key, value, updated_at, updated_by)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT(key) DO UPDATE SET value = %s, updated_at = %s, updated_by = %s
            ''', (key, value, now, updated_by, value, now, updated_by))
        else:
            conn.execute('''
                INSERT INTO platform_settings (key, value, updated_at, updated_by)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = ?, updated_at = ?, updated_by = ?
            ''', (key, value, now, updated_by, value, now, updated_by))
        conn.commit()
    finally:
        conn.close()


def get_usage_analytics(billing_month=None):
    """Returns per-user usage summary for the admin analytics dashboard."""
    if not billing_month:
        billing_month = datetime.now().strftime("%Y-%m")
    conn = _get_connection()
    try:
        prev_bm = _prev_month(billing_month)
        if is_postgres():
            rows = _execute_plain(conn, '''
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
                    WHERE billing_month = %s AND (is_impersonated = FALSE OR is_impersonated IS NULL)
                    GROUP BY username
                ) curr ON u.username = curr.username
                LEFT JOIN (
                    SELECT username, SUM(action_weight) as total_actions
                    FROM usage_tracking
                    WHERE billing_month = %s
                    GROUP BY username
                ) prev ON u.username = prev.username
                ORDER BY COALESCE(curr.total_actions, 0) DESC
            ''', (billing_month, prev_bm)).fetchall()
        else:
            rows = _execute_plain(conn, '''
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
                    WHERE billing_month = ? AND (is_impersonated = {"FALSE" if is_postgres() else "0"} OR is_impersonated IS NULL)
                    GROUP BY username
                ) curr ON u.username = curr.username
                LEFT JOIN (
                    SELECT username, SUM(action_weight) as total_actions
                    FROM usage_tracking
                    WHERE billing_month = ?
                    GROUP BY username
                ) prev ON u.username = prev.username
                ORDER BY COALESCE(curr.total_actions, 0) DESC
            ''', (billing_month, prev_bm)).fetchall()
        return [_dict_row(row) for row in rows]
    finally:
        conn.close()


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
    conn = _get_connection()
    try:
        return _fetchone_val(_execute_plain(
            conn, _q("SELECT COALESCE(SUM(action_weight), 0) FROM usage_tracking WHERE billing_month = ?"),
            (billing_month,)), 0)
    finally:
        conn.close()


def get_monthly_usage_trend(months=6):
    """Returns list of (billing_month, total_actions) for the last N months."""
    conn = _get_connection()
    try:
        now = datetime.now()
        results = []
        for i in range(months - 1, -1, -1):
            y = now.year
            m = now.month - i
            while m <= 0:
                m += 12
                y -= 1
            bm = f"{y}-{m:02d}"
            total = _fetchone_val(_execute_plain(
                conn, _q("SELECT COALESCE(SUM(action_weight), 0) FROM usage_tracking WHERE billing_month = ?"),
                (bm,)), 0)
            results.append({"month": bm, "actions": total})
        return results
    finally:
        conn.close()


def record_usage_action_impersonated(username, org_id, module, action_weight, billing_month, action_detail=None):
    """Records an AI action flagged as impersonated (does not count toward soft cap)."""
    conn = _get_connection()
    try:
        _execute_plain(conn, _q('''
            INSERT INTO usage_tracking (username, org_id, module, action_weight, billing_month, is_impersonated, action_detail)
            VALUES (?, ?, ?, ?, ?, {"TRUE" if is_postgres() else "1"}, ?)
        '''), (username, org_id, module, action_weight, billing_month, action_detail))
        conn.commit()
    finally:
        conn.close()


def update_last_login(username):
    """Updates last_login to now for a user."""
    conn = _get_connection()
    try:
        _execute_plain(conn, _q("UPDATE users SET last_login = ? WHERE username = ?"),
                       (datetime.now().isoformat(), username))
        conn.commit()
    finally:
        conn.close()


def get_table_row_counts():
    """Returns dict of table_name -> row_count for admin health check."""
    conn = _get_connection()
    try:
        tables = ['users', 'profiles', 'usage_tracking', 'organizations',
                  'activity_log', 'admin_audit_log', 'platform_settings', 'product_events']
        counts = {}
        for t in tables:
            try:
                counts[t] = _fetchone_val(_execute_plain(conn, f"SELECT COUNT(*) FROM {t}"), 0)
            except Exception:
                counts[t] = 0
                if is_postgres():
                    conn.rollback()
        return counts
    finally:
        conn.close()


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
        conn = _get_connection()
        try:
            _execute_plain(conn, _q(
                """INSERT INTO product_events
                   (event_type, username, org_id, brand_id, metadata_json, session_id)
                   VALUES (?, ?, ?, ?, ?, ?)"""),
                (event_type, username, org_id, brand_id,
                 json.dumps(metadata) if metadata else None,
                 session_id))
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logging.warning(f"Event tracking failed ({event_type}): {e}")


def check_milestone(username, step_name, session_id=None, org_id=None):
    """Fire onboarding milestone only if not already recorded for this user."""
    try:
        conn = _get_connection()
        try:
            like_query = "SELECT 1 FROM product_events WHERE event_type='onboarding_step' AND username=? AND metadata_json LIKE ?"
            if is_postgres():
                like_query = like_query.replace("LIKE", "ILIKE")
            existing = _execute_plain(
                conn, _q(like_query),
                (username, f'%"{step_name}"%')).fetchone()
            if not existing:
                _execute_plain(conn, _q(
                    """INSERT INTO product_events
                       (event_type, username, org_id, metadata_json, session_id)
                       VALUES (?, ?, ?, ?, ?)"""),
                    ("onboarding_step", username, org_id,
                     json.dumps({"step": step_name}), session_id))
                conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


# ── Analytics query functions ─────────────────────────────────────────────────

def _datetime_offset(days):
    """Returns a date offset expression for the current backend."""
    if is_postgres():
        return f"NOW() - INTERVAL '{days} days'"
    return f"datetime('now', '-{days} days')"


def get_active_users(days=7):
    """Returns count of users with at least 1 module_action in last N days."""
    conn = _get_connection()
    try:
        sql = f"""SELECT COUNT(DISTINCT username) FROM product_events
                  WHERE event_type='module_action'
                  AND timestamp >= {_datetime_offset(days)}"""
        return _fetchone_val(_execute_plain(conn, sql), 0)
    finally:
        conn.close()


def get_user_sessions_per_week(days=28):
    """Returns avg sessions per active user per week over last N days."""
    conn = _get_connection()
    try:
        sql = f"""SELECT username, COUNT(DISTINCT session_id) as sessions
                  FROM product_events
                  WHERE event_type='session_start'
                  AND timestamp >= {_datetime_offset(days)}
                  GROUP BY username"""
        rows = _execute_plain(conn, sql).fetchall()
        if not rows:
            return 0.0
        weeks = max(days / 7, 1)
        total_sessions = sum(
            (r['sessions'] if isinstance(r, dict) else r[1]) for r in rows)
        return round(total_sessions / len(rows) / weeks, 1)
    finally:
        conn.close()


def get_user_return_table():
    """Returns per-user retention data for the return table."""
    conn = _get_connection()
    try:
        if is_postgres():
            sql = """
                SELECT
                    u.username,
                    u.created_at as signed_up,
                    u.subscription_tier,
                    MAX(pe.timestamp) as last_active,
                    COUNT(DISTINCT CASE WHEN pe.event_type='module_action' THEN pe.id END) as total_actions,
                    COUNT(DISTINCT EXTRACT(WEEK FROM pe.timestamp::timestamp)) as weeks_active
                FROM users u
                LEFT JOIN product_events pe ON u.username = pe.username
                    AND pe.event_type = 'module_action'
                WHERE u.subscription_tier != 'super_admin'
                GROUP BY u.username, u.created_at, u.subscription_tier
                ORDER BY MAX(pe.timestamp) DESC NULLS LAST
            """
        else:
            sql = """
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
            """
        rows = _execute_plain(conn, sql).fetchall()
        return [_dict_row(r) for r in rows]
    finally:
        conn.close()


def _json_extract(field, json_key):
    """Return the correct JSON extraction expression for the backend."""
    if is_postgres():
        return f"{field}::json->>'{json_key}'"
    return f"json_extract({field}, '$.{json_key}')"


def get_module_engagement():
    """Returns module engagement data for the analytics dashboard."""
    conn = _get_connection()
    try:
        mod = _json_extract('metadata_json', 'module')
        sql = f"""
            SELECT
                {mod} as module,
                COUNT(*) as total_actions,
                COUNT(DISTINCT username) as unique_users
            FROM product_events
            WHERE event_type = 'module_action'
            AND {mod} IS NOT NULL
            GROUP BY {mod}
            ORDER BY total_actions DESC
        """
        rows = _execute_plain(conn, sql).fetchall()
        return [_dict_row(r) for r in rows]
    finally:
        conn.close()


def get_module_engagement_week(weeks_ago=0):
    """Returns module action counts for a specific week."""
    conn = _get_connection()
    try:
        mod = _json_extract('metadata_json', 'module')
        start_days = (weeks_ago + 1) * 7
        end_days = weeks_ago * 7
        if is_postgres():
            sql = f"""
                SELECT {mod} as module, COUNT(*) as actions
                FROM product_events
                WHERE event_type = 'module_action'
                AND timestamp >= NOW() - INTERVAL '{start_days} days'
                AND timestamp < NOW() - INTERVAL '{end_days} days'
                GROUP BY {mod}
            """
        else:
            sql = f"""
                SELECT {mod} as module, COUNT(*) as actions
                FROM product_events
                WHERE event_type = 'module_action'
                AND timestamp >= datetime('now', '-{start_days} days')
                AND timestamp < datetime('now', '-{end_days} days')
                GROUP BY {mod}
            """
        rows = _execute_plain(conn, sql).fetchall()
        result = {}
        for r in rows:
            if isinstance(r, dict):
                result[r['module']] = r['actions']
            else:
                result[r[0]] = r[1]
        return result
    finally:
        conn.close()


def get_session_action_distribution():
    """Returns distribution of actions per session."""
    conn = _get_connection()
    try:
        rows = _execute_plain(conn, """
            SELECT session_id, COUNT(*) as actions
            FROM product_events
            WHERE event_type = 'module_action'
            AND session_id IS NOT NULL
            GROUP BY session_id
        """).fetchall()

        total_sessions = _fetchone_val(_execute_plain(
            conn, "SELECT COUNT(DISTINCT session_id) FROM product_events WHERE event_type='session_start'"
        ), 0)

        action_sessions = len(rows)
        zero_sessions = max(total_sessions - action_sessions, 0)

        buckets = {"0": zero_sessions, "1": 0, "2-3": 0, "4+": 0}
        for r in rows:
            count = r['actions'] if isinstance(r, dict) else r[1]
            if count == 1:
                buckets["1"] += 1
            elif count <= 3:
                buckets["2-3"] += 1
            else:
                buckets["4+"] += 1

        return buckets, total_sessions
    finally:
        conn.close()


def get_api_costs(days=30):
    """Returns API cost data for the last N days."""
    conn = _get_connection()
    try:
        cost_field = _json_extract('metadata_json', 'estimated_cost_usd')
        mod_field = _json_extract('metadata_json', 'module')
        offset = _datetime_offset(days)

        if is_postgres():
            date_expr = "DATE(timestamp)::text"
        else:
            date_expr = "DATE(timestamp)"

        total = _execute_plain(conn, f"""
            SELECT COALESCE(SUM(CAST({cost_field} AS FLOAT)), 0) as total_cost,
                   COUNT(*) as total_actions
            FROM product_events
            WHERE event_type = 'api_cost'
            AND timestamp >= {offset}
        """).fetchone()

        per_module = _execute_plain(conn, f"""
            SELECT {mod_field} as module,
                   SUM(CAST({cost_field} AS FLOAT)) as cost,
                   COUNT(*) as actions
            FROM product_events
            WHERE event_type = 'api_cost'
            AND timestamp >= {offset}
            GROUP BY {mod_field}
            ORDER BY cost DESC
        """).fetchall()

        daily = _execute_plain(conn, f"""
            SELECT {date_expr} as day,
                   SUM(CAST({cost_field} AS FLOAT)) as cost
            FROM product_events
            WHERE event_type = 'api_cost'
            AND timestamp >= {offset}
            GROUP BY {date_expr}
            ORDER BY {date_expr}
        """).fetchall()

        total_row = _dict_row(total) if total else {}
        return {
            "total_cost": total_row.get('total_cost', 0) or 0,
            "total_actions": total_row.get('total_actions', 0) or 0,
            "per_module": [_dict_row(r) for r in per_module],
            "daily": [_dict_row(r) for r in daily],
        }
    finally:
        conn.close()


def get_active_user_count(days=30):
    """Returns count of distinct active users (with module_action) in last N days."""
    conn = _get_connection()
    try:
        sql = f"""SELECT COUNT(DISTINCT username) FROM product_events
                  WHERE event_type='module_action'
                  AND timestamp >= {_datetime_offset(days)}"""
        return _fetchone_val(_execute_plain(conn, sql), 0)
    finally:
        conn.close()


def get_calibration_distribution():
    """Returns calibration score distribution across all non-sample brands."""
    conn = _get_connection()
    try:
        _false_val = "FALSE" if is_postgres() else "0"
        rows = _execute_plain(conn, f"""
            SELECT data FROM profiles
            WHERE is_sample_brand = {_false_val} OR is_sample_brand IS NULL
        """).fetchall()

        buckets = {"0-25": 0, "26-50": 0, "51-75": 0, "76-100": 0}
        scores = []
        for row in rows:
            try:
                raw = row['data'] if isinstance(row, dict) else row[0]
                data = json.loads(raw) if isinstance(raw, str) else raw
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
    finally:
        conn.close()


def get_avg_calibration_trend(weeks=8):
    """Returns weekly average calibration score from calibration_change events."""
    conn = _get_connection()
    try:
        new_score = _json_extract('metadata_json', 'new_score')
        days = weeks * 7
        if is_postgres():
            sql = f"""
                SELECT TO_CHAR(timestamp::timestamp, 'IYYY-"W"IW') as week,
                       AVG(CAST({new_score} AS FLOAT)) as avg_score
                FROM product_events
                WHERE event_type = 'calibration_change'
                AND timestamp >= NOW() - INTERVAL '{days} days'
                GROUP BY week
                ORDER BY week
            """
        else:
            sql = f"""
                SELECT strftime('%Y-W%W', timestamp) as week,
                       AVG({new_score}) as avg_score
                FROM product_events
                WHERE event_type = 'calibration_change'
                AND timestamp >= datetime('now', '-{days} days')
                GROUP BY week
                ORDER BY week
            """
        rows = _execute_plain(conn, sql).fetchall()
        return [_dict_row(r) for r in rows]
    finally:
        conn.close()


def get_profile_completion_stats():
    """Returns profile completion breakdown across all non-sample brands."""
    conn = _get_connection()
    try:
        _false_val = "FALSE" if is_postgres() else "0"
        rows = _execute_plain(conn, f"""
            SELECT data FROM profiles
            WHERE is_sample_brand = {_false_val} OR is_sample_brand IS NULL
        """).fetchall()

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
                raw = row['data'] if isinstance(row, dict) else row[0]
                data = json.loads(raw) if isinstance(raw, str) else raw
                if not isinstance(data, dict):
                    continue
                inputs = data.get('inputs', {})

                strat_count = sum(1 for k in ['wiz_name', 'wiz_mission', 'wiz_values', 'wiz_archetype']
                                  if inputs.get(k))
                if strat_count >= 3:
                    stats["strategy_fields"] += 1

                if len(inputs.get('voice_dna', '')) > 20 or '[ASSET:' in inputs.get('voice_dna', ''):
                    stats["voice_samples"] += 1
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
    finally:
        conn.close()


def get_onboarding_funnel():
    """Returns onboarding funnel data."""
    conn = _get_connection()
    try:
        total_users = _fetchone_val(_execute_plain(
            conn, "SELECT COUNT(*) FROM users WHERE subscription_tier != 'super_admin'"), 0)

        steps = [
            "account_created", "first_brand_created", "first_voice_sample",
            "first_module_run", "message_house_started",
            "calibration_crossed_60", "calibration_crossed_90"
        ]
        funnel = {}
        like_kw = "ILIKE" if is_postgres() else "LIKE"
        for step in steps:
            count = _fetchone_val(_execute_plain(
                conn, _q(f"SELECT COUNT(DISTINCT username) FROM product_events "
                         f"WHERE event_type='onboarding_step' AND metadata_json {like_kw} ?"),
                (f'%"{step}"%',)), 0)
            funnel[step] = count

        return funnel, total_users
    finally:
        conn.close()


def get_inactive_user_diagnostics(days_threshold=14):
    """Returns diagnostics for users inactive for N+ days."""
    conn = _get_connection()
    try:
        offset = _datetime_offset(days_threshold)
        mod_field = _json_extract('metadata_json', 'module')
        step_field = _json_extract('metadata_json', 'step')

        if is_postgres():
            sql = f"""
                SELECT u.username, u.created_at,
                    MAX(pe.timestamp) as last_active,
                    COUNT(DISTINCT CASE WHEN pe.event_type='module_action' THEN pe.id END) as total_actions
                FROM users u
                LEFT JOIN product_events pe ON u.username = pe.username
                WHERE u.subscription_tier != 'super_admin'
                GROUP BY u.username, u.created_at
                HAVING MAX(pe.timestamp) IS NULL OR MAX(pe.timestamp) < {offset}
            """
        else:
            sql = f"""
                SELECT u.username, u.created_at,
                    MAX(pe.timestamp) as last_active,
                    COUNT(DISTINCT CASE WHEN pe.event_type='module_action' THEN pe.id END) as total_actions
                FROM users u
                LEFT JOIN product_events pe ON u.username = pe.username
                WHERE u.subscription_tier != 'super_admin'
                GROUP BY u.username
                HAVING last_active IS NULL OR last_active < {offset}
            """

        users = _execute_plain(conn, sql).fetchall()

        results = []
        for u in users:
            u = _dict_row(u)
            username = u['username']

            modules = _execute_plain(
                conn, _q(f"""SELECT DISTINCT {mod_field}
                            FROM product_events
                            WHERE username=? AND event_type='module_action'"""),
                (username,)).fetchall()
            modules_used = []
            for m in modules:
                val = m[list(m.keys())[0]] if isinstance(m, dict) else m[0]
                if val:
                    modules_used.append(val)
            all_modules = {"content_generator", "copy_editor", "social_assistant", "visual_audit"}
            modules_never = all_modules - set(modules_used)

            steps = _execute_plain(
                conn, _q(f"""SELECT {step_field}
                            FROM product_events
                            WHERE username=? AND event_type='onboarding_step'"""),
                (username,)).fetchall()
            steps_done = []
            for s in steps:
                val = s[list(s.keys())[0]] if isinstance(s, dict) else s[0]
                if val:
                    steps_done.append(val)

            org_row = _execute_plain(
                conn, _q("SELECT org_id FROM users WHERE username=?"), (username,)).fetchone()
            org = username
            if org_row:
                org_val = org_row['org_id'] if isinstance(org_row, dict) else org_row[0]
                org = org_val if org_val else username

            profiles = _execute_plain(
                conn, _q(f"SELECT data FROM profiles WHERE org_id=? AND (is_sample_brand={'FALSE' if is_postgres() else '0'} OR is_sample_brand IS NULL)"),
                (org,)).fetchall()

            max_confidence = 0
            has_voice = False
            has_mh = False
            for p in profiles:
                try:
                    raw = p['data'] if isinstance(p, dict) else p[0]
                    d = json.loads(raw) if isinstance(raw, str) else raw
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
                "last_active": u.get('last_active') or "Never",
                "total_actions": u.get('total_actions', 0),
                "confidence": max_confidence,
                "missing": ", ".join(missing) if missing else "Complete",
            })

        return results
    finally:
        conn.close()


def get_acquisition_sources():
    """Returns acquisition source breakdown."""
    conn = _get_connection()
    try:
        source_field = _json_extract('metadata_json', 'source')
        sql = f"""
            SELECT {source_field} as source,
                   COUNT(*) as count
            FROM product_events
            WHERE event_type = 'user_registered'
            GROUP BY source
            ORDER BY count DESC
        """
        rows = _execute_plain(conn, sql).fetchall()
        return [_dict_row(r) for r in rows]
    finally:
        conn.close()


def get_revenue_metrics():
    """Returns revenue and conversion metrics."""
    conn = _get_connection()
    try:
        rows = _execute_plain(
            conn, "SELECT subscription_tier, COUNT(*) as cnt FROM users "
                  "WHERE subscription_tier != 'super_admin' GROUP BY subscription_tier").fetchall()
        tier_counts = {}
        for r in rows:
            if isinstance(r, dict):
                tier_counts[r['subscription_tier']] = r['cnt']
            else:
                tier_counts[r[0]] = r[1]

        paying = _fetchone_val(_execute_plain(
            conn, "SELECT COUNT(*) FROM users WHERE subscription_status='active' "
                  "AND subscription_tier IN ('solo', 'agency', 'enterprise')"), 0)

        total_non_admin = _fetchone_val(_execute_plain(
            conn, "SELECT COUNT(*) FROM users WHERE subscription_tier != 'super_admin'"), 0)

        new_tier = _json_extract('metadata_json', 'new_tier')
        if is_postgres():
            avg_days = _fetchone_val(_execute_plain(conn, f"""
                SELECT AVG(EXTRACT(EPOCH FROM (pe.timestamp::timestamp - u.created_at::timestamp)) / 86400)
                FROM product_events pe
                JOIN users u ON pe.username = u.username
                WHERE pe.event_type = 'subscription_changed'
                AND {new_tier} IN ('solo', 'agency', 'enterprise')
            """), None)
        else:
            avg_days = _fetchone_val(_execute_plain(conn, f"""
                SELECT AVG(julianday(pe.timestamp) - julianday(u.created_at))
                FROM product_events pe
                JOIN users u ON pe.username = u.username
                WHERE pe.event_type = 'subscription_changed'
                AND {new_tier} IN ('solo', 'agency', 'enterprise')
            """), None)

        return {
            "tier_counts": tier_counts,
            "paying_users": paying,
            "total_users": total_non_admin,
            "conversion_rate": round(paying / total_non_admin * 100, 1) if total_non_admin > 0 else 0,
            "avg_days_to_conversion": round(avg_days, 1) if avg_days else None,
        }
    finally:
        conn.close()


def get_product_events_csv():
    """Returns all product_events as CSV string for export."""
    conn = _get_connection()
    try:
        rows = _execute_plain(conn, "SELECT * FROM product_events ORDER BY timestamp DESC").fetchall()

        if not rows:
            return "id,event_type,username,org_id,brand_id,metadata_json,session_id,timestamp\n"

        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        first = _dict_row(rows[0])
        writer.writerow(first.keys())
        for row in rows:
            d = _dict_row(row)
            writer.writerow(d.values())
        return output.getvalue()
    finally:
        conn.close()


def create_user_admin(username, email, password, tier='solo', org_id=None, org_role='member'):
    """Admin user creation — bypasses seat limits."""
    hashed = ph.hash(password)
    conn = _get_connection()
    try:
        _execute_plain(conn, _q('''
            INSERT INTO users (username, email, password_hash, org_id, is_admin, subscription_tier,
                               subscription_status, org_role, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)
        '''), (username, email, hashed, org_id, True if org_role == 'owner' else False,
              tier, org_role, datetime.now().isoformat()))
        conn.commit()
        return True
    except (sqlite3.IntegrityError if not is_postgres() else Exception) as e:
        if is_postgres():
            conn.rollback()
            err_str = str(e).lower()
            if 'unique' in err_str or 'duplicate' in err_str:
                return False
            raise
        return False
    finally:
        conn.close()
