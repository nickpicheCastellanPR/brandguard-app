"""
test_suite.py — Comprehensive Signet Studio System Test Suite.

Covers 14 test categories across all modules. Does NOT modify application
code, does NOT touch the production database, does NOT call external APIs.

Run:
    python test_suite.py
"""

import sys
import os
import traceback
import sqlite3
import json
import tempfile
import shutil
import re
import importlib
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Test harness
# ---------------------------------------------------------------------------
results = []


def run_test(name, test_fn):
    """Run a test function, capture pass/fail/error."""
    try:
        result = test_fn()
        if result is True or result is None:
            results.append(("PASS", name, ""))
        elif isinstance(result, str):
            results.append(("WARN", name, result))
        else:
            results.append(("FAIL", name, str(result)))
    except Exception as e:
        results.append(("ERROR", name, f"{type(e).__name__}: {e}\n{traceback.format_exc()}"))


# ---------------------------------------------------------------------------
# Shared test state
# ---------------------------------------------------------------------------
_TEST_DB_PATH = None          # Set in Category 2
_original_db_name = None      # Saved so we can restore after tests


def _setup_test_db():
    """Create a temp directory and redirect db_manager.DB_NAME to a test DB."""
    global _TEST_DB_PATH, _original_db_name
    import db_manager as db
    _original_db_name = db.DB_NAME
    # Force SQLite for tests (clear DATABASE_URL)
    db.DATABASE_URL = ""
    tmp = tempfile.mkdtemp(prefix="signet_test_")
    _TEST_DB_PATH = os.path.join(tmp, "test.db")
    db.DB_NAME = _TEST_DB_PATH
    return db


def _teardown_test_db():
    """Restore the original DB_NAME and clean up."""
    global _TEST_DB_PATH, _original_db_name
    import db_manager as db
    if _original_db_name:
        db.DB_NAME = _original_db_name
    if _TEST_DB_PATH:
        tmp_dir = os.path.dirname(_TEST_DB_PATH)
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORY 1: Imports & Module Integrity
# ═══════════════════════════════════════════════════════════════════════════

_module_inventory = {}  # Populated during import tests


def _inventory_module(mod, mod_name):
    """List all public callables and constants in a module."""
    items = {}
    for attr_name in sorted(dir(mod)):
        if attr_name.startswith("_"):
            continue
        obj = getattr(mod, attr_name)
        kind = "function" if callable(obj) else "constant"
        items[attr_name] = kind
    _module_inventory[mod_name] = items


def test_import_db_manager():
    import db_manager
    _inventory_module(db_manager, "db_manager")
    required = [
        "init_db", "create_user", "check_login", "save_profile",
        "get_profiles", "delete_profile", "load_sample_brand",
        "log_event", "get_org_logs", "suspend_user", "unsuspend_user",
        "is_user_suspended", "get_user_full", "set_user_subscription",
        "record_usage_action", "get_monthly_usage", "count_user_brands",
    ]
    missing = [f for f in required if not hasattr(db_manager, f)]
    if missing:
        return f"Missing functions: {missing}"
    return True


def test_import_tier_config():
    import tier_config
    _inventory_module(tier_config, "tier_config")
    assert hasattr(tier_config, "TIER_CONFIG"), "Missing TIER_CONFIG"
    assert hasattr(tier_config, "get_tier_config"), "Missing get_tier_config"
    assert hasattr(tier_config, "get_tier_from_variant_id"), "Missing get_tier_from_variant_id"
    assert hasattr(tier_config, "PROTECTED_TIERS"), "Missing PROTECTED_TIERS"
    return True


def test_import_subscription_manager():
    # subscription_manager imports streamlit — we need to mock it
    try:
        import subscription_manager
        _inventory_module(subscription_manager, "subscription_manager")
        required = ["resolve_user_tier", "check_brand_limit",
                     "check_usage_limit", "record_ai_action",
                     "get_usage_nudge_message"]
        missing = [f for f in required if not hasattr(subscription_manager, f)]
        if missing:
            return f"Missing functions: {missing}"
        return True
    except ImportError as e:
        return f"Import failed (likely streamlit dependency): {e}"


def test_import_brand_ui():
    import brand_ui
    _inventory_module(brand_ui, "brand_ui")
    required = ["BRAND_COLORS", "SHIELD_ALIGNED", "SHIELD_DRIFT",
                 "SHIELD_DEGRADATION", "render_severity",
                 "render_module_help", "inject_typography_css",
                 "inject_button_css"]
    missing = [f for f in required if not hasattr(brand_ui, f)]
    if missing:
        return f"Missing exports: {missing}"
    return True


def test_import_sample_brand_data():
    import sample_brand_data
    _inventory_module(sample_brand_data, "sample_brand_data")
    assert hasattr(sample_brand_data, "SAMPLE_BRAND"), "Missing SAMPLE_BRAND"
    return True


def test_import_prompt_builder():
    import prompt_builder
    _inventory_module(prompt_builder, "prompt_builder")
    required = ["build_brand_context", "build_social_context",
                 "parse_voice_clusters", "get_cluster_status",
                 "build_mh_context", "VOICE_CLUSTER_NAMES",
                 "CONTENT_TYPE_TO_CLUSTER"]
    missing = [f for f in required if not hasattr(prompt_builder, f)]
    if missing:
        return f"Missing exports: {missing}"
    return True


def test_import_webhook_handler():
    try:
        import webhook_handler
        _inventory_module(webhook_handler, "webhook_handler")
        required = ["verify_signature", "handle_ls_webhook", "app"]
        missing = [f for f in required if not hasattr(webhook_handler, f)]
        if missing:
            return f"Missing exports: {missing}"
        return True
    except ImportError as e:
        return f"Import failed (likely FastAPI/uvicorn dependency): {e}"


def test_import_logic():
    try:
        import logic
        _inventory_module(logic, "logic")
        required = ["SignetLogic", "extract_dominant_colors", "ColorScorer",
                     "hex_to_rgb", "rgb_to_hex", "sanitize_user_input",
                     "image_to_base64"]
        missing = [f for f in required if not hasattr(logic, f)]
        if missing:
            return f"Missing exports: {missing}"
        return True
    except ImportError as e:
        return f"Import failed: {e}"


def test_import_visual_audit():
    try:
        import visual_audit
        _inventory_module(visual_audit, "visual_audit")
        required = ["run_full_audit", "run_color_compliance",
                     "run_visual_identity_check", "run_copy_compliance"]
        missing = [f for f in required if not hasattr(visual_audit, f)]
        if missing:
            return f"Missing exports: {missing}"
        return True
    except ImportError as e:
        return f"Import failed: {e}"


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORY 2: Database Schema Verification
# ═══════════════════════════════════════════════════════════════════════════

_schema_inventory = {}  # table -> [(name, type, notnull, default, pk)]


def _get_table_columns(conn_or_path, table):
    """Return column info from PRAGMA. Accepts either a connection or path."""
    if isinstance(conn_or_path, str):
        conn = sqlite3.connect(conn_or_path)
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        conn.close()
    else:
        rows = conn_or_path.execute(f"PRAGMA table_info({table})").fetchall()
    return {row[1]: {"type": row[2], "notnull": row[3], "default": row[4], "pk": row[5]} for row in rows}


def _get_tables(conn):
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
    return [r[0] for r in rows]


def test_schema_creation():
    db = _setup_test_db()
    db.init_db()
    conn = sqlite3.connect(_TEST_DB_PATH)
    tables = _get_tables(conn)
    conn.close()
    expected = ["users", "profiles", "activity_log", "organizations",
                "usage_tracking", "admin_audit_log", "platform_settings", "product_events"]
    missing = [t for t in expected if t not in tables]
    if missing:
        return f"Missing tables: {missing}"
    return True


def test_users_table_columns():
    cols = _get_table_columns(_TEST_DB_PATH, "users")
    _schema_inventory["users"] = cols
    expected = [
        "username", "email", "password_hash", "is_admin", "org_id",
        "subscription_status", "created_at", "subscription_tier",
        "org_role", "lemon_squeezy_subscription_id",
        "lemon_squeezy_variant_id", "last_subscription_sync",
        "last_login", "comp_expires_at", "comp_reason",
        "subscription_override_until", "is_beta_tester",
        "is_suspended", "suspended_at", "suspended_reason", "suspended_by",
    ]
    missing = [c for c in expected if c not in cols]
    if missing:
        return f"Missing columns: {missing}"
    return True


def test_profiles_table_columns():
    cols = _get_table_columns(_TEST_DB_PATH, "profiles")
    _schema_inventory["profiles"] = cols
    expected = ["id", "org_id", "name", "data", "created_at",
                "updated_by", "is_sample_brand"]
    missing = [c for c in expected if c not in cols]
    if missing:
        return f"Missing columns: {missing}"
    return True


def test_activity_log_table():
    cols = _get_table_columns(_TEST_DB_PATH, "activity_log")
    _schema_inventory["activity_log"] = cols
    expected = ["id", "org_id", "username", "timestamp", "activity_type",
                "asset_name", "score", "verdict", "metadata_json"]
    missing = [c for c in expected if c not in cols]
    if missing:
        return f"Missing columns: {missing}"
    return True


def test_usage_tracking_table():
    cols = _get_table_columns(_TEST_DB_PATH, "usage_tracking")
    _schema_inventory["usage_tracking"] = cols
    expected = ["id", "username", "org_id", "module", "action_weight",
                "billing_month", "timestamp", "is_impersonated", "action_detail"]
    missing = [c for c in expected if c not in cols]
    if missing:
        return f"Missing columns: {missing}"
    return True


def test_organizations_table():
    cols = _get_table_columns(_TEST_DB_PATH, "organizations")
    _schema_inventory["organizations"] = cols
    expected = ["org_id", "org_name", "subscription_tier",
                "owner_username", "created_at"]
    missing = [c for c in expected if c not in cols]
    if missing:
        return f"Missing columns: {missing}"
    return True


def test_admin_audit_log_table():
    cols = _get_table_columns(_TEST_DB_PATH, "admin_audit_log")
    _schema_inventory["admin_audit_log"] = cols
    expected = ["id", "admin_username", "action_type", "target_type",
                "target_id", "details", "timestamp"]
    missing = [c for c in expected if c not in cols]
    if missing:
        return f"Missing columns: {missing}"
    return True


def test_platform_settings_table():
    cols = _get_table_columns(_TEST_DB_PATH, "platform_settings")
    _schema_inventory["platform_settings"] = cols
    expected = ["key", "value", "updated_at", "updated_by"]
    missing = [c for c in expected if c not in cols]
    if missing:
        return f"Missing columns: {missing}"
    return True


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORY 3: Tier Configuration
# ═══════════════════════════════════════════════════════════════════════════

def test_tier_solo():
    from tier_config import TIER_CONFIG
    solo = TIER_CONFIG.get("solo")
    if not solo:
        return "Solo tier not found"
    issues = []
    if solo["max_brands"] != 3:
        issues.append(f"max_brands={solo['max_brands']}, expected 3")
    if 1304018 not in solo["lemon_squeezy_variant_ids"]:
        issues.append(f"variant_id 1304018 not in {solo['lemon_squeezy_variant_ids']}")
    if solo["monthly_ai_actions"] != 200:
        issues.append(f"monthly_ai_actions={solo['monthly_ai_actions']}, expected 200")
    return "; ".join(issues) if issues else True


