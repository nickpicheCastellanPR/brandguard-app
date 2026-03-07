"""
content_types.py — Single source of truth for content types across all modules.

Every module (Content Generator, Copy Editor, Social Assistant, Visual Audit)
references this file for content type definitions, word ranges, and cluster mappings.
Never hardcode content type lists anywhere else in the codebase.
"""
from __future__ import annotations


# ── Content Types (used by Content Generator & Copy Editor) ──────────────────

CONTENT_TYPES = {
    # ── Corporate Affairs ──
    "press_release": {
        "label": "Press Release",
        "cluster": "Corporate Affairs",
        "lengths": {"brief": (250, 350), "standard": (400, 600), "detailed": (700, 900)},
        "modules": ["generator", "editor"],
    },
    "fact_sheet": {
        "label": "Fact Sheet",
        "cluster": "Corporate Affairs",
        "lengths": {"brief": (200, 300), "standard": (350, 500), "detailed": (600, 800)},
        "modules": ["generator", "editor"],
    },
    "company_statement": {
        "label": "Company Statement",
        "cluster": "Corporate Affairs",
        "lengths": {"brief": (100, 200), "standard": (250, 400), "detailed": (500, 700)},
        "modules": ["generator", "editor"],
    },
    "investor_update": {
        "label": "Investor Update",
        "cluster": "Corporate Affairs",
        "lengths": {"brief": (300, 450), "standard": (500, 750), "detailed": (800, 1100)},
        "modules": ["generator", "editor"],
    },
    "board_report": {
        "label": "Board Report",
        "cluster": "Corporate Affairs",
        "lengths": {"brief": (400, 600), "standard": (700, 1000), "detailed": (1200, 1600)},
        "modules": ["generator", "editor"],
    },

    # ── Crisis & Response ──
    "incident_report": {
        "label": "Incident Report",
        "cluster": "Crisis & Response",
        "lengths": {"brief": (200, 350), "standard": (400, 600), "detailed": (700, 1000)},
        "modules": ["generator", "editor"],
    },
    "holding_statement": {
        "label": "Holding Statement",
        "cluster": "Crisis & Response",
        "lengths": {"brief": (100, 200), "standard": (250, 400), "detailed": (500, 650)},
        "modules": ["generator", "editor"],
    },
    "customer_apology": {
        "label": "Customer Apology",
        "cluster": "Crisis & Response",
        "lengths": {"brief": (150, 250), "standard": (300, 500), "detailed": (600, 800)},
        "modules": ["generator", "editor"],
    },
    "crisis_faq": {
        "label": "Crisis FAQ",
        "cluster": "Crisis & Response",
        "lengths": {"brief": (300, 500), "standard": (600, 900), "detailed": (1000, 1400)},
        "modules": ["generator", "editor"],
    },

    # ── Internal Leadership ──
    "all_hands_memo": {
        "label": "All-Hands Memo",
        "cluster": "Internal Leadership",
        "lengths": {"brief": (200, 350), "standard": (400, 650), "detailed": (700, 1000)},
        "modules": ["generator", "editor"],
    },
    "team_update": {
        "label": "Team Update",
        "cluster": "Internal Leadership",
        "lengths": {"brief": (150, 250), "standard": (300, 500), "detailed": (600, 800)},
        "modules": ["generator", "editor"],
    },
    "policy_announcement": {
        "label": "Policy Announcement",
        "cluster": "Internal Leadership",
        "lengths": {"brief": (200, 350), "standard": (400, 600), "detailed": (700, 900)},
        "modules": ["generator", "editor"],
    },
    "org_change_announcement": {
        "label": "Org Change Announcement",
        "cluster": "Internal Leadership",
        "lengths": {"brief": (200, 350), "standard": (400, 650), "detailed": (700, 1000)},
        "modules": ["generator", "editor"],
    },

    # ── Thought Leadership ──
    "op_ed": {
        "label": "Op-Ed",
        "cluster": "Thought Leadership",
        "lengths": {"brief": (600, 800), "standard": (900, 1200), "detailed": (1400, 1800)},
        "modules": ["generator", "editor"],
    },
    "blog_post": {
        "label": "Blog Post",
        "cluster": "Thought Leadership",
        "lengths": {"brief": (500, 700), "standard": (800, 1200), "detailed": (1400, 1800)},
        "modules": ["generator", "editor"],
    },
    "keynote_speech": {
        "label": "Keynote Speech",
        "cluster": "Thought Leadership",
        "lengths": {"brief": (500, 700), "standard": (900, 1300), "detailed": (1500, 2000)},
        "modules": ["generator", "editor"],
    },
    "conference_talk": {
        "label": "Conference Talk",
        "cluster": "Thought Leadership",
        "lengths": {"brief": (400, 600), "standard": (700, 1000), "detailed": (1200, 1600)},
        "modules": ["generator", "editor"],
    },
    "byline_article": {
        "label": "Byline Article",
        "cluster": "Thought Leadership",
        "lengths": {"brief": (500, 700), "standard": (800, 1200), "detailed": (1400, 1800)},
        "modules": ["generator", "editor"],
    },

    # ── Brand Marketing ──
    "website_copy": {
        "label": "Website Copy",
        "cluster": "Brand Marketing",
        "lengths": {"brief": (100, 200), "standard": (250, 400), "detailed": (500, 700)},
        "modules": ["generator", "editor"],
    },
    "product_launch_email": {
        "label": "Product Launch Email",
        "cluster": "Brand Marketing",
        "lengths": {"brief": (150, 250), "standard": (300, 500), "detailed": (600, 800)},
        "modules": ["generator", "editor"],
    },
    "newsletter": {
        "label": "Newsletter",
        "cluster": "Brand Marketing",
        "lengths": {"brief": (300, 500), "standard": (600, 900), "detailed": (1000, 1400)},
        "modules": ["generator", "editor"],
    },
    "social_campaign_brief": {
        "label": "Social Media Campaign Brief",
        "cluster": "Brand Marketing",
        "lengths": {"brief": (200, 350), "standard": (400, 600), "detailed": (700, 1000)},
        "modules": ["generator", "editor"],
    },
    "product_description": {
        "label": "Product Description",
        "cluster": "Brand Marketing",
        "lengths": {"brief": (50, 100), "standard": (150, 250), "detailed": (300, 500)},
        "modules": ["generator", "editor"],
    },
    "customer_email": {
        "label": "Customer Email",
        "cluster": "Brand Marketing",
        "lengths": {"brief": (100, 200), "standard": (250, 400), "detailed": (500, 700)},
        "modules": ["generator", "editor"],
    },

    # ── Custom ──
    "custom": {
        "label": "Other / Custom",
        "cluster": None,
        "lengths": {"brief": (200, 400), "standard": (500, 800), "detailed": (1000, 1500)},
        "modules": ["generator", "editor"],
    },
}


