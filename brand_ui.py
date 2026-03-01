"""
brand_ui.py — Single source of truth for Castellan/Signet brand UI constants.

Shield SVGs, severity rendering, module help text, brand colors.
Imported by app.py, admin_panel.py, and any future UI modules.
"""

# ─── BRAND COLORS ─────────────────────────────────────────────────────────────
BRAND_COLORS = {
    "dark": "#24363b",
    "gold": "#ab8f59",
    "sage": "#5c6b61",
    "cream": "#f5f5f0",
    "charcoal": "#3d3d3d",
    "copper": "#a6784d",
    "teal_dark": "#1b2a2e",
}

# ─── SHIELD SVGs (20x24px inline) ────────────────────────────────────────────
# Matching the Signet logo shield silhouette. Render via st.markdown(unsafe_allow_html=True).

SHIELD_ALIGNED = (
    '<svg width="20" height="24" viewBox="0 0 20 24" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M10 0L20 4V12C20 18.6 14.2 22.8 10 24C5.8 22.8 0 18.6 0 12V4L10 0Z" fill="#ab8f59"/>'
    '</svg>'
)

SHIELD_DRIFT = (
    '<svg width="20" height="24" viewBox="0 0 20 24" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M10 0L20 4V12C20 18.6 14.2 22.8 10 24C5.8 22.8 0 18.6 0 12V4L10 0Z" '
    'fill="none" stroke="#ab8f59" stroke-width="1.5"/>'
    '<line x1="7" y1="5" x2="12" y2="13" stroke="#3d3d3d" stroke-width="1.5" stroke-linecap="round"/>'
    '<line x1="12" y1="13" x2="9" y2="19" stroke="#3d3d3d" stroke-width="1.5" stroke-linecap="round"/>'
    '</svg>'
)

SHIELD_DEGRADATION = (
    '<svg width="20" height="24" viewBox="0 0 20 24" xmlns="http://www.w3.org/2000/svg">'
    '<path d="M10 0L20 4V12C20 18.6 14.2 22.8 10 24C5.8 22.8 0 18.6 0 12V4L10 0Z" fill="#24363b"/>'
    '<line x1="6" y1="4" x2="13" y2="12" stroke="#a6784d" stroke-width="2" stroke-linecap="round"/>'
    '<line x1="13" y1="12" x2="8" y2="20" stroke="#a6784d" stroke-width="2" stroke-linecap="round"/>'
    '<line x1="14" y1="6" x2="10" y2="15" stroke="#a6784d" stroke-width="1.5" stroke-linecap="round"/>'
    '</svg>'
)

# ─── SEVERITY RENDERING ──────────────────────────────────────────────────────

_SEVERITY_CONFIG = {
    "aligned": {
        "shield": SHIELD_ALIGNED,
        "label": "ALIGNED",
        "color": "#ab8f59",
    },
    "drift": {
        "shield": SHIELD_DRIFT,
        "label": "DRIFT",
        "color": "#3d3d3d",
    },
    "degradation": {
        "shield": SHIELD_DEGRADATION,
        "label": "DEGRADATION",
        "color": "#a6784d",
    },
    "note": {
        "shield": None,
        "label": "",
        "color": "#5c6b61",
    },
}


def render_severity(level: str, text: str) -> str:
    """Return an HTML string for a severity indicator.

    Args:
        level: One of "aligned", "drift", "degradation", "note".
        text: The message to display alongside the indicator.

    Returns:
        An HTML string safe for st.markdown(unsafe_allow_html=True).
    """
    cfg = _SEVERITY_CONFIG.get(level, _SEVERITY_CONFIG["note"])

    if level == "note":
        return (
            f'<span style="color:{cfg["color"]}; font-size:0.8rem; font-style:italic;">'
            f'{text}</span>'
        )

    shield = cfg["shield"]
    label = cfg["label"]
    color = cfg["color"]
    return (
        f'<span style="display:inline-flex; align-items:center; gap:6px; font-size:0.8rem; line-height:1.4;">'
        f'{shield}'
        f'<span style="font-variant:small-caps; font-weight:700; color:{color};">{label}</span>'
        f'<span style="color:#3d3d3d;">{text}</span>'
        f'</span>'
    )


# ─── HELP BUTTON CSS ─────────────────────────────────────────────────────────

HELP_EXPANDER_CSS = """
<style>
/* Signet help expander — gold accent */
div[data-testid="stExpander"] details[data-testid="stExpanderDetails"] {
    border-left: 3px solid #ab8f59;
}
div[data-testid="stExpander"] summary span[data-testid="stMarkdownContainer"] p {
    font-weight: 700;
    color: #ab8f59;
    font-size: 0.85rem;
    letter-spacing: 0.05em;
}
</style>
"""

# ─── MODULE HELP TEXT ─────────────────────────────────────────────────────────
# Exact approved text from DEV_LOG. Visual Audit uses the updated version
# (no COST NOTE — action costs are not user-facing per Part E).