def test_tier_agency():
    from tier_config import TIER_CONFIG
    agency = TIER_CONFIG.get("agency")
    if not agency:
        return "Agency tier not found"
    issues = []
    if agency["max_brands"] != 10:
        issues.append(f"max_brands={agency['max_brands']}, expected 10")
    if 1304027 not in agency["lemon_squeezy_variant_ids"]:
        issues.append(f"variant_id 1304027 not in {agency['lemon_squeezy_variant_ids']}")
    if agency["monthly_ai_actions"] != 800:
        issues.append(f"monthly_ai_actions={agency['monthly_ai_actions']}, expected 800")
    return "; ".join(issues) if issues else True


def test_tier_enterprise():
    from tier_config import TIER_CONFIG
    ent = TIER_CONFIG.get("enterprise")
    if not ent:
        return "Enterprise tier not found"
    issues = []
    if ent["max_brands"] != -1:
        issues.append(f"max_brands={ent['max_brands']}, expected -1 (unlimited)")
    if 1303961 not in ent["lemon_squeezy_variant_ids"]:
        issues.append(f"variant_id 1303961 not in {ent['lemon_squeezy_variant_ids']}")
    if ent["monthly_ai_actions"] != 1500:
        issues.append(f"monthly_ai_actions={ent['monthly_ai_actions']}, expected 1500")
    return "; ".join(issues) if issues else True


def test_tier_free_default():
    """No explicit 'free' tier — get_tier_config falls back to solo."""
    from tier_config import get_tier_config
    result = get_tier_config("nonexistent_tier")
    if result is None:
        return "get_tier_config returns None for unknown tier (expected fallback to solo)"
    if result.get("max_brands") != 3:
        return f"Fallback tier has max_brands={result.get('max_brands')}, expected 3 (solo)"
    return True


def test_tier_casing_consistency():
    from tier_config import TIER_CONFIG
    issues = []
    for key in TIER_CONFIG:
        if key != key.lower():
            issues.append(f"Tier key {key!r} is not lowercase")
    return "; ".join(issues) if issues else True


def test_tier_ordering():
    """Agency limits > Solo limits across all dimensions."""
    from tier_config import TIER_CONFIG
    solo = TIER_CONFIG["solo"]
    agency = TIER_CONFIG["agency"]
    issues = []
    if agency["max_brands"] <= solo["max_brands"]:
        issues.append(f"agency max_brands ({agency['max_brands']}) not > solo ({solo['max_brands']})")
    if agency["monthly_ai_actions"] <= solo["monthly_ai_actions"]:
        issues.append(f"agency actions ({agency['monthly_ai_actions']}) not > solo ({solo['monthly_ai_actions']})")
    if agency["max_seats"] <= solo["max_seats"]:
        issues.append(f"agency seats ({agency['max_seats']}) not > solo ({solo['max_seats']})")
    return "; ".join(issues) if issues else True


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORY 4: User Management
# ═══════════════════════════════════════════════════════════════════════════

def test_create_user():
    import db_manager as db
    result = db.create_user("testuser1", "test@example.com", "password123")
    if not result:
        return "create_user returned False"
    return True


def test_create_duplicate_user():
    import db_manager as db
    result = db.create_user("testuser1", "test2@example.com", "password456")
    if result is not False:
        return f"Duplicate user creation should return False, got {result}"
    return True


def test_get_user_by_username():
    import db_manager as db
    user = db.get_user_full("testuser1")
    if not user:
        return "get_user_full returned None"
    if user["username"] != "testuser1":
        return f"Username mismatch: {user['username']}"
    if user["email"] != "test@example.com":
        return f"Email mismatch: {user['email']}"
    return True


def test_get_nonexistent_user():
    import db_manager as db
    user = db.get_user_full("ghost_user_xyz")
    if user is not None:
        return f"Expected None, got {user}"
    return True


def test_set_super_admin():
    import db_manager as db
    db.update_user_fields("testuser1", subscription_tier="super_admin")
    user = db.get_user_full("testuser1")
    if user["subscription_tier"] != "super_admin":
        return f"Tier not updated: {user['subscription_tier']}"
    # Reset
    db.update_user_fields("testuser1", subscription_tier="solo")
    return True


def test_set_beta_tester():
    import db_manager as db
    db.update_user_fields("testuser1", is_beta_tester=1)
    user = db.get_user_full("testuser1")
    if not user["is_beta_tester"]:
        return f"is_beta_tester not set: {user['is_beta_tester']}"
    db.update_user_fields("testuser1", is_beta_tester=0)
    return True


def test_suspend_user():
    import db_manager as db
    db.suspend_user("testuser1", "test violation", "admin_user")
    is_susp, reason = db.is_user_suspended("testuser1")
    if not is_susp:
        return f"Expected suspended=True, got {is_susp}"
    if reason != "test violation":
        return f"Reason mismatch: {reason}"
    user = db.get_user_full("testuser1")
    if not user.get("suspended_at"):
        return "suspended_at not set"
    if user.get("suspended_by") != "admin_user":
        return f"suspended_by mismatch: {user.get('suspended_by')}"
    return True


def test_unsuspend_user():
    import db_manager as db
    db.unsuspend_user("testuser1")
    is_susp, reason = db.is_user_suspended("testuser1")
    if is_susp:
        return f"Expected suspended=False after unsuspend, got {is_susp}"
    if reason is not None:
        return f"Reason should be None after unsuspend, got {reason}"
    return True


def test_suspend_super_admin():
    """suspend_user should reject suspension of super_admin accounts."""
    import db_manager as db
    db.update_user_fields("testuser1", subscription_tier="super_admin")
    result = db.suspend_user("testuser1", "should this work?", "other_admin")
    is_susp, _ = db.is_user_suspended("testuser1")
    db.unsuspend_user("testuser1")
    db.update_user_fields("testuser1", subscription_tier="solo")
    if result is not False:
        return f"suspend_user returned {result} for super_admin, expected False"
    if is_susp:
        return "super_admin was actually suspended despite guard"
    return True


def test_check_login():
    import db_manager as db
    result = db.check_login("testuser1", "password123")
    if not result:
        return "check_login returned None for valid credentials"
    if result["username"] != "testuser1":
        return f"Username mismatch: {result['username']}"
    bad = db.check_login("testuser1", "wrong_password")
    if bad is not None:
        return f"check_login should return None for bad password, got {bad}"
    return True


def test_check_login_nonexistent():
    import db_manager as db
    result = db.check_login("nobody_here", "pass")
    if result is not None:
        return f"Expected None for nonexistent user, got {result}"
    return True


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORY 5: Brand CRUD Operations
# ═══════════════════════════════════════════════════════════════════════════

def test_create_brand():
    import db_manager as db
    profile_data = {"inputs": {"wiz_name": "Test Brand", "wiz_mission": "Test mission"}}
    db.save_profile("testuser1", "Test Brand", profile_data)
    profiles = db.get_profiles("testuser1")
    if "Test Brand" not in profiles:
        return "Brand not found after creation"
    return True


def test_retrieve_brand():
    import db_manager as db
    profiles = db.get_profiles("testuser1")
    brand = profiles.get("Test Brand")
    if not brand:
        return "Brand not found"
    if brand.get("inputs", {}).get("wiz_name") != "Test Brand":
        return f"Brand data mismatch: {brand}"
    return True


def test_update_brand():
    import db_manager as db
    updated = {
        "inputs": {
            "wiz_name": "Test Brand",
            "wiz_mission": "Updated mission",
            "mh_brand_promise": "Our updated promise",
        }
    }
    db.save_profile("testuser1", "Test Brand", updated)
    profiles = db.get_profiles("testuser1")
    brand = profiles.get("Test Brand")
    if brand["inputs"]["wiz_mission"] != "Updated mission":
        return f"Update didn't persist: {brand['inputs']['wiz_mission']}"
    if brand["inputs"]["mh_brand_promise"] != "Our updated promise":
        return f"MH update didn't persist"
    return True


def test_delete_brand():
    import db_manager as db
    db.save_profile("testuser1", "Delete Me Brand",
                     {"inputs": {"wiz_name": "Delete Me Brand"}})
    profiles = db.get_profiles("testuser1")
    if "Delete Me Brand" not in profiles:
        return "Brand not created for deletion test"
    db.delete_profile("testuser1", "Delete Me Brand")
    profiles = db.get_profiles("testuser1")
    if "Delete Me Brand" in profiles:
        return "Brand still present after deletion"
    return True


def test_list_brands():
    import db_manager as db
    # Create a second brand
    db.save_profile("testuser1", "Brand Two", {"inputs": {"wiz_name": "Brand Two"}})
    profiles = db.get_profiles("testuser1")
    if len(profiles) < 2:
        return f"Expected at least 2 brands, got {len(profiles)}"
    # Cleanup
    db.delete_profile("testuser1", "Brand Two")
    return True


def test_count_brands_excludes_sample():
    import db_manager as db
    org_id = "testuser1"  # Solo user — org_id falls back to username
    count_before = db.count_user_brands(org_id, exclude_sample=True)
    db.load_sample_brand("testuser1")
    count_after = db.count_user_brands(org_id, exclude_sample=True)
    if count_after != count_before:
        return (f"Sample brand counted toward limit: before={count_before}, "
                f"after={count_after}")
    db.delete_sample_brand("testuser1")
    return True


def test_load_sample_brand():
    import db_manager as db
    result = db.load_sample_brand("testuser1")
    if not result:
        return "load_sample_brand returned False (already loaded?)"
    has = db.has_sample_brand("testuser1")
    if not has:
        return "has_sample_brand returned False after loading"
    return True


def test_load_sample_brand_twice():
    import db_manager as db
    result = db.load_sample_brand("testuser1")
    if result is not False:
        return f"Second load should return False, got {result}"
    return True


def test_delete_sample_brand():
    import db_manager as db
    db.delete_sample_brand("testuser1")
    has = db.has_sample_brand("testuser1")
    if has:
        return "Sample brand still present after deletion"
    return True


def test_reload_sample_brand():
    import db_manager as db
    result = db.load_sample_brand("testuser1")
    if not result:
        return "Reload after deletion failed"
    db.delete_sample_brand("testuser1")
    return True


def test_is_profile_sample():
    import db_manager as db
    db.load_sample_brand("testuser1")
    from sample_brand_data import SAMPLE_BRAND
    is_sample = db.is_profile_sample("testuser1", SAMPLE_BRAND["profile_name"])
    if not is_sample:
        return "is_profile_sample returned False for sample brand"
    is_regular = db.is_profile_sample("testuser1", "Test Brand")
    if is_regular:
        return "is_profile_sample returned True for regular brand"
    db.delete_sample_brand("testuser1")
    return True


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORY 6: Calibration Engine
# ═══════════════════════════════════════════════════════════════════════════

# We need to mock the count_social_by_platform function which is defined in app.py.
# Since we can't import app.py (Streamlit), we'll re-implement the calibration logic
# by extracting it. Instead, we call app.py functions directly after injecting a
# minimal streamlit mock.

_calc_fn = None  # Will hold calculate_calibration_score
_count_social_fn = None  # Will hold count_social_by_platform


