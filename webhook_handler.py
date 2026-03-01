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
    import sqlite3
    conn = sqlite3.connect(db.DB_NAME)
    result = conn.execute(
        "SELECT username FROM users WHERE email = ?", (email,)
    ).fetchone()
    conn.close()
    return result[0] if result else None


def _handle_subscription_active(email: str, tier_key: str, sub_id: str, variant_id: str):
    """Set user to active status for the resolved tier."""
    username = _find_username_by_email(email)
    if not username:
        logger.warning(f"Webhook: no user found for email {email!r}")
        return
    db.set_user_subscription(username, tier_key, "active", sub_id, variant_id)
    logger.info(f"Webhook: activated {username!r} → tier={tier_key!r}")


def _update_user_by_email(email: str, tier_key: str, status: str, sub_id: str):
    """Update subscription status for user found by email."""
    username = _find_username_by_email(email)
    if not username:
        logger.warning(f"Webhook: no user found for email {email!r}")
        return
    db.set_user_subscription(username, tier_key, status, sub_id)
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

    logger.info(f"Webhook event: {event!r} | email={email!r} | tier={tier_key!r}")

    if event == "subscription_created":
        _handle_subscription_active(email, tier_key, sub_id, str(variant_id))
    elif event == "subscription_updated":
        _handle_subscription_active(email, tier_key, sub_id, str(variant_id))
    elif event == "subscription_cancelled":
        _update_user_by_email(email, tier_key, "cancelled", sub_id)
    elif event == "subscription_payment_failed":
        _update_user_by_email(email, tier_key, "past_due", sub_id)
    elif event == "subscription_resumed":
        _handle_subscription_active(email, tier_key, sub_id, str(variant_id))
    else:
        logger.info(f"Webhook: unhandled event {event!r}, ignoring")

    return {"status": "ok"}


@app.get("/health")
async def health():
    return {"status": "ok"}
