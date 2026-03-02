"""
subscription_manager.py — Tier resolution, usage metering, and access checks.

Public API (import subscription_manager as sub_manager):
    sub_manager.resolve_user_tier(username)         → tier config dict
    sub_manager.sync_user_status(username, email)   → same (backward-compat alias)
    sub_manager.check_brand_limit(username)         → {"allowed": bool, "current": int, "max": int}
    sub_manager.check_seat_limit(org_id)            → {"allowed": bool, "current": int, "max": int}
    sub_manager.record_ai_action(username, module)  → None
    sub_manager.check_usage_limit(username)         → {"within_limit": True, "used": int, "limit": int, "percentage": float}
    sub_manager.get_usage_nudge_message(usage_info) → str | None
"""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime

import requests
import streamlit as st

import db_manager as db
from tier_config import TIER_CONFIG, PROTECTED_TIERS, get_tier_from_variant_id

logger = logging.getLogger(__name__)

# --- CONFIG ---
LS_API_KEY = os.environ.get("LEMONSQUEEZY_API_KEY", "")
LS_STORE_ID = os.environ.get("LEMONSQUEEZY_STORE_ID", "")
LS_CACHE_TTL_SECONDS = 3600  # 60 minutes

_LS_HEADERS = {
    "Accept": "application/vnd.api+json",
    "Content-Type": "application/vnd.api+json",
    "Authorization": f"Bearer {LS_API_KEY}",
}


# ── Lemon Squeezy status → subscription_status mapping ──────────────────────

_LS_STATUS_MAP = {
    "active":    "active",
    "on_trial":  "active",
    "past_due":  "past_due",
    "cancelled": "cancelled",
    "expired":   "cancelled",
    "unpaid":    "cancelled",
    "paused":    "inactive",
}


def _poll_ls_for_email(email: str) -> tuple[str | None, str | None, str | None]:
    """
    Poll Lemon Squeezy API for the most recent subscription by email.
    Returns (tier_key, subscription_status, ls_sub_id) or (None, None, None) on failure.
    """
    if not LS_API_KEY:
        logger.info("No LS_API_KEY set — skipping LS poll")
        return None, None, None

    try:
        resp = requests.get(
            "https://api.lemonsqueezy.com/v1/subscriptions",
            headers=_LS_HEADERS,
            params={"filter[user_email]": email, "filter[store_id]": LS_STORE_ID},
            timeout=10,
        )
        if resp.status_code != 200:
            logger.warning(f"LS API returned {resp.status_code} for {email!r}")
            return None, None, None

        data = resp.json().get("data", [])
        if not data:
            return None, "inactive", None

        latest = data[0]
        attrs = latest.get("attributes", {})
        ls_status = attrs.get("status", "")
        variant_id = attrs.get("variant_id")
        sub_id = str(latest.get("id", ""))

        tier_key = get_tier_from_variant_id(variant_id) or "solo"
        mapped_status = _LS_STATUS_MAP.get(ls_status, "inactive")

        return tier_key, mapped_status, sub_id

    except Exception as e:
        logger.warning(f"LS poll failed for {email!r}: {e}")
        return None, None, None


# ── Core tier resolution ─────────────────────────────────────────────────────