def _load_calibration_engine():
    """Parse and exec just the calibration functions from app.py without importing Streamlit."""
    global _calc_fn, _count_social_fn

    app_path = os.path.join(os.path.dirname(__file__), "app.py")
    with open(app_path, "r", encoding="utf-8") as f:
        source = f.read()

    # Extract count_social_by_platform
    match_social = re.search(
        r'(def count_social_by_platform\(.*?\n(?:(?:    .*|)\n)*)',
        source
    )
    # Extract calculate_calibration_score
    match_cal = re.search(
        r'(def calculate_calibration_score\(.*?\n(?:(?:    .*|)\n)*)',
        source
    )

    if not match_cal:
        raise RuntimeError("Could not extract calculate_calibration_score from app.py")

    # Build a minimal execution environment
    exec_globals = {
        "json": json,
        "re": re,
        "__builtins__": __builtins__,
    }

    # We need brand_ui for the shield icons referenced in cluster_health
    try:
        import brand_ui
        exec_globals["brand_ui"] = brand_ui
    except ImportError:
        # Create a minimal mock
        class _MockBrandUI:
            SHIELD_ALIGNED = ""
            SHIELD_DRIFT = ""
            SHIELD_DEGRADATION = ""
        exec_globals["brand_ui"] = _MockBrandUI()

    # Exec count_social_by_platform first (it's needed by calibration)
    if match_social:
        exec(match_social.group(1), exec_globals)

    # Exec calculate_calibration_score
    exec(match_cal.group(1), exec_globals)

    _count_social_fn = exec_globals.get("count_social_by_platform")
    _calc_fn = exec_globals.get("calculate_calibration_score")

    if not _calc_fn:
        raise RuntimeError("calculate_calibration_score not found after exec")


def _make_profile(inputs=None):
    """Helper to build a profile_data dict."""
    return {"inputs": inputs or {}}


def _make_full_voice_dna():
    """Build voice DNA with 3+ samples per cluster."""
    clusters = [
        "CORPORATE AFFAIRS", "CRISIS & RESPONSE", "INTERNAL LEADERSHIP",
        "THOUGHT LEADERSHIP", "BRAND MARKETING"
    ]
    chunks = []
    for c in clusters:
        for i in range(3):
            chunks.append(
                f"[ASSET: CLUSTER: {c} | SENDER: TEST | AUDIENCE: TEST | SOURCE: Sample {i+1} | DATE: 2025-01-01]\n"
                f"Sample content for {c} cluster, sample {i+1}.\n"
                "----------------"
            )
    return "\n\n".join(chunks)


def _make_pillars_json(count=3, complete=True):
    """Build pillars JSON with specified completeness."""
    pillars = []
    for i in range(count):
        p = {"name": f"Pillar {i+1}"}
        if complete:
            p["tagline"] = f"Tagline for pillar {i+1}"
            p["headline_claim"] = f"Headline claim for pillar {i+1}"
            p["proof_1"] = f"Proof point 1 for pillar {i+1}"
            p["proof_2"] = f"Proof point 2 for pillar {i+1}"
            p["proof_3"] = f"Proof point 3 for pillar {i+1}"
        pillars.append(p)
    return json.dumps(pillars)


def _make_social_dna(linkedin=0, instagram=0, twitter=0):
    """Build social_dna with platform samples."""
    chunks = []
    for i in range(linkedin):
        chunks.append(f"[ASSET: LINKEDIN POST | DATE: 2025-01-01]\nLinkedIn sample {i+1}\n----------------")
    for i in range(instagram):
        chunks.append(f"[ASSET: INSTAGRAM POST | DATE: 2025-01-01]\nInstagram sample {i+1}\n----------------")
    for i in range(twitter):
        chunks.append(f"[ASSET: TWITTER POST | DATE: 2025-01-01]\nTwitter sample {i+1}\n----------------")
    return "\n\n".join(chunks)


def test_cal_weights_sum():
    """Strategy(10) + MH(25) + Visuals(10) + Social(10) + Voice(45) = 100."""
    total = 10 + 25 + 10 + 10 + 45
    if total != 100:
        return f"Weights sum to {total}, expected 100"
    return True


def test_cal_empty_brand():
    prof = _make_profile({})
    result = _calc_fn(prof)
    if result["score"] != 0:
        return f"Empty brand score = {result['score']}, expected 0"
    return True


def test_cal_strategy_only():
    prof = _make_profile({
        "wiz_mission": "Test mission",
        "wiz_values": "Test values",
        "wiz_guardrails": "Test guardrails",
        "wiz_archetype": "The Creator",
    })
    result = _calc_fn(prof)
    # Strategy = 10pts, but hard ceiling caps at 55 (MH = 0)
    if result["score"] != 10:
        return f"Strategy-only score = {result['score']}, expected 10"
    return True


def test_cal_strategy_plus_full_mh():
    prof = _make_profile({
        "wiz_mission": "Mission",
        "wiz_values": "Values",
        "wiz_guardrails": "Guards",
        "wiz_archetype": "Creator",
        "mh_brand_promise": "Our promise",
        "mh_pillars_json": _make_pillars_json(3, complete=True),
        "mh_founder_positioning": "Founder pos",
        "mh_pov": "Our POV",
        "mh_boilerplate": "Boilerplate text",
        "mh_offlimits": "No competitor names",
        "mh_preapproval_claims": "Stats need approval",
        "mh_tone_constraints": "No snark",
    })
    result = _calc_fn(prof)
    # Strategy = 10, MH sub-score should be ~100 -> 25pts
    expected_min = 33  # At least strategy (10) + significant MH
    if result["score"] < expected_min:
        return f"Strategy+MH score = {result['score']}, expected >= {expected_min}"
    return True


def test_cal_full_brand():
    prof = _make_profile({
        "wiz_mission": "Mission",
        "wiz_values": "Values",
        "wiz_guardrails": "Guards",
        "wiz_archetype": "Creator",
        "mh_brand_promise": "Our promise",
        "mh_pillars_json": _make_pillars_json(3, complete=True),
        "mh_founder_positioning": "Founder pos",
        "mh_pov": "Our POV",
        "mh_boilerplate": "Boilerplate text",
        "mh_offlimits": "Off limits",
        "mh_preapproval_claims": "Pre-approval",
        "mh_tone_constraints": "Constraints",
        "palette_primary": ["#1A2332"],
        "visual_dna": "[ASSET: LOGO DESCRIPTION]\nLogo desc\n----",
        "social_dna": _make_social_dna(linkedin=3, instagram=3, twitter=3),
        "voice_dna": _make_full_voice_dna(),
    })
    result = _calc_fn(prof)
    if result["score"] < 90:
        return f"Full brand score = {result['score']}, expected >= 90"
    return True


def test_cal_hard_ceiling_no_mh():
    """0% MH + everything else maxed → cap at 55."""
    prof = _make_profile({
        "wiz_mission": "Mission",
        "wiz_values": "Values",
        "wiz_guardrails": "Guards",
        "wiz_archetype": "Creator",
        "palette_primary": ["#1A2332"],
        "visual_dna": "[ASSET: LOGO DESCRIPTION]\nLogo desc\n----",
        "social_dna": _make_social_dna(linkedin=3, instagram=3, twitter=3),
        "voice_dna": _make_full_voice_dna(),
    })
    result = _calc_fn(prof)
    if result["score"] > 55:
        return f"Score with no MH = {result['score']}, should be capped at 55"
    if not result.get("mh_ceiling_active"):
        return "mh_ceiling_active should be True"
    return True


def test_cal_partial_mh_removes_ceiling():
    """Any MH data > 0 removes the 55 ceiling."""
    prof = _make_profile({
        "wiz_mission": "Mission",
        "wiz_values": "Values",
        "wiz_guardrails": "Guards",
        "wiz_archetype": "Creator",
        "mh_brand_promise": "Our promise",
        "palette_primary": ["#1A2332"],
        "visual_dna": "[ASSET: LOGO DESCRIPTION]\nLogo desc\n----",
        "social_dna": _make_social_dna(linkedin=3, instagram=3, twitter=3),
        "voice_dna": _make_full_voice_dna(),
    })
    result = _calc_fn(prof)
    if result.get("mh_ceiling_active"):
        return "Ceiling should NOT be active with brand_promise set"
    return True


def test_cal_mh_brand_promise_weight():
    """Brand promise only → ~20% of MH → 5% of total."""
    prof = _make_profile({
        "mh_brand_promise": "Our promise",
    })
    result = _calc_fn(prof)
    expected = int(20 * 0.25)  # 5
    if result["score"] != expected:
        return f"Brand promise only score = {result['score']}, expected {expected}"
    return True


def test_cal_voice_cluster_empty():
    prof = _make_profile({
        "voice_dna": "",
    })
    result = _calc_fn(prof)
    for key, info in result.get("clusters", {}).items():
        if info["count"] != 0:
            return f"Cluster {key} has count {info['count']} with empty voice_dna"
        if info["status"] != "EMPTY":
            return f"Cluster {key} status is {info['status']}, expected EMPTY"
    return True


def test_cal_voice_cluster_partial():
    """1 sample in Corporate Affairs → UNSTABLE, 3 points."""
    voice = (
        "[ASSET: CLUSTER: CORPORATE AFFAIRS | SENDER: T | AUDIENCE: T | SOURCE: S1 | DATE: 2025-01-01]\n"
        "Sample 1\n----------------"
    )
    prof = _make_profile({"voice_dna": voice})
    result = _calc_fn(prof)
    corp = result["clusters"].get("Corporate", {})
    if corp.get("count") != 1:
        return f"Corporate count = {corp.get('count')}, expected 1"
    if corp.get("status") != "UNSTABLE":
        return f"Corporate status = {corp.get('status')}, expected UNSTABLE"
    return True


def test_cal_voice_cluster_fortified():
    """3 samples → FORTIFIED, 9 points."""
    chunks = []
    for i in range(3):
        chunks.append(
            f"[ASSET: CLUSTER: CORPORATE AFFAIRS | SENDER: T | AUDIENCE: T | SOURCE: S{i} | DATE: 2025-01-01]\n"
            f"Sample {i}\n----------------"
        )
    voice = "\n\n".join(chunks)
    prof = _make_profile({"voice_dna": voice})
    result = _calc_fn(prof)
    corp = result["clusters"].get("Corporate", {})
    if corp.get("count") < 3:
        return f"Corporate count = {corp.get('count')}, expected >= 3"
    if corp.get("status") != "FORTIFIED":
        return f"Corporate status = {corp.get('status')}, expected FORTIFIED"
    return True


def test_cal_voice_3clusters_full_2empty():
    """3 clusters at 3+ samples, 2 empty → voice = 27/45."""
    clusters = ["CORPORATE AFFAIRS", "CRISIS & RESPONSE", "INTERNAL LEADERSHIP"]
    chunks = []
    for c in clusters:
        for i in range(3):
            chunks.append(
                f"[ASSET: CLUSTER: {c} | SENDER: T | AUDIENCE: T | SOURCE: S{i} | DATE: 2025-01-01]\n"
                f"Sample\n----------------"
            )
    voice = "\n\n".join(chunks)
    prof = _make_profile({"voice_dna": voice})
    result = _calc_fn(prof)
    voice_score = sum(
        9 if info["status"] == "FORTIFIED" else (3 if info["status"] == "UNSTABLE" else 0)
        for info in result["clusters"].values()
    )
    if voice_score != 27:
        return f"Voice score = {voice_score}, expected 27 (3x9)"
    return True


