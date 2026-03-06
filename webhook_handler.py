"""
webhook_handler.py — FastAPI receiver for Lemon Squeezy subscription webhooks.

Run alongside Streamlit via start.sh:
    uvicorn webhook_handler:app --host 0.0.0.0 --port 8001
"""
from __future__ import annotations

import hmac
import hashlib
import json
import logging
import os
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
import db_manager as db
from tier_config import get_tier_from_variant_id

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

WEBHOOK_SECRET = os.environ.get("LEMONSQUEEZY_WEBHOOK_SECRET", "")


def verify_signature(payload_body: bytes, signature: str) -> bool:
    """Verify HMAC-SHA256 signature from Lemon Squeezy."""
    if not WEBHOOK_SECRET:
        logger.warning("LEMONSQUEEZY_WEBHOOK_SECRET not set — skipping signature check")
        return True  # Dev fallback: allow unsigned in local env without secret
    expected = hmac.new(WEBHOOK_SECRET.encode(), payload_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def _find_username_by_email(email: str) -> str | None:
    """Looks up a username by email address."""
    return db.get_user_by_email(email)


def _resolve_username(email: str, payload: dict) -> str | None:
    """Resolve username from custom_data.user_id first, then email fallback."""
    custom_data = payload.get("meta", {}).get("custom_data", {})
    user_id = custom_data.get("user_id")
    if user_id:
        user = db.get_user_full(user_id)
        if user:
            return user_id
    return _find_username_by_email(email)


def _store_subscription_dates(username: str, attrs: dict):
    """Store renews_at and ends_at from subscription attributes."""
    renews_at = attrs.get("renews_at")
    ends_at = attrs.get("ends_at")
    updates = {}
    if renews_at:
        updates["renews_at"] = renews_at
    if ends_at:
        updates["ends_at"] = ends_at
    if updates:
        db.update_user_fields(username, **updates)


def _handle_subscription_active(username: str, tier_key: str, sub_id: str, variant_id: str, attrs: dict = None):
    """Set user to active status for the resolved tier."""
    if not username:
        return
    # Capture old tier for analytics
    old_user = db.get_user_full(username)
    old_tier = old_user.get('subscription_tier', 'solo') if old_user else 'solo'

    db.set_user_subscription(username, tier_key, "active", sub_id, variant_id)
    logger.info(f"Webhook: activated {username!r} → tier={tier_key!r}")

    # Store subscription period dates
    if attrs:
        _store_subscription_dates(username, attrs)

    # Clear trial expired flag if they subscribe
    trial_info = db.get_trial_info(username)
    if trial_info and trial_info.get("trial_expired"):
        db.update_user_fields(username, trial_expired=False if db.is_postgres() else 0)

    # Analytics: subscription changed
    if old_tier != tier_key:
        db.track_event("subscription_changed", username, metadata={
            "old_tier": old_tier, "new_tier": tier_key,
            "trigger": "checkout_completed",
        })


def _update_user_subscription(username: str, tier_key: str, status: str, sub_id: str, attrs: dict = None):
    """Update subscription status for a resolved user."""
    if not username:
        return
    db.set_user_subscription(username, tier_key, status, sub_id)
    if attrs:
        _store_subscription_dates(username, attrs)
    logger.info(f"Webhook: updated {username!r} → tier={tier_key!r}, status={status!r}")


@app.post("/webhooks/lemonsqueezy")
async def handle_ls_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("X-Signature", "")

    if not verify_signature(body, sig):
        logger.warning("Webhook: invalid signature")
        raise HTTPException(status_code=401, detail="Invalid signature")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event = payload.get("meta", {}).get("event_name", "")
    attrs = payload.get("data", {}).get("attributes", {})

    email = attrs.get("user_email", "")
    variant_id = attrs.get("variant_id")
    sub_id = str(payload.get("data", {}).get("id", ""))

    tier_key = get_tier_from_variant_id(variant_id) or "solo"

    # Resolve username: custom_data.user_id first, then email lookup
    username = _resolve_username(email, payload)

    logger.info(f"Webhook event: {event!r} | email={email!r} | user={username!r} | tier={tier_key!r}")

    if not username:
        logger.warning(f"Webhook: no user found for email={email!r}, event={event!r}")
        return {"status": "ok", "note": "user_not_found"}

    if event == "subscription_created":
        _handle_subscription_active(username, tier_key, sub_id, str(variant_id), attrs)
    elif event == "subscription_updated":
        _handle_subscription_active(username, tier_key, sub_id, str(variant_id), attrs)
    elif event == "subscription_cancelled":
        # Analytics: capture tenure and actions before updating status
        _cancel_data = db.get_user_full(username)
        _tenure_days = 0
        if _cancel_data and _cancel_data.get('created_at'):
            try:
                _signup = datetime.fromisoformat(_cancel_data['created_at'].replace('Z', ''))
                _tenure_days = (datetime.now() - _signup).days
            except (ValueError, TypeError):
                pass
        _total_actions = db.get_monthly_usage_user(username, datetime.now().strftime("%Y-%m"))
        db.track_event("subscription_cancelled", username, metadata={
            "tier": tier_key,
            "tenure_days": _tenure_days,
            "total_actions": _total_actions,
        })
        _update_user_subscription(username, tier_key, "cancelled", sub_id, attrs)
    elif event == "subscription_payment_failed":
        # Grace period: set to past_due, don't lock immediately
        _update_user_subscription(username, tier_key, "past_due", sub_id, attrs)
        logger.info(f"Webhook: payment failed for {username!r} — set to past_due (grace period)")
    elif event == "subscription_resumed":
        _handle_subscription_active(username, tier_key, sub_id, str(variant_id), attrs)
    else:
        logger.info(f"Webhook: unhandled event {event!r}, ignoring")

    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "ok"}
