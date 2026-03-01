"""
tier_config.py — Single source of truth for all subscription tier definitions.
Every limit, module permission, and pricing figure lives here.
Never hardcode tier limits anywhere else in the codebase.
"""

TIER_CONFIG = {
    "solo": {
        "display_name": "Solo",
        "price_monthly_usd": 50,
        "max_brands": 3,
        "max_seats": 1,  # Solo user is automatic super-user of their account
        "modules": ["content_generator", "social_assistant", "copy_editor", "visual_audit"],
        "monthly_ai_actions": 200,
        "visual_audit_action_weight": 3,  # Each Visual Audit counts as 3 AI actions
        "lemon_squeezy_variant_ids": [1304018],
    },
    "agency": {
        "display_name": "Agency",
        "price_monthly_usd": 250,
        "max_brands": 10,
        "max_seats": 5,
        "modules": ["content_generator", "social_assistant", "copy_editor", "visual_audit"],
        "monthly_ai_actions": 800,
        "visual_audit_action_weight": 3,
        "lemon_squeezy_variant_ids": [1304027],
    },
    "enterprise": {
        "display_name": "Enterprise",
        "price_monthly_usd": 500,
        "max_brands": -1,  # -1 = unlimited
        "max_seats": 10,
        "modules": ["content_generator", "social_assistant", "copy_editor", "visual_audit"],
        "monthly_ai_actions": 1500,
        "visual_audit_action_weight": 3,
        "lemon_squeezy_variant_ids": [1303961],
    },
    "retainer": {
        # Retainer clients map to Enterprise. Billing distinction only.
        # Set manually by super-admin. Bypasses Lemon Squeezy entirely.
        "display_name": "Enterprise (Retainer)",
        "price_monthly_usd": 0,
        "max_brands": -1,
        "max_seats": 10,
        "modules": ["content_generator", "social_assistant", "copy_editor", "visual_audit"],
        "monthly_ai_actions": 1500,
        "visual_audit_action_weight": 3,
        "lemon_squeezy_variant_ids": [],
    },
    "super_admin": {
        # God mode. Platform owner only. Never exposed in UI or billing.
        "display_name": "Super Admin",
        "price_monthly_usd": 0,
        "max_brands": -1,
        "max_seats": -1,
        "modules": ["content_generator", "social_assistant", "copy_editor", "visual_audit"],
        "monthly_ai_actions": -1,  # Unlimited
        "visual_audit_action_weight": 0,
        "lemon_squeezy_variant_ids": [],
    },
}

# Protected tiers bypass Lemon Squeezy subscription checks entirely
PROTECTED_TIERS = {"retainer", "super_admin"}


def get_tier_config(tier_key: str) -> dict:
    """Return the tier config dict for a given tier key. Defaults to solo."""
    return TIER_CONFIG.get(tier_key, TIER_CONFIG["solo"])


def get_tier_from_variant_id(variant_id) -> str | None:
    """Map a Lemon Squeezy variant_id integer to a Signet tier key.
    Returns None if no match found.
    """
    try:
        vid = int(variant_id)
    except (TypeError, ValueError):
        return None
    for tier_key, config in TIER_CONFIG.items():
        if vid in config.get("lemon_squeezy_variant_ids", []):
            return tier_key
    return None