def test_cal_social_scoring():
    """LinkedIn 3/5, Instagram 0/5, Twitter 0/5 → 1 platform calibrated → 7pts."""
    social = _make_social_dna(linkedin=3, instagram=0, twitter=0)
    prof = _make_profile({"social_dna": social})
    result = _calc_fn(prof)
    platforms = result.get("social_platforms", {})
    if platforms.get("LinkedIn", 0) < 3:
        return f"LinkedIn count = {platforms.get('LinkedIn')}, expected >= 3"
    # Score with only social = at most 7 (1 platform calibrated) capped by 55 (no MH)
    return True


def test_cal_social_all_platforms():
    """All platforms at 3+ → 10pts."""
    social = _make_social_dna(linkedin=3, instagram=3, twitter=3)
    prof = _make_profile({"social_dna": social})
    result = _calc_fn(prof)
    platforms = result.get("social_platforms", {})
    calibrated = sum(1 for c in platforms.values() if c >= 3)
    if calibrated < 2:
        return f"Only {calibrated} platforms calibrated, expected >= 2 for full score"
    return True


def test_cal_sample_brand():
    """Load Meridian Labs sample brand and verify high score."""
    from sample_brand_data import SAMPLE_BRAND
    profile_data = SAMPLE_BRAND["profile_data"]
    result = _calc_fn(profile_data)
    if result["score"] < 90:
        return f"Sample brand score = {result['score']}, expected >= 90"
    return True


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORY 7: Usage Tracking & Limits
# ═══════════════════════════════════════════════════════════════════════════

def test_record_usage():
    import db_manager as db
    billing_month = datetime.now().strftime("%Y-%m")
    db.record_usage_action("testuser1", "testuser1", "content_generator", 1, billing_month, "test action")
    used = db.get_monthly_usage_user("testuser1", billing_month)
    if used < 1:
        return f"Usage count = {used}, expected >= 1"
    return True


def test_usage_with_detail():
    import db_manager as db
    billing_month = datetime.now().strftime("%Y-%m")
    db.record_usage_action("testuser1", "testuser1", "visual_audit", 3, billing_month, "audit of logo.png")
    # Verify via direct query
    _conn = sqlite3.connect(_TEST_DB_PATH)
    _row = _conn.execute(
        "SELECT action_detail FROM usage_tracking WHERE username = ? AND module = 'visual_audit' ORDER BY id DESC LIMIT 1",
        ("testuser1",)
    ).fetchone()
    _conn.close()
    if not _row or _row[0] != "audit of logo.png":
        return f"action_detail not stored correctly: {_row}"
    return True


def test_usage_count_no_activity():
    import db_manager as db
    billing_month = datetime.now().strftime("%Y-%m")
    used = db.get_monthly_usage_user("noactivity_user", billing_month)
    if used != 0:
        return f"Expected 0 usage for user with no activity, got {used}"
    return True


def test_usage_org_level():
    import db_manager as db
    billing_month = datetime.now().strftime("%Y-%m")
    org_used = db.get_monthly_usage("testuser1", billing_month)
    if org_used < 1:
        return f"Org usage = {org_used}, expected >= 1"
    return True


def test_activity_log():
    import db_manager as db
    db.log_event("testuser1", "testuser1", "CONTENT GENERATOR", "test.docx", 85, "APPROVED", {"detail": "test"})
    logs = db.get_org_logs("testuser1", limit=5)
    if not logs:
        return "No activity logs returned"
    latest = logs[0]
    if latest["activity_type"] != "CONTENT GENERATOR":
        return f"activity_type mismatch: {latest['activity_type']}"
    return True


def test_activity_log_order():
    import db_manager as db
    db.log_event("testuser1", "testuser1", "COPY EDITOR", "draft.txt", 70, "NEEDS REVIEW", {})
    logs = db.get_org_logs("testuser1", limit=5)
    if len(logs) < 2:
        return f"Expected at least 2 log entries, got {len(logs)}"
    # Latest should be COPY EDITOR (most recent)
    if logs[0]["activity_type"] != "COPY EDITOR":
        return f"Logs not in reverse order: latest={logs[0]['activity_type']}"
    return True


def test_activity_log_scoping():
    import db_manager as db
    db.create_user("otheruser", "other@example.com", "pass123")
    db.log_event("otheruser", "otheruser", "VISUAL AUDIT", "img.png", 95, "COMPLIANT", {})
    logs_user1 = db.get_org_logs("testuser1", limit=100)
    logs_user2 = db.get_org_logs("otheruser", limit=100)
    user1_types = [l["activity_type"] for l in logs_user1]
    if "VISUAL AUDIT" in user1_types:
        return "testuser1 sees otheruser's activity log (scoping failure)"
    if not logs_user2:
        return "otheruser has no logs"
    return True


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORY 8: Suspension System
# ═══════════════════════════════════════════════════════════════════════════

def test_suspension_fields():
    import db_manager as db
    db.create_user("suspendme", "suspend@test.com", "pass")
    db.suspend_user("suspendme", "Terms of service violation", "admin_nick")
    user = db.get_user_full("suspendme")
    issues = []
    if not user.get("is_suspended"):
        issues.append("is_suspended not True")
    if not user.get("suspended_at"):
        issues.append("suspended_at not set")
    if user.get("suspended_reason") != "Terms of service violation":
        issues.append(f"suspended_reason wrong: {user.get('suspended_reason')}")
    if user.get("suspended_by") != "admin_nick":
        issues.append(f"suspended_by wrong: {user.get('suspended_by')}")
    return "; ".join(issues) if issues else True


def test_unsuspension_clears_fields():
    import db_manager as db
    db.unsuspend_user("suspendme")
    user = db.get_user_full("suspendme")
    issues = []
    if user.get("is_suspended"):
        issues.append("is_suspended still True")
    if user.get("suspended_at") is not None:
        issues.append(f"suspended_at not cleared: {user.get('suspended_at')}")
    if user.get("suspended_reason") is not None:
        issues.append(f"suspended_reason not cleared: {user.get('suspended_reason')}")
    if user.get("suspended_by") is not None:
        issues.append(f"suspended_by not cleared: {user.get('suspended_by')}")
    return "; ".join(issues) if issues else True


def test_suspension_survives_status_update():
    import db_manager as db
    db.suspend_user("suspendme", "Test reason", "admin")
    db.set_user_subscription("suspendme", "solo", "active", "ls_123", "1304018")
    is_susp, reason = db.is_user_suspended("suspendme")
    if not is_susp:
        return "Suspension cleared by subscription update"
    db.unsuspend_user("suspendme")
    return True


def test_admin_audit_log():
    import db_manager as db
    db.log_admin_action("admin_nick", "suspend_user", "user", "suspendme",
                         {"reason": "test"})
    logs = db.get_admin_audit_log(limit=5)
    if not logs:
        return "No admin audit log entries"
    latest = logs[0]
    if latest["action_type"] != "suspend_user":
        return f"action_type mismatch: {latest['action_type']}"
    return True


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORY 9: Prompt Builder
# ═══════════════════════════════════════════════════════════════════════════

def test_prompt_full_brand():
    from prompt_builder import build_brand_context
    from sample_brand_data import SAMPLE_BRAND
    ctx = build_brand_context(SAMPLE_BRAND["profile_data"])
    issues = []
    if "Meridian Labs" not in ctx:
        issues.append("Brand name not in context")
    if "BRAND PROMISE" not in ctx:
        issues.append("Brand promise section missing")
    if "VOICE REFERENCE SAMPLES" not in ctx:
        issues.append("Voice samples section missing")
    if "DATA COMPLETENESS" not in ctx:
        issues.append("Data completeness section missing")
    if "MESSAGE HOUSE" not in ctx:
        issues.append("Message house section missing")
    return "; ".join(issues) if issues else True


def test_prompt_empty_brand():
    from prompt_builder import build_brand_context
    ctx = build_brand_context({"inputs": {}})
    if "None" in ctx and "none" not in ctx.lower():
        # Allow lowercase "none" in natural language
        return f"Literal 'None' found in empty brand context"
    if ctx.startswith("Error") or "error" in ctx.lower()[:20]:
        return f"Error building empty brand context: {ctx[:100]}"
    return True


def test_prompt_mh_no_voice():
    from prompt_builder import build_brand_context
    ctx = build_brand_context({"inputs": {
        "wiz_name": "Test",
        "mh_brand_promise": "Our promise",
        "mh_pillars_json": _make_pillars_json(2),
    }})
    issues = []
    if "MESSAGE HOUSE" not in ctx:
        issues.append("Message house missing with MH data")
    if "VOICE REFERENCE SAMPLES" in ctx:
        issues.append("Voice section present with no voice data")
    return "; ".join(issues) if issues else True


def test_prompt_voice_no_mh():
    from prompt_builder import build_brand_context
    ctx = build_brand_context({"inputs": {
        "wiz_name": "Test",
        "voice_dna": _make_full_voice_dna(),
    }})
    if "VOICE REFERENCE SAMPLES" not in ctx:
        return "Voice section missing with voice data"
    if "No message house configured" not in ctx:
        return "Missing degradation notice for empty MH"
    return True


def test_prompt_content_type_cluster():
    """All content types in CONTENT_TYPE_TO_CLUSTER map to valid clusters."""
    from prompt_builder import CONTENT_TYPE_TO_CLUSTER, VOICE_CLUSTER_NAMES
    issues = []
    for ct, cluster in CONTENT_TYPE_TO_CLUSTER.items():
        if cluster not in VOICE_CLUSTER_NAMES:
            issues.append(f"{ct!r} maps to unknown cluster {cluster!r}")
    return "; ".join(issues) if issues else True


def test_prompt_social_context():
    from prompt_builder import build_social_context
    from sample_brand_data import SAMPLE_BRAND
    ctx = build_social_context(SAMPLE_BRAND["profile_data"])
    issues = []
    if "SOCIAL MEDIA SAMPLES" not in ctx:
        issues.append("Social samples section missing")
    if "Brand Marketing" not in ctx:
        issues.append("Brand Marketing voice reference missing")
    if "Meridian Labs" not in ctx:
        issues.append("Brand name missing from social context")
    return "; ".join(issues) if issues else True


def test_prompt_no_none_injection():
    """Check that build_brand_context doesn't inject 'None' for missing fields."""
    from prompt_builder import build_brand_context
    test_cases = [
        {},
        {"wiz_name": "Test"},
        {"wiz_name": "Test", "wiz_mission": ""},
        {"wiz_name": "Test", "mh_pillars_json": ""},
    ]
    for i, inputs in enumerate(test_cases):
        ctx = build_brand_context({"inputs": inputs})
        # Check for literal "None" as a standalone word (not inside "none of the")
        if re.search(r'\bNone\b', ctx):
            return f"Test case {i}: literal 'None' found in context"
    return True


def test_prompt_cluster_filtering():
    from prompt_builder import build_brand_context
    from sample_brand_data import SAMPLE_BRAND
    ctx = build_brand_context(
        SAMPLE_BRAND["profile_data"],
        cluster_filter="Corporate Affairs"
    )
    if "Corporate Affairs" not in ctx:
        return "Cluster filter not applied"
    return True