HELP_CONTENT_GENERATOR = {
    "what_it_does": (
        "Generates brand-aligned content calibrated to your brand profile "
        "\u2014 strategy, message house, and voice samples."
    ),
    "what_to_provide": (
        "Describe what you need: \u201cWrite a press release about our Series B\u201d "
        "or \u201cDraft homepage hero copy.\u201d Include the content type so the engine "
        "selects the right voice cluster."
    ),
    "what_you_get": (
        "Content written in your brand\u2019s voice, drawing from your approved message "
        "pillars and proof points. Includes a rationale section showing which brand "
        "elements informed the output."
    ),
    "calibration_note": (
        "The more complete your brand profile, the more precise the output. An incomplete "
        "profile produces more generic results \u2014 not wrong, but less distinctly yours."
    ),
}

HELP_SOCIAL_ASSISTANT = {
    "what_it_does": (
        "Creates social media content calibrated to your brand\u2019s voice and social "
        "presence. Optimized for platform-specific formats."
    ),
    "what_to_provide": (
        "A topic or prompt, and which platform (LinkedIn, Twitter/X, or other). "
        "For founder-voice posts, specify \u201cfounder voice\u201d to blend thought "
        "leadership patterns."
    ),
    "what_you_get": (
        "Platform-appropriate social content aligned with your brand\u2019s tone, message "
        "pillars, and social media reference samples. Includes a rationale section."
    ),
    "calibration_note": (
        "Upload at least 3 social media samples in the Brand Architect. Without them, "
        "the engine calibrates from your general brand voice \u2014 usable, but less "
        "tuned to your social presence."
    ),
}

HELP_COPY_EDITOR = {
    "what_it_does": (
        "Audits your draft content against your brand profile. Flags brand drift and "
        "brand degradation \u2014 misaligned tone, unapproved claims, guardrail violations, "
        "and generic language."
    ),
    "what_to_provide": (
        "Paste your draft text. The engine works best when you specify the content type "
        "(press release, blog post, email, etc.) so it checks against the right voice cluster."
    ),
    "what_you_get": (
        "A line-by-line review with specific findings. Each issue cites which brand "
        "guideline it relates to, rates it as aligned / drift / degradation, and "
        "suggests a brand-aligned alternative."
    ),
    "calibration_note": (
        "The more complete your message house, the deeper the audit. Without message "
        "pillars and proof points, the engine can check tone but cannot verify positioning "
        "or claim accuracy."
    ),
}

HELP_VISUAL_AUDIT = {
    "what_it_does": (
        "Analyzes uploaded images (screenshots, mockups, ad creatives) for brand "
        "compliance across three layers: color palette accuracy, visual identity "
        "consistency, and copy alignment."
    ),
    "what_to_provide": (
        "Upload a screenshot or image file (PNG, JPG, WEBP). Optionally describe "
        "what the asset is \u2014 \u201clanding page hero\u201d or \u201cemail header\u201d "
        "\u2014 for more targeted analysis."
    ),
    "what_you_get": (
        "A unified compliance report with an overall score (0\u2013100). Color compliance "
        "is checked deterministically. Visual identity and copy alignment use AI analysis. "
        "Each finding references a specific brand guideline."
    ),
    "calibration_note": (
        "A complete brand profile with hex palette, message house, and voice samples "
        "produces the most thorough audit. The engine checks what it can with whatever "
        "data you\u2019ve provided."
    ),
}

_MODULE_HELP_MAP = {
    "visual_audit": HELP_VISUAL_AUDIT,
    "copy_editor": HELP_COPY_EDITOR,
    "content_generator": HELP_CONTENT_GENERATOR,
    "social_assistant": HELP_SOCIAL_ASSISTANT,
}


def render_module_help(module_key: str):
    """Render a styled help expander for a module.

    Call this right after the module's st.title(). Uses Streamlit internally.

    Args:
        module_key: One of "visual_audit", "copy_editor",
                    "content_generator", "social_assistant".
    """
    import streamlit as st

    help_data = _MODULE_HELP_MAP.get(module_key)
    if not help_data:
        return

    st.markdown(HELP_EXPANDER_CSS, unsafe_allow_html=True)

    with st.expander("HOW THIS MODULE WORKS", expanded=False):
        st.markdown(
            f"**WHAT IT DOES:**\n{help_data['what_it_does']}",
        )
        st.markdown(
            f"**WHAT TO PROVIDE:**\n{help_data['what_to_provide']}",
        )
        st.markdown(
            f"**WHAT YOU GET BACK:**\n{help_data['what_you_get']}",
        )
        st.markdown(
            f'<div style="margin-top:8px; padding:8px 12px; background:rgba(171,143,89,0.08); '
            f'border-left:2px solid #ab8f59; font-size:0.85rem; color:#3d3d3d;">'
            f'<strong>CALIBRATION NOTE:</strong> {help_data["calibration_note"]}</div>',
            unsafe_allow_html=True,
        )