def resolve_user_tier(username: str) -> dict:
    """
    Resolves and returns the full tier config dict for a user.

    Resolution order:
    1. Protected tiers (retainer, super_admin) → bypass LS entirely
    2. Session cache (within TTL) → use cached tier
    3. DB cache (last_subscription_sync within 60 min) → use DB tier
    4. Poll Lemon Squeezy → update DB + session + return fresh tier

    Always returns a TIER_CONFIG dict augmented with:
        "_tier_key": str
        "_subscription_status": str
    """
    # Check session cache first
    cached_at = st.session_state.get("_tier_resolved_at", 0)
    if time.time() - cached_at < LS_CACHE_TTL_SECONDS:
        cached = st.session_state.get("tier")
        if cached and "_tier_key" in cached:
            return cached

    user = db.get_user_full(username)
    if not user:
        logger.warning(f"resolve_user_tier: user {username!r} not found")
        return _build_tier_result("solo", "inactive")

    tier_key = user.get("subscription_tier") or "solo"
    sub_status = user.get("subscription_status") or "inactive"

    # 1. Protected tiers — never check LS
    if tier_key in PROTECTED_TIERS:
        return _build_tier_result(tier_key, "active")

    # 1b. Comp access — if comp_expires_at is set and in the future, treat as active
    comp_expires = user.get("comp_expires_at")
    if comp_expires:
        try:
            if datetime.fromisoformat(comp_expires) > datetime.now():
                return _build_tier_result(tier_key, "active")
            else:
                # Comp expired — clear it and fall through to normal resolution
                db.update_user_fields(username, comp_expires_at=None, comp_reason=None)
        except (ValueError, TypeError):
            pass

    # 1c. Subscription override — if set and in the future, treat as active
    override_until = user.get("subscription_override_until")
    if override_until:
        try:
            if datetime.fromisoformat(override_until) > datetime.now():
                return _build_tier_result(tier_key, "active")
        except (ValueError, TypeError):
            pass

    # 2. DB cache — skip LS if synced recently
    last_sync = user.get("last_subscription_sync")
    if last_sync:
        try:
            synced_at = datetime.fromisoformat(last_sync)
            age = (datetime.now() - synced_at).total_seconds()
            if age < LS_CACHE_TTL_SECONDS:
                return _build_tier_result(tier_key, sub_status)
        except (ValueError, TypeError):
            pass

    # 3. Poll Lemon Squeezy
    email = user.get("email", "")
    ls_tier_key, ls_status, ls_sub_id = _poll_ls_for_email(email)

    if ls_tier_key and ls_status:
        db.set_user_subscription(username, ls_tier_key, ls_status, ls_sub_id)
        return _build_tier_result(ls_tier_key, ls_status)

    # LS poll failed — return DB values as-is
    return _build_tier_result(tier_key, sub_status)


def _build_tier_result(tier_key: str, sub_status: str) -> dict:
    """Return TIER_CONFIG dict with _tier_key and _subscription_status injected."""
    config = dict(TIER_CONFIG.get(tier_key, TIER_CONFIG["solo"]))
    config["_tier_key"] = tier_key
    config["_subscription_status"] = sub_status
    return config


def sync_user_status(username: str, email: str) -> dict:
    """
    Backward-compatible alias for resolve_user_tier.
    Returns tier config dict; also updates st.session_state['status'] for legacy guards.
    """
    tier_config = resolve_user_tier(username)
    # Keep legacy 'status' key populated for existing paywall guards
    st.session_state["status"] = tier_config.get("_subscription_status", "inactive")
    st.session_state["subscription_status"] = st.session_state["status"]
    return tier_config


def resolve_tier_from_ls_variant(variant_id) -> str | None:
    """Maps a Lemon Squeezy variant_id to a tier key."""
    return get_tier_from_variant_id(variant_id)


# ── Brand & seat limits ──────────────────────────────────────────────────────

def check_brand_limit(username: str) -> dict:
    """
    Returns {"allowed": bool, "current": int, "max": int}.
    super_admin is always allowed.
    """
    user = db.get_user_full(username)
    if not user:
        return {"allowed": False, "current": 0, "max": 0}

    org_id = user.get("org_id") or username
    tier_key = user.get("subscription_tier") or "solo"

    if tier_key == "super_admin":
        return {"allowed": True, "current": 0, "max": -1}

    max_brands = TIER_CONFIG.get(tier_key, TIER_CONFIG["solo"])["max_brands"]
    current = db.count_user_brands(org_id)

    return {
        "allowed": max_brands == -1 or current < max_brands,
        "current": current,
        "max": max_brands,
    }