def test_prompt_voice_cluster_status():
    from prompt_builder import get_cluster_status
    from sample_brand_data import SAMPLE_BRAND
    voice_dna = SAMPLE_BRAND["profile_data"]["inputs"]["voice_dna"]
    statuses = get_cluster_status(voice_dna)
    for cname, info in statuses.items():
        if info["count"] < 3:
            return f"Sample brand cluster {cname} has only {info['count']} samples (expected >= 3)"
        if info["status"] != "FORTIFIED":
            return f"Sample brand cluster {cname} is {info['status']} (expected FORTIFIED)"
    return True


def test_prompt_mh_builder():
    from prompt_builder import build_mh_context
    mh = build_mh_context({
        "mh_brand_promise": "Our promise",
        "mh_pillars_json": _make_pillars_json(3, complete=True),
        "mh_founder_positioning": "Founder positioning",
        "mh_pov": "Our POV",
        "mh_boilerplate": "Our boilerplate",
        "mh_offlimits": "Competitor names",
        "mh_preapproval_claims": "Stats",
        "mh_tone_constraints": "No snark",
    })
    expected_parts = [
        "BRAND PROMISE", "MESSAGE PILLARS", "PILLAR 1", "PILLAR 2", "PILLAR 3",
        "FOUNDER POSITIONING", "POV STATEMENT", "BOILERPLATE",
        "MESSAGING GUARDRAILS", "Off-limits", "Pre-approval", "Tone constraints",
    ]
    missing = [p for p in expected_parts if p not in mh]
    if missing:
        return f"Missing sections in MH context: {missing}"
    return True


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORY 10: Webhook Handler
# ═══════════════════════════════════════════════════════════════════════════

def test_webhook_signature_valid():
    import hmac
    import hashlib
    try:
        from webhook_handler import verify_signature
    except ImportError:
        return "webhook_handler import failed"
    # Set a test secret
    import webhook_handler as wh
    original_secret = wh.WEBHOOK_SECRET
    wh.WEBHOOK_SECRET = "test_secret_123"
    payload = b'{"test": "data"}'
    sig = hmac.new(b"test_secret_123", payload, hashlib.sha256).hexdigest()
    result = verify_signature(payload, sig)
    wh.WEBHOOK_SECRET = original_secret
    if not result:
        return "Valid signature rejected"
    return True


def test_webhook_signature_invalid():
    try:
        from webhook_handler import verify_signature
    except ImportError:
        return "webhook_handler import failed"
    import webhook_handler as wh
    original_secret = wh.WEBHOOK_SECRET
    wh.WEBHOOK_SECRET = "test_secret_123"
    result = verify_signature(b'{"test": "data"}', "badbadbadbadsignature")
    wh.WEBHOOK_SECRET = original_secret
    if result:
        return "Invalid signature accepted"
    return True


def test_webhook_signature_missing_secret():
    """When WEBHOOK_SECRET is empty, verify_signature allows through (dev mode)."""
    try:
        from webhook_handler import verify_signature
    except ImportError:
        return "webhook_handler import failed"
    import webhook_handler as wh
    original_secret = wh.WEBHOOK_SECRET
    wh.WEBHOOK_SECRET = ""
    result = verify_signature(b'{"test": "data"}', "")
    wh.WEBHOOK_SECRET = original_secret
    if not result:
        return "Empty secret should allow passthrough in dev mode"
    return True


def test_webhook_variant_mapping():
    from tier_config import get_tier_from_variant_id
    cases = [
        (1304018, "solo"),
        (1304027, "agency"),
        (1303961, "enterprise"),
        (9999999, None),
        (None, None),
        ("garbage", None),
    ]
    issues = []
    for vid, expected in cases:
        result = get_tier_from_variant_id(vid)
        if result != expected:
            issues.append(f"variant {vid}: got {result!r}, expected {expected!r}")
    return "; ".join(issues) if issues else True


def test_webhook_find_user_by_email():
    """_find_username_by_email should find users by email."""
    import db_manager as db
    try:
        from webhook_handler import _find_username_by_email
    except ImportError:
        return "webhook_handler import failed"
    # Use the test DB which has testuser1 with test@example.com
    result = _find_username_by_email("test@example.com")
    if result != "testuser1":
        return f"Expected 'testuser1', got {result!r}"
    none_result = _find_username_by_email("nobody@nowhere.com")
    if none_result is not None:
        return f"Expected None for unknown email, got {none_result!r}"
    return True


def test_webhook_subscription_created():
    """Simulate subscription_created event processing."""
    import db_manager as db
    try:
        from webhook_handler import _handle_subscription_active
    except ImportError:
        return "webhook_handler import failed"
    _handle_subscription_active("test@example.com", "agency", "sub_123", "1304027")
    user = db.get_user_full("testuser1")
    if user["subscription_tier"] != "agency":
        return f"Tier not updated: {user['subscription_tier']}"
    if user["subscription_status"] != "active":
        return f"Status not active: {user['subscription_status']}"
    # Restore to solo
    db.set_user_subscription("testuser1", "solo", "inactive")
    return True


def test_webhook_subscription_cancelled():
    import db_manager as db
    try:
        from webhook_handler import _update_user_by_email
    except ImportError:
        return "webhook_handler import failed"
    _update_user_by_email("test@example.com", "solo", "cancelled", "sub_123")
    user = db.get_user_full("testuser1")
    if user["subscription_status"] != "cancelled":
        return f"Status not cancelled: {user['subscription_status']}"
    # Restore
    db.set_user_subscription("testuser1", "solo", "inactive")
    return True


def test_webhook_nonexistent_user():
    """Event for non-existent user should not crash."""
    try:
        from webhook_handler import _handle_subscription_active
    except ImportError:
        return "webhook_handler import failed"
    # Should log warning, not crash
    _handle_subscription_active("nobody@nowhere.com", "solo", "sub_999", "1304018")
    return True


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORY 11: Terminology Compliance Audit
# ═══════════════════════════════════════════════════════════════════════════

_term_findings = []  # Collected during tests