# ── Social platform specs (used by Social Assistant) ─────────────────────────

SOCIAL_PLATFORMS = {
    "linkedin": {
        "label": "LinkedIn",
        "lengths": {"brief": (80, 150), "standard": (150, 250), "detailed": (250, 400)},
        "max_chars": 3000,
        "notes": "No hashtags. No outbound links in body. Link goes in first comment.",
    },
    "twitter": {
        "label": "Twitter / X",
        "lengths": {"brief": (30, 50), "standard": (50, 80), "detailed": (80, 140)},
        "max_chars": 280,
        "notes": "Character count is hard limit. Threads supported for longer content.",
    },
    "instagram": {
        "label": "Instagram",
        "lengths": {"brief": (40, 80), "standard": (80, 150), "detailed": (150, 300)},
        "max_chars": 2200,
        "notes": "Caption length. Hashtags acceptable (3-5 max). Visual-first platform.",
    },
}


# ── Visual asset types (used by Visual Audit) ────────────────────────────────

VISUAL_ASSET_TYPES = {
    "marketing_page": {"label": "Marketing Page / Website", "notes": "Full page screenshot or section"},
    "email_template": {"label": "Email Template", "notes": "HTML email or screenshot"},
    "social_graphic": {"label": "Social Media Graphic", "notes": "Post image, banner, or ad creative"},
    "presentation_slide": {"label": "Presentation Slide", "notes": "Individual slide or deck screenshot"},
    "document_header": {"label": "Document / Letterhead", "notes": "PDF, Word doc header, or branded template"},
    "logo_usage": {"label": "Logo Usage", "notes": "Logo placement in context"},
    "advertisement": {"label": "Advertisement", "notes": "Digital ad, print ad, or banner"},
    "other_visual": {"label": "Other Visual Asset", "notes": "Any branded visual not listed above"},
}