def check_seat_limit(org_id: str) -> dict:
    """
    Returns {"allowed": bool, "current": int, "max": int}.
    Looks up tier via organizations table or org admin.
    """
    import sqlite3 as _sq
    conn = _sq.connect(db.DB_NAME)
    current = conn.execute(
        "SELECT COUNT(*) FROM users WHERE org_id = ?", (org_id,)
    ).fetchone()[0]
    conn.close()

    tier_key = db.get_org_tier(org_id) or "solo"

    if tier_key == "super_admin":
        return {"allowed": True, "current": current, "max": -1}

    max_seats = TIER_CONFIG.get(tier_key, TIER_CONFIG["solo"])["max_seats"]

    return {
        "allowed": max_seats == -1 or current < max_seats,
        "current": current,
        "max": max_seats,
    }


# ── Usage metering ───────────────────────────────────────────────────────────

def record_ai_action(username: str, module_name: str, action_detail: str = None):
    """Records a weighted AI action for usage metering. No-op for super_admin.
    Checks st.session_state for impersonation context."""
    user = db.get_user_full(username)
    if not user:
        return

    tier_key = user.get("subscription_tier") or "solo"
    if tier_key == "super_admin":
        return

    tier = TIER_CONFIG.get(tier_key, TIER_CONFIG["solo"])
    weight = tier["visual_audit_action_weight"] if module_name == "visual_audit" else 1

    org_id = user.get("org_id") or username
    billing_month = datetime.now().strftime("%Y-%m")

    is_impersonating = bool(st.session_state.get("admin_session"))
    if is_impersonating:
        db.record_usage_action_impersonated(username, org_id, module_name, weight, billing_month, action_detail)
    else:
        db.record_usage_action(username, org_id, module_name, weight, billing_month, action_detail)


def check_usage_limit(username: str) -> dict:
    """
    Returns {"within_limit": True, "used": int, "limit": int, "percentage": float}.
    Always returns within_limit=True — usage cap is informational (soft cap only).
    """
    user = db.get_user_full(username)
    if not user:
        return {"within_limit": True, "used": 0, "limit": 0, "percentage": 0.0}

    tier_key = user.get("subscription_tier") or "solo"

    if tier_key == "super_admin":
        return {"within_limit": True, "used": 0, "limit": -1, "percentage": 0.0}

    # Beta testers: track usage but bypass limits and nudges
    if user.get("is_beta_tester"):
        return {"within_limit": True, "used": 0, "limit": -1, "percentage": 0.0}

    tier = TIER_CONFIG.get(tier_key, TIER_CONFIG["solo"])
    limit = tier["monthly_ai_actions"]
    org_id = user.get("org_id") or username
    billing_month = datetime.now().strftime("%Y-%m")

    # Exclude impersonated actions from soft cap calculation
    import sqlite3 as _sq
    conn = _sq.connect(db.DB_NAME)
    if tier_key == "solo":
        used = conn.execute(
            "SELECT COALESCE(SUM(action_weight), 0) FROM usage_tracking "
            "WHERE username = ? AND billing_month = ? AND (is_impersonated = 0 OR is_impersonated IS NULL)",
            (username, billing_month)
        ).fetchone()[0]
    else:
        used = conn.execute(
            "SELECT COALESCE(SUM(action_weight), 0) FROM usage_tracking "
            "WHERE org_id = ? AND billing_month = ? AND (is_impersonated = 0 OR is_impersonated IS NULL)",
            (org_id, billing_month)
        ).fetchone()[0]
    conn.close()

    pct = (used / limit * 100) if limit > 0 else 0.0

    return {
        "within_limit": True,  # Soft cap — never block
        "used": used,
        "limit": limit,
        "percentage": pct,
    }


def get_usage_nudge_message(usage_info: dict) -> str | None:
    """
    Returns a nudge message string if usage is at/near cap, or None if no nudge needed.
    """
    pct = usage_info.get("percentage", 0)
    used = usage_info.get("used", 0)
    limit = usage_info.get("limit", 0)

    if limit <= 0:
        return None

    if pct >= 100:
        return (
            "You've reached your monthly usage limit. You can keep working \u2014 if your needs have grown "
            "beyond your current plan, we'd love to talk about the right fit. "
            "Contact us at support@castellanpr.com."
        )
    elif pct >= 80:
        return "You're approaching your monthly usage limit. No rush \u2014 just a heads up."

    return None