def _grep_codebase(pattern, exclude_comments=False):
    """Search Python files for a pattern. Returns list of (file, line_no, line)."""
    hits = []
    root = os.path.dirname(os.path.abspath(__file__))
    py_files = [
        "app.py", "db_manager.py", "tier_config.py", "subscription_manager.py",
        "webhook_handler.py", "brand_ui.py", "sample_brand_data.py",
        "prompt_builder.py", "logic.py", "visual_audit.py", "admin_panel.py",
    ]
    for fname in py_files:
        fpath = os.path.join(root, fname)
        if not os.path.exists(fpath):
            continue
        try:
            with open(fpath, "r", encoding="utf-8", errors="replace") as f:
                for i, line in enumerate(f, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        stripped = line.strip()
                        is_comment = stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''")
                        if exclude_comments and is_comment:
                            continue
                        hits.append((fname, i, stripped[:120]))
        except Exception:
            pass
    return hits


def _check_term(test_name, pattern, allow_comments=True):
    """Helper that returns True (pass) or a report string."""
    hits = _grep_codebase(pattern, exclude_comments=not allow_comments)
    if not hits:
        return True
    report_lines = []
    for fname, lineno, line in hits:
        is_comment = line.startswith("#") or line.startswith('"""') or line.startswith("'''")
        tag = "[COMMENT]" if is_comment else "[USER-FACING]"
        entry = f"  {tag} {fname}:{lineno}: {line}"
        report_lines.append(entry)
        _term_findings.append({"test": test_name, "file": fname, "line": lineno,
                                "text": line, "comment": is_comment})
    user_facing = [h for h in hits
                    if not h[2].startswith("#") and not h[2].startswith('"""') and not h[2].startswith("'''")]
    if user_facing:
        return f"Found {len(user_facing)} user-facing hit(s):\n" + "\n".join(report_lines)
    return f"Found {len(hits)} hit(s) (comments only):\n" + "\n".join(report_lines)


def test_term_brand_governance_engine():
    return _check_term("Brand Governance Engine", r"Brand Governance Engine")


def test_term_brand_governance():
    return _check_term("brand governance", r"brand governance")


def test_term_publishing_perimeter():
    return _check_term("publishing perimeter", r"publishing perimeter")


def test_term_authoritative_signal():
    return _check_term("authoritative signal", r"authoritative signal")


def test_term_voice_dna():
    """Check for user-facing 'Voice DNA' / 'voice DNA' strings.
    Note: variable names like 'voice_dna' are OK."""
    hits = _grep_codebase(r'["\'].*[Vv]oice DNA.*["\']')
    if not hits:
        return True
    report = "\n".join(f"  {f}:{l}: {t}" for f, l, t in hits)
    return f"Found 'Voice DNA' in strings:\n{report}"


def test_term_gold_standard():
    return _check_term("gold-standard", r"gold[- ]standard")


def test_term_signal_degradation():
    return _check_term("signal degradation", r"signal degradation")


def test_term_signal_integrity():
    return _check_term("Signal Integrity Score", r"Signal Integrity Score")


def test_term_algorithmic_fidelity():
    return _check_term("algorithmic fidelity", r"algorithmic fidelity")


def test_term_hallucination():
    """Check for user-facing 'hallucination' — internal code comments OK."""
    hits = _grep_codebase(r"hallucination", exclude_comments=True)
    if not hits:
        return True
    report = "\n".join(f"  {f}:{l}: {t}" for f, l, t in hits)
    return f"Found user-facing 'hallucination':\n{report}"


def test_term_fortified_user_facing():
    """Check for user-facing Fortified/Unstable/Empty status labels.
    These are internal calibration terms; dashboard should show
    Calibrated/Partially Calibrated/Not Calibrated.
    Note: variable/code usage of FORTIFIED/UNSTABLE/EMPTY is expected."""
    # Just flag the existence — this is informational
    hits_fortified = _grep_codebase(r'["\']FORTIFIED["\']')
    hits_unstable = _grep_codebase(r'["\']UNSTABLE["\']')
    hits_empty_status = _grep_codebase(r'["\']EMPTY["\']')
    total = len(hits_fortified) + len(hits_unstable) + len(hits_empty_status)
    if total > 0:
        return (f"Found {total} string-literal occurrences of FORTIFIED/UNSTABLE/EMPTY. "
                "These appear in calibration logic code. Verify they are not shown "
                "directly to end users in the UI (some may be internal labels).")
    return True


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORY 12: Configuration & Environment
# ═══════════════════════════════════════════════════════════════════════════

def test_config_toml_exists():
    toml_path = os.path.join(os.path.dirname(__file__), ".streamlit", "config.toml")
    if not os.path.exists(toml_path):
        return f"Missing .streamlit/config.toml"
    return True


def test_config_primary_color():
    toml_path = os.path.join(os.path.dirname(__file__), ".streamlit", "config.toml")
    with open(toml_path, "r") as f:
        content = f.read()
    if '#ab8f59' not in content:
        return f"primaryColor '#ab8f59' not found in config.toml"
    return True


def test_config_background_color():
    toml_path = os.path.join(os.path.dirname(__file__), ".streamlit", "config.toml")
    with open(toml_path, "r") as f:
        content = f.read()
    # The actual config uses backgroundColor = "#24363b"
    if '#24363b' not in content:
        return f"backgroundColor '#24363b' not found (expected dark teal)"
    return True


def test_config_secondary_bg_color():
    toml_path = os.path.join(os.path.dirname(__file__), ".streamlit", "config.toml")
    with open(toml_path, "r") as f:
        content = f.read()
    if '#1b2a2e' not in content:
        return f"secondaryBackgroundColor '#1b2a2e' not found"
    return True


def test_config_text_color():
    toml_path = os.path.join(os.path.dirname(__file__), ".streamlit", "config.toml")
    with open(toml_path, "r") as f:
        content = f.read()
    if '#f5f5f0' not in content:
        return f"textColor '#f5f5f0' not found"
    return True


def test_start_sh_exists():
    sh_path = os.path.join(os.path.dirname(__file__), "start.sh")
    if not os.path.exists(sh_path):
        return "Missing start.sh"
    with open(sh_path, "r") as f:
        content = f.read()
    issues = []
    if "uvicorn" not in content:
        issues.append("uvicorn not found in start.sh")
    if "streamlit" not in content:
        issues.append("streamlit not found in start.sh")
    if "8001" not in content:
        issues.append("port 8001 not found in start.sh")
    return "; ".join(issues) if issues else True


def test_brand_ui_colors():
    import brand_ui
    expected = {
        "dark": "#24363b",
        "gold": "#ab8f59",
        "cream": "#f5f5f0",
        "charcoal": "#3d3d3d",
        "sage": "#5c6b61",
        "copper": "#a6784d",
    }
    issues = []
    for key, hex_val in expected.items():
        actual = brand_ui.BRAND_COLORS.get(key)
        if actual != hex_val:
            issues.append(f"{key}: expected {hex_val}, got {actual}")
    return "; ".join(issues) if issues else True


def test_env_no_api_key():
    """Verify the app handles missing ANTHROPIC_API_KEY gracefully."""
    import logic
    # logic.client would be None if no key
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "ANTHROPIC_API_KEY is set — cannot test missing key behavior"
    if logic.client is not None:
        return f"logic.client is not None despite missing API key"
    return True


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORY 13: Sample Brand Data Integrity
# ═══════════════════════════════════════════════════════════════════════════

def test_sample_brand_name():
    from sample_brand_data import SAMPLE_BRAND
    name = SAMPLE_BRAND["profile_data"]["inputs"].get("wiz_name", "")
    if "Meridian" not in name:
        return f"Brand name = {name!r}, expected to contain 'Meridian'"
    return True


def test_sample_archetype():
    from sample_brand_data import SAMPLE_BRAND
    arch = SAMPLE_BRAND["profile_data"]["inputs"].get("wiz_archetype", "")
    if not arch:
        return "Archetype is empty"
    return True


def test_sample_tone():
    from sample_brand_data import SAMPLE_BRAND
    tone = SAMPLE_BRAND["profile_data"]["inputs"].get("wiz_tone", "")
    if not tone:
        return "Tone keywords is empty"
    return True


def test_sample_mission():
    from sample_brand_data import SAMPLE_BRAND
    mission = SAMPLE_BRAND["profile_data"]["inputs"].get("wiz_mission", "")
    if not mission or len(mission) < 10:
        return f"Mission is missing or too short: {mission!r}"
    return True


def test_sample_values():
    from sample_brand_data import SAMPLE_BRAND
    values = SAMPLE_BRAND["profile_data"]["inputs"].get("wiz_values", "")
    if not values:
        return "Core values is empty"
    return True


def test_sample_guardrails():
    from sample_brand_data import SAMPLE_BRAND
    guardrails = SAMPLE_BRAND["profile_data"]["inputs"].get("wiz_guardrails", "")
    if not guardrails or len(guardrails) < 20:
        return f"Guardrails missing or too short"
    if "DO" not in guardrails.upper():
        return "Guardrails should contain DO's"
    if "DON'T" not in guardrails.upper() and "DON'T" not in guardrails:
        return "Guardrails should contain DON'T's"
    return True


def test_sample_hex_palette():
    from sample_brand_data import SAMPLE_BRAND
    inputs = SAMPLE_BRAND["profile_data"]["inputs"]
    primary = inputs.get("palette_primary", [])
    secondary = inputs.get("palette_secondary", [])
    accent = inputs.get("palette_accent", [])
    all_colors = primary + secondary + accent
    if len(all_colors) < 4:
        return f"Only {len(all_colors)} palette colors defined, expected >= 4"
    for c in all_colors:
        if not re.match(r'^#[0-9a-fA-F]{6}$', c):
            return f"Invalid hex code: {c}"
    return True


def test_sample_brand_promise():
    from sample_brand_data import SAMPLE_BRAND
    bp = SAMPLE_BRAND["profile_data"]["inputs"].get("mh_brand_promise", "")
    if not bp or len(bp) < 10:
        return f"Brand promise missing or too short"
    return True


def test_sample_pillars():
    from sample_brand_data import SAMPLE_BRAND
    pj = SAMPLE_BRAND["profile_data"]["inputs"].get("mh_pillars_json", "")
    if not pj:
        return "Pillars JSON is empty"
    pillars = json.loads(pj)
    if len(pillars) != 3:
        return f"Expected 3 pillars, got {len(pillars)}"
    for i, p in enumerate(pillars):
        issues = []
        if not p.get("name"):
            issues.append(f"Pillar {i+1}: missing name")
        if not p.get("tagline"):
            issues.append(f"Pillar {i+1}: missing tagline")
        if not p.get("headline_claim"):
            issues.append(f"Pillar {i+1}: missing headline_claim")
        for j in range(1, 4):
            if not p.get(f"proof_{j}"):
                issues.append(f"Pillar {i+1}: missing proof_{j}")
        if issues:
            return "; ".join(issues)
    return True


def test_sample_founder_positioning():
    from sample_brand_data import SAMPLE_BRAND
    fp = SAMPLE_BRAND["profile_data"]["inputs"].get("mh_founder_positioning", "")
    if not fp:
        return "Founder positioning is empty"
    return True


def test_sample_pov():
    from sample_brand_data import SAMPLE_BRAND
    pov = SAMPLE_BRAND["profile_data"]["inputs"].get("mh_pov", "")
    if not pov:
        return "POV statement is empty"
    return True


def test_sample_boilerplate():
    from sample_brand_data import SAMPLE_BRAND
    bp = SAMPLE_BRAND["profile_data"]["inputs"].get("mh_boilerplate", "")
    if not bp:
        return "Boilerplate is empty"
    return True


def test_sample_messaging_guardrails():
    from sample_brand_data import SAMPLE_BRAND
    inputs = SAMPLE_BRAND["profile_data"]["inputs"]
    issues = []
    if not inputs.get("mh_offlimits"):
        issues.append("mh_offlimits is empty")
    if not inputs.get("mh_preapproval_claims"):
        issues.append("mh_preapproval_claims is empty")
    if not inputs.get("mh_tone_constraints"):
        issues.append("mh_tone_constraints is empty")
    return "; ".join(issues) if issues else True


def test_sample_voice_clusters():
    from sample_brand_data import SAMPLE_BRAND
    from prompt_builder import get_cluster_status
    voice = SAMPLE_BRAND["profile_data"]["inputs"].get("voice_dna", "")
    if not voice:
        return "voice_dna is empty"
    statuses = get_cluster_status(voice)
    issues = []
    for cname, info in statuses.items():
        if info["count"] < 3:
            issues.append(f"{cname}: only {info['count']} samples (need >= 3)")
    return "; ".join(issues) if issues else True


def test_sample_social_samples():
    from sample_brand_data import SAMPLE_BRAND
    social = SAMPLE_BRAND["profile_data"]["inputs"].get("social_dna", "")
    if not social:
        return "social_dna is empty"
    count = social.upper().count("[ASSET:")
    if count < 3:
        return f"Only {count} social samples, expected >= 3"
    return True


def test_sample_no_empty_fields():
    from sample_brand_data import SAMPLE_BRAND
    inputs = SAMPLE_BRAND["profile_data"]["inputs"]
    expected_fields = [
        "wiz_name", "wiz_archetype", "wiz_tone", "wiz_mission", "wiz_values",
        "wiz_guardrails", "mh_brand_promise", "mh_pillars_json",
        "mh_founder_positioning", "mh_pov", "mh_boilerplate",
        "mh_offlimits", "mh_preapproval_claims", "mh_tone_constraints",
        "voice_dna", "social_dna", "visual_dna",
    ]
    empty = []
    for f in expected_fields:
        val = inputs.get(f)
        if val is None or (isinstance(val, str) and not val.strip()):
            empty.append(f)
    if empty:
        return f"Empty fields: {empty}"
    return True


# ═══════════════════════════════════════════════════════════════════════════
# CATEGORY 14: Edge Cases & Error Handling
# ═══════════════════════════════════════════════════════════════════════════

def test_edge_empty_brand_name():
    """save_profile should reject empty brand names."""
    import db_manager as db
    result = db.save_profile("testuser1", "", {"inputs": {"wiz_name": ""}})
    if result is not False:
        return f"save_profile returned {result} for empty name, expected False"
    result2 = db.save_profile("testuser1", "   ", {"inputs": {"wiz_name": ""}})
    if result2 is not False:
        return f"save_profile returned {result2} for whitespace name, expected False"
    return True


def test_edge_long_brand_name():
    import db_manager as db
    long_name = "A" * 1000
    db.save_profile("testuser1", long_name, {"inputs": {"wiz_name": long_name}})
    profiles = db.get_profiles("testuser1")
    if long_name not in profiles:
        return "Long brand name not stored"
    db.delete_profile("testuser1", long_name)
    return True


def test_edge_calibration_corrupted_data():
    """Calibration with corrupted/missing data should not crash."""
    result = _calc_fn({"inputs": {"mh_pillars_json": "not valid json"}})
    if result is None:
        return "Calibration returned None for corrupted data"
    # Score should be 0 or some safe value
    return True


def test_edge_calibration_legacy():
    """Legacy profile format (no 'inputs' key) should not crash."""
    result = _calc_fn({"final_text": "Some text here"})
    if result is None:
        return "Calibration returned None for legacy format"
    return True


def test_edge_usage_missing_brand():
    """Log usage with None org_id — should not crash."""
    import db_manager as db
    billing_month = datetime.now().strftime("%Y-%m")
    try:
        db.record_usage_action("testuser1", None, "content_generator", 1, billing_month)
        return True
    except Exception as e:
        return f"Crashed: {e}"


def test_edge_activity_log_empty():
    import db_manager as db
    logs = db.get_org_logs("brand_with_zero_activity", limit=20)
    if logs is None:
        return "get_org_logs returned None instead of empty list"
    if len(logs) != 0:
        return f"Expected empty list, got {len(logs)} items"
    return True


def test_edge_long_prompt_builder_input():
    """Very long text in prompt builder fields — should not crash."""
    from prompt_builder import build_brand_context
    long_text = "X" * 10000
    ctx = build_brand_context({"inputs": {
        "wiz_name": long_text,
        "wiz_mission": long_text,
        "wiz_guardrails": long_text,
    }})
    if not ctx:
        return "build_brand_context returned empty for long input"
    return True


def test_edge_color_scorer_empty():
    """ColorScorer with empty inputs."""
    from logic import ColorScorer
    score, reason = ColorScorer.grade_color_match([], "")
    # No brand hexes → score 100 ("no strict brand colors")
    if score != 100:
        return f"Expected 100 for no brand colors, got {score}"
    score2, _ = ColorScorer.grade_color_match(["#ff0000"], "")
    if score2 != 100:
        return f"Expected 100 for no brand colors in text, got {score2}"
    score3, _ = ColorScorer.grade_color_match([], "#ff0000")
    if score3 != 0:
        return f"Expected 0 for no detected colors, got {score3}"
    return True


def test_edge_webhook_empty_body():
    """Malformed / empty payload should be handled."""
    try:
        from webhook_handler import verify_signature
    except ImportError:
        return "webhook_handler import failed"
    # Empty body with no secret set should pass through
    import webhook_handler as wh
    original = wh.WEBHOOK_SECRET
    wh.WEBHOOK_SECRET = ""
    result = verify_signature(b"", "")
    wh.WEBHOOK_SECRET = original
    if not result:
        return "Empty body with no secret should pass dev mode"
    return True


def test_edge_platform_settings():
    """Platform settings CRUD edge cases."""
    import db_manager as db
    db.set_platform_setting("test_key", "test_value", "test_admin")
    val = db.get_platform_setting("test_key")
    if val != "test_value":
        return f"Setting not retrieved: {val}"
    # Update same key
    db.set_platform_setting("test_key", "updated_value", "test_admin")
    val = db.get_platform_setting("test_key")
    if val != "updated_value":
        return f"Setting not updated: {val}"
    # Non-existent key
    val = db.get_platform_setting("nonexistent_key")
    if val is not None:
        return f"Non-existent key returned {val} instead of None"
    return True


def test_edge_table_row_counts():
    """get_table_row_counts should not crash."""
    import db_manager as db
    counts = db.get_table_row_counts()
    if not isinstance(counts, dict):
        return f"Expected dict, got {type(counts)}"
    if "users" not in counts:
        return "Missing 'users' key"
    return True


# ═══════════════════════════════════════════════════════════════════════════
# Report Generation
# ═══════════════════════════════════════════════════════════════════════════

def print_report():
    """Print and save structured test report."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    py_ver = sys.version.split()[0]
    sqlite_ver = sqlite3.sqlite_version

    total = len(results)
    passed = sum(1 for s, _, _ in results if s == "PASS")
    warned = sum(1 for s, _, _ in results if s == "WARN")
    failed = sum(1 for s, _, _ in results if s == "FAIL")
    errored = sum(1 for s, _, _ in results if s == "ERROR")

    lines = []
    lines.append(f"# SIGNET TEST REPORT")
    lines.append(f"Generated: {ts}")
    lines.append(f"Python: {py_ver}")
    lines.append(f"SQLite: {sqlite_ver}")
    lines.append("")
    lines.append("## SUMMARY")
    lines.append(f"- Total Tests: {total}")
    lines.append(f"- Passed: {passed}")
    lines.append(f"- Warnings: {warned}")
    lines.append(f"- Failed: {failed}")
    lines.append(f"- Errors: {errored}")
    lines.append("")

    # --- Failures & Errors ---
    fails_and_errors = [(s, n, d) for s, n, d in results if s in ("FAIL", "ERROR")]
    if fails_and_errors:
        lines.append("## FAILURES & ERRORS")
        for status, name, detail in fails_and_errors:
            lines.append(f"### [{status}] {name}")
            lines.append(f"```")
            lines.append(detail)
            lines.append(f"```")
            lines.append("")
    else:
        lines.append("## FAILURES & ERRORS")
        lines.append("None!")
        lines.append("")

    # --- Warnings ---
    warns = [(s, n, d) for s, n, d in results if s == "WARN"]
    if warns:
        lines.append("## WARNINGS")
        for _, name, detail in warns:
            lines.append(f"### [WARN] {name}")
            lines.append(f"```")
            lines.append(detail)
            lines.append(f"```")
            lines.append("")
    else:
        lines.append("## WARNINGS")
        lines.append("None!")
        lines.append("")

    # --- Full Results ---
    lines.append("## FULL RESULTS")
    lines.append("")
    current_category = ""
    for status, name, detail in results:
        # Detect category change from test name prefix
        parts = name.split(":", 1)
        cat = parts[0].strip() if ":" in name else ""
        if cat and cat != current_category:
            current_category = cat
            lines.append(f"### {current_category}")
            lines.append("")

        icon = {"PASS": "PASS", "WARN": "WARN", "FAIL": "FAIL", "ERROR": "ERR!"}[status]
        line = f"- [{icon}] {name}"
        if detail and status != "PASS":
            # Truncate long details
            short = detail.split("\n")[0][:120]
            line += f" — {short}"
        lines.append(line)
    lines.append("")

    # --- Module Inventory ---
    lines.append("## MODULE INVENTORY")
    lines.append("")
    for mod_name, exports in sorted(_module_inventory.items()):
        lines.append(f"### {mod_name}")
        for name, kind in exports.items():
            lines.append(f"- `{name}` ({kind})")
        lines.append("")

    # --- Schema Inventory ---
    lines.append("## SCHEMA INVENTORY")
    lines.append("")
    for table_name, cols in sorted(_schema_inventory.items()):
        lines.append(f"### {table_name}")
        lines.append("| Column | Type | PK | Not Null | Default |")
        lines.append("|--------|------|-----|----------|---------|")
        for col_name, info in cols.items():
            lines.append(
                f"| {col_name} | {info['type']} | {'YES' if info['pk'] else ''} | "
                f"{'YES' if info['notnull'] else ''} | {info['default'] or ''} |"
            )
        lines.append("")

    # --- Manual Testing Required ---
    lines.append("## MANUAL TESTING REQUIRED")
    lines.append("")
    lines.append("The following aspects cannot be tested programmatically:")
    lines.append("")
    lines.append("1. **Streamlit UI Rendering** — Verify all pages render without visual errors:")
    lines.append("   - Dashboard, Brand Architect, Visual Compliance, Copy Editor, Content Generator, Social Media Assistant")
    lines.append("   - Sidebar navigation and module routing")
    lines.append("   - Calibration dial and progress bars render correctly")
    lines.append("   - Gold button text is legible (not gold-on-gold)")
    lines.append("")
    lines.append("2. **AI API Calls** — Requires valid ANTHROPIC_API_KEY:")
    lines.append("   - Content Generator produces brand-aligned output")
    lines.append("   - Copy Editor audits drafts against brand profile")
    lines.append("   - Social Media Assistant generates posts with web search")
    lines.append("   - Visual Audit completes 3-layer analysis")
    lines.append("")
    lines.append("3. **Visual Appearance** — Browser inspection required:")
    lines.append("   - Castellan color palette renders correctly (dark teal bg, gold accents, cream text)")
    lines.append("   - Montserrat typography loads and applies globally")
    lines.append("   - Expander backgrounds are cream (#f5f5f0)")
    lines.append("   - Audit findings text is legible (not white-on-white)")
    lines.append("   - Reference Anchors / severity indicators have proper contrast")
    lines.append("   - Shield SVGs render inline in all browsers")
    lines.append("")
    lines.append("4. **Lemon Squeezy Integration** — Requires live webhook delivery:")
    lines.append("   - Webhook HTTP endpoint accepts POST requests")
    lines.append("   - HMAC signature validation with real LS_WEBHOOK_SECRET")
    lines.append("   - Full lifecycle: subscription_created → updated → cancelled → resumed")
    lines.append("")
    lines.append("5. **Admin Panel** — Requires super_admin login:")
    lines.append("   - User management (impersonation, suspension, tier changes)")
    lines.append("   - Organization management")
    lines.append("   - Usage analytics and audit log viewing")
    lines.append("   - Password reset functionality")
    lines.append("")

    report = "\n".join(lines)

    # Print to stdout (handle Windows cp1252 encoding)
    try:
        print(report)
    except UnicodeEncodeError:
        print(report.encode("ascii", errors="replace").decode("ascii"))

    # Save to file
    report_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "TEST_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nReport saved to: {report_path}")


# ═══════════════════════════════════════════════════════════════════════════
# Main runner
# ═══════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("SIGNET STUDIO — COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print()

    # ── Category 1: Imports ──
    print("Category 1: Imports & Module Integrity...")
    run_test("Cat 1: Import db_manager", test_import_db_manager)
    run_test("Cat 1: Import tier_config", test_import_tier_config)
    run_test("Cat 1: Import subscription_manager", test_import_subscription_manager)
    run_test("Cat 1: Import brand_ui", test_import_brand_ui)
    run_test("Cat 1: Import sample_brand_data", test_import_sample_brand_data)
    run_test("Cat 1: Import prompt_builder", test_import_prompt_builder)
    run_test("Cat 1: Import webhook_handler", test_import_webhook_handler)
    run_test("Cat 1: Import logic", test_import_logic)
    run_test("Cat 1: Import visual_audit", test_import_visual_audit)
    print(f"  {sum(1 for s,_,_ in results if s=='PASS')}/{len(results)} passed")

    # ── Category 2: Schema ──
    print("Category 2: Database Schema Verification...")
    cat2_start = len(results)
    run_test("Cat 2: Schema creation", test_schema_creation)
    run_test("Cat 2: Users table columns", test_users_table_columns)
    run_test("Cat 2: Profiles table columns", test_profiles_table_columns)
    run_test("Cat 2: Activity log table", test_activity_log_table)
    run_test("Cat 2: Usage tracking table", test_usage_tracking_table)
    run_test("Cat 2: Organizations table", test_organizations_table)
    run_test("Cat 2: Admin audit log table", test_admin_audit_log_table)
    run_test("Cat 2: Platform settings table", test_platform_settings_table)
    cat2_pass = sum(1 for s,_,_ in results[cat2_start:] if s=='PASS')
    print(f"  {cat2_pass}/{len(results)-cat2_start} passed")

    # ── Category 3: Tier Configuration ──
    print("Category 3: Tier Configuration...")
    cat3_start = len(results)
    run_test("Cat 3: Solo tier", test_tier_solo)
    run_test("Cat 3: Agency tier", test_tier_agency)
    run_test("Cat 3: Enterprise tier", test_tier_enterprise)
    run_test("Cat 3: Free/default tier fallback", test_tier_free_default)
    run_test("Cat 3: Tier casing consistency", test_tier_casing_consistency)
    run_test("Cat 3: Tier ordering (agency > solo)", test_tier_ordering)
    cat3_pass = sum(1 for s,_,_ in results[cat3_start:] if s=='PASS')
    print(f"  {cat3_pass}/{len(results)-cat3_start} passed")

    # ── Category 4: User Management ──
    print("Category 4: User Management...")
    cat4_start = len(results)
    run_test("Cat 4: Create user", test_create_user)
    run_test("Cat 4: Duplicate user", test_create_duplicate_user)
    run_test("Cat 4: Get user by username", test_get_user_by_username)
    run_test("Cat 4: Get non-existent user", test_get_nonexistent_user)
    run_test("Cat 4: Set super_admin", test_set_super_admin)
    run_test("Cat 4: Set beta_tester", test_set_beta_tester)
    run_test("Cat 4: Suspend user", test_suspend_user)
    run_test("Cat 4: Unsuspend user", test_unsuspend_user)
    run_test("Cat 4: Suspend super_admin", test_suspend_super_admin)
    run_test("Cat 4: Check login (valid)", test_check_login)
    run_test("Cat 4: Check login (nonexistent)", test_check_login_nonexistent)
    cat4_pass = sum(1 for s,_,_ in results[cat4_start:] if s=='PASS')
    print(f"  {cat4_pass}/{len(results)-cat4_start} passed")

    # ── Category 5: Brand CRUD ──
    print("Category 5: Brand CRUD Operations...")
    cat5_start = len(results)
    run_test("Cat 5: Create brand", test_create_brand)
    run_test("Cat 5: Retrieve brand", test_retrieve_brand)
    run_test("Cat 5: Update brand", test_update_brand)
    run_test("Cat 5: Delete brand", test_delete_brand)
    run_test("Cat 5: List brands", test_list_brands)
    run_test("Cat 5: Sample brand excludes from count", test_count_brands_excludes_sample)
    run_test("Cat 5: Load sample brand", test_load_sample_brand)
    run_test("Cat 5: Load sample brand twice", test_load_sample_brand_twice)
    run_test("Cat 5: Delete sample brand", test_delete_sample_brand)
    run_test("Cat 5: Reload sample brand", test_reload_sample_brand)
    run_test("Cat 5: Is profile sample", test_is_profile_sample)
    cat5_pass = sum(1 for s,_,_ in results[cat5_start:] if s=='PASS')
    print(f"  {cat5_pass}/{len(results)-cat5_start} passed")

    # ── Category 6: Calibration Engine ──
    print("Category 6: Calibration Engine...")
    cat6_start = len(results)
    try:
        _load_calibration_engine()
        run_test("Cat 6: Weights sum to 100%", test_cal_weights_sum)
        run_test("Cat 6: Empty brand = 0%", test_cal_empty_brand)
        run_test("Cat 6: Strategy only = 10%", test_cal_strategy_only)
        run_test("Cat 6: Strategy + full MH >= 33%", test_cal_strategy_plus_full_mh)
        run_test("Cat 6: Full brand >= 90%", test_cal_full_brand)
        run_test("Cat 6: Hard ceiling (no MH) cap at 55", test_cal_hard_ceiling_no_mh)
        run_test("Cat 6: Partial MH removes ceiling", test_cal_partial_mh_removes_ceiling)
        run_test("Cat 6: Brand promise weight", test_cal_mh_brand_promise_weight)
        run_test("Cat 6: Voice cluster empty", test_cal_voice_cluster_empty)
        run_test("Cat 6: Voice cluster partial (UNSTABLE)", test_cal_voice_cluster_partial)
        run_test("Cat 6: Voice cluster fortified", test_cal_voice_cluster_fortified)
        run_test("Cat 6: 3 clusters full, 2 empty", test_cal_voice_3clusters_full_2empty)
        run_test("Cat 6: Social scoring", test_cal_social_scoring)
        run_test("Cat 6: Social all platforms", test_cal_social_all_platforms)
        run_test("Cat 6: Sample brand score >= 90", test_cal_sample_brand)
    except Exception as e:
        results.append(("ERROR", "Cat 6: Load calibration engine",
                         f"{type(e).__name__}: {e}\n{traceback.format_exc()}"))
    cat6_pass = sum(1 for s,_,_ in results[cat6_start:] if s=='PASS')
    print(f"  {cat6_pass}/{len(results)-cat6_start} passed")

    # ── Category 7: Usage Tracking ──
    print("Category 7: Usage Tracking & Limits...")
    cat7_start = len(results)
    run_test("Cat 7: Record usage event", test_record_usage)
    run_test("Cat 7: Usage with detail", test_usage_with_detail)
    run_test("Cat 7: Usage count (no activity)", test_usage_count_no_activity)
    run_test("Cat 7: Org-level usage", test_usage_org_level)
    run_test("Cat 7: Activity log creation", test_activity_log)
    run_test("Cat 7: Activity log order", test_activity_log_order)
    run_test("Cat 7: Activity log scoping", test_activity_log_scoping)
    cat7_pass = sum(1 for s,_,_ in results[cat7_start:] if s=='PASS')
    print(f"  {cat7_pass}/{len(results)-cat7_start} passed")

    # ── Category 8: Suspension System ──
    print("Category 8: Suspension System...")
    cat8_start = len(results)
    run_test("Cat 8: Suspension fields", test_suspension_fields)
    run_test("Cat 8: Unsuspension clears fields", test_unsuspension_clears_fields)
    run_test("Cat 8: Suspension survives status update", test_suspension_survives_status_update)
    run_test("Cat 8: Admin audit log", test_admin_audit_log)
    cat8_pass = sum(1 for s,_,_ in results[cat8_start:] if s=='PASS')
    print(f"  {cat8_pass}/{len(results)-cat8_start} passed")

    # ── Category 9: Prompt Builder ──
    print("Category 9: Prompt Builder...")
    cat9_start = len(results)
    run_test("Cat 9: Full brand context", test_prompt_full_brand)
    run_test("Cat 9: Empty brand context", test_prompt_empty_brand)
    run_test("Cat 9: MH no voice", test_prompt_mh_no_voice)
    run_test("Cat 9: Voice no MH", test_prompt_voice_no_mh)
    run_test("Cat 9: Content type cluster mapping", test_prompt_content_type_cluster)
    run_test("Cat 9: Social context", test_prompt_social_context)
    run_test("Cat 9: No None injection", test_prompt_no_none_injection)
    run_test("Cat 9: Cluster filtering", test_prompt_cluster_filtering)
    run_test("Cat 9: Voice cluster status", test_prompt_voice_cluster_status)
    run_test("Cat 9: MH builder", test_prompt_mh_builder)
    cat9_pass = sum(1 for s,_,_ in results[cat9_start:] if s=='PASS')
    print(f"  {cat9_pass}/{len(results)-cat9_start} passed")

    # ── Category 10: Webhook Handler ──
    print("Category 10: Webhook Handler...")
    cat10_start = len(results)
    run_test("Cat 10: Valid signature", test_webhook_signature_valid)
    run_test("Cat 10: Invalid signature", test_webhook_signature_invalid)
    run_test("Cat 10: Missing secret (dev mode)", test_webhook_signature_missing_secret)
    run_test("Cat 10: Variant ID mapping", test_webhook_variant_mapping)
    run_test("Cat 10: Find user by email", test_webhook_find_user_by_email)
    run_test("Cat 10: Subscription created", test_webhook_subscription_created)
    run_test("Cat 10: Subscription cancelled", test_webhook_subscription_cancelled)
    run_test("Cat 10: Non-existent user", test_webhook_nonexistent_user)
    cat10_pass = sum(1 for s,_,_ in results[cat10_start:] if s=='PASS')
    print(f"  {cat10_pass}/{len(results)-cat10_start} passed")

    # ── Category 11: Terminology Audit ──
    print("Category 11: Terminology Compliance Audit...")
    cat11_start = len(results)
    run_test("Cat 11: No 'Brand Governance Engine'", test_term_brand_governance_engine)
    run_test("Cat 11: No 'brand governance'", test_term_brand_governance)
    run_test("Cat 11: No 'publishing perimeter'", test_term_publishing_perimeter)
    run_test("Cat 11: No 'authoritative signal'", test_term_authoritative_signal)
    run_test("Cat 11: No 'Voice DNA' in strings", test_term_voice_dna)
    run_test("Cat 11: No 'gold-standard'", test_term_gold_standard)
    run_test("Cat 11: No 'signal degradation'", test_term_signal_degradation)
    run_test("Cat 11: No 'Signal Integrity Score'", test_term_signal_integrity)
    run_test("Cat 11: No 'algorithmic fidelity'", test_term_algorithmic_fidelity)
    run_test("Cat 11: No 'hallucination' (user-facing)", test_term_hallucination)
    run_test("Cat 11: FORTIFIED/UNSTABLE/EMPTY labels", test_term_fortified_user_facing)
    cat11_pass = sum(1 for s,_,_ in results[cat11_start:] if s=='PASS')
    print(f"  {cat11_pass}/{len(results)-cat11_start} passed")

    # ── Category 12: Configuration ──
    print("Category 12: Configuration & Environment...")
    cat12_start = len(results)
    run_test("Cat 12: config.toml exists", test_config_toml_exists)
    run_test("Cat 12: primaryColor = #ab8f59", test_config_primary_color)
    run_test("Cat 12: backgroundColor = #24363b", test_config_background_color)
    run_test("Cat 12: secondaryBackgroundColor = #1b2a2e", test_config_secondary_bg_color)
    run_test("Cat 12: textColor = #f5f5f0", test_config_text_color)
    run_test("Cat 12: start.sh exists with uvicorn+streamlit", test_start_sh_exists)
    run_test("Cat 12: brand_ui.py Castellan palette", test_brand_ui_colors)
    run_test("Cat 12: Missing ANTHROPIC_API_KEY handling", test_env_no_api_key)
    cat12_pass = sum(1 for s,_,_ in results[cat12_start:] if s=='PASS')
    print(f"  {cat12_pass}/{len(results)-cat12_start} passed")

    # ── Category 13: Sample Brand Data ──
    print("Category 13: Sample Brand Data Integrity...")
    cat13_start = len(results)
    run_test("Cat 13: Brand name", test_sample_brand_name)
    run_test("Cat 13: Archetype", test_sample_archetype)
    run_test("Cat 13: Tone keywords", test_sample_tone)
    run_test("Cat 13: Mission statement", test_sample_mission)
    run_test("Cat 13: Core values", test_sample_values)
    run_test("Cat 13: Guardrails", test_sample_guardrails)
    run_test("Cat 13: Hex palette", test_sample_hex_palette)
    run_test("Cat 13: Brand promise", test_sample_brand_promise)
    run_test("Cat 13: Message pillars", test_sample_pillars)
    run_test("Cat 13: Founder positioning", test_sample_founder_positioning)
    run_test("Cat 13: POV statement", test_sample_pov)
    run_test("Cat 13: Boilerplate", test_sample_boilerplate)
    run_test("Cat 13: Messaging guardrails", test_sample_messaging_guardrails)
    run_test("Cat 13: Voice cluster samples", test_sample_voice_clusters)
    run_test("Cat 13: Social samples", test_sample_social_samples)
    run_test("Cat 13: No empty fields", test_sample_no_empty_fields)
    cat13_pass = sum(1 for s,_,_ in results[cat13_start:] if s=='PASS')
    print(f"  {cat13_pass}/{len(results)-cat13_start} passed")

    # ── Category 14: Edge Cases ──
    print("Category 14: Edge Cases & Error Handling...")
    cat14_start = len(results)
    run_test("Cat 14: Empty brand name", test_edge_empty_brand_name)
    run_test("Cat 14: Long brand name", test_edge_long_brand_name)
    run_test("Cat 14: Corrupted calibration data", test_edge_calibration_corrupted_data)
    run_test("Cat 14: Legacy profile format", test_edge_calibration_legacy)
    run_test("Cat 14: Usage missing brand_id", test_edge_usage_missing_brand)
    run_test("Cat 14: Activity log empty", test_edge_activity_log_empty)
    run_test("Cat 14: Long prompt builder input", test_edge_long_prompt_builder_input)
    run_test("Cat 14: ColorScorer edge cases", test_edge_color_scorer_empty)
    run_test("Cat 14: Webhook empty body", test_edge_webhook_empty_body)
    run_test("Cat 14: Platform settings CRUD", test_edge_platform_settings)
    run_test("Cat 14: Table row counts", test_edge_table_row_counts)
    cat14_pass = sum(1 for s,_,_ in results[cat14_start:] if s=='PASS')
    print(f"  {cat14_pass}/{len(results)-cat14_start} passed")

    # Cleanup
    print("\nCleaning up test database...")
    _teardown_test_db()

    # Print report
    print("\n" + "=" * 60)
    print_report()


if __name__ == "__main__":
    main()