# ── Voice cluster names (canonical list, matches prompt_builder.py) ──────────

VOICE_CLUSTER_NAMES = [
    "Corporate Affairs",
    "Crisis & Response",
    "Internal Leadership",
    "Thought Leadership",
    "Brand Marketing",
]


# ── Helper functions ─────────────────────────────────────────────────────────

def get_content_types_for_module(module: str) -> dict:
    """Get the content types available for a specific module ('generator' or 'editor')."""
    return {k: v for k, v in CONTENT_TYPES.items() if module in v["modules"]}


def get_type_key_by_label(label: str) -> str:
    """Reverse-lookup: get type key from display label. Returns 'custom' if not found."""
    for key, config in CONTENT_TYPES.items():
        if config["label"] == label:
            return key
    return "custom"


def get_labels_for_module(module: str) -> list[str]:
    """Get a flat list of display labels for a module's dropdown."""
    return [v["label"] for k, v in CONTENT_TYPES.items() if module in v["modules"]]


def get_cluster_for_type(type_key: str) -> str | None:
    """Get the voice cluster for a content type key."""
    if type_key in CONTENT_TYPES:
        return CONTENT_TYPES[type_key]["cluster"]
    return None


def get_cluster_for_label(label: str) -> str | None:
    """Get the voice cluster for a content type label."""
    return get_cluster_for_type(get_type_key_by_label(label))


def get_word_range(type_key: str, length_setting: str) -> tuple[int, int]:
    """Get the (min, max) word range for a content type at a given length setting."""
    if type_key in CONTENT_TYPES:
        return CONTENT_TYPES[type_key]["lengths"].get(length_setting, (300, 600))
    return (300, 600)


def get_length_label(type_key: str, length_setting: str) -> str:
    """Get a display label like 'Standard (400-600 words)' for the slider."""
    word_range = get_word_range(type_key, length_setting)
    names = {"brief": "Brief", "standard": "Standard", "detailed": "Detailed"}
    name = names.get(length_setting, "Standard")
    return f"{name} ({word_range[0]}-{word_range[1]} words)"


def get_social_platform_key(display_name: str) -> str:
    """Map a display name like 'LinkedIn' or 'X (Twitter)' to a platform key."""
    name_lower = display_name.lower()
    if "linkedin" in name_lower:
        return "linkedin"
    if "twitter" in name_lower or "x (" in name_lower:
        return "twitter"
    if "instagram" in name_lower:
        return "instagram"
    return "linkedin"


def get_social_length_label(platform_key: str, length_setting: str) -> str:
    """Get a display label for social platform word range."""
    platform = SOCIAL_PLATFORMS.get(platform_key, SOCIAL_PLATFORMS["linkedin"])
    word_range = platform["lengths"].get(length_setting, (100, 200))
    names = {"brief": "Brief", "standard": "Standard", "detailed": "Detailed"}
    name = names.get(length_setting, "Standard")
    return f"{name} ({word_range[0]}-{word_range[1]} words)"
