import streamlit as st
from PIL import Image
import os
import re
import json

import time # Added for Session Expiry
import uuid
from logic import SignetLogic
import db_manager as db
import subscription_manager as sub_manager
import admin_panel
import visual_audit
import html
from prompt_builder import build_brand_context, build_social_context, build_mh_context
from content_types import (CONTENT_TYPES, SOCIAL_PLATFORMS, VISUAL_ASSET_TYPES,
                           CLUSTER_DISPLAY_NAMES,
                           get_cluster_for_label,
                           get_word_range, get_length_label, get_social_platform_key,
                           get_social_length_label, get_ordered_display_options,
                           get_key_from_display,
                           VOICE_CLUSTER_NAMES as CT_CLUSTER_NAMES)
import brand_ui
import email_helper

# --- PAGE CONFIG ---
icon_path = "Signet_Icon_Color.png"
if os.path.exists(icon_path):
    page_icon = Image.open(icon_path)
else:
    page_icon = None 

st.set_page_config(
    page_title="Signet", 
    page_icon=page_icon, 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 1. SECURITY & PERFORMANCE: SINGLETON LOGIC ---
# Fix: Cache the logic engine so it doesn't reload on every click (Oliver's Suggestion #2)
@st.cache_resource
def get_logic_engine():
    return SignetLogic()

try:
    logic_engine = get_logic_engine()
except Exception as e:
    st.error(f"🚨 CRITICAL STARTUP ERROR: {e}")
    st.code(f"Details: {type(e).__name__}", language="text")
    st.stop()

# Initialize DB (This will create the V3 schema from db_manager)
if 'db_init_v3' not in st.session_state:
    db.init_db()
    st.session_state['db_init_v3'] = True

# --- 2. SECURITY: SESSION EXPIRY WATCHDOG ---
# Fix: Force logout after 60 minutes of inactivity (Oliver's Suggestion #5)
if st.session_state.get('authenticated'):
    current_ts = time.time()
    last_active = st.session_state.get('last_active_ts', current_ts)
    
    # 3600 seconds = 1 hour
    if current_ts - last_active > 3600:
        st.session_state.clear()
        st.warning("Session expired due to inactivity. Please log in again.")
        st.stop()
    
    st.session_state['last_active_ts'] = current_ts

# --- GOOGLE FONTS (must load before any CSS references Montserrat) ---
st.markdown('<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600;700;900&display=swap" rel="stylesheet">', unsafe_allow_html=True)

# --- THE CASTELLAN IDENTITY SYSTEM (CSS) ---
st.markdown("""
<style>
    /* 1. PALETTE DEFINITION */
    :root {
        --c-teal-deep: #24363b;   /* Main Background */
        --c-teal-dark: #1b2a2e;   /* Input Backgrounds */
        --c-gold-muted: #ab8f59;  /* Accents & Borders */
        --c-cream: #f5f5f0;       /* Sidebar & Text */
        --c-sage: #5c6b61;        /* Success/Secondary */
        --c-charcoal: #3d3d3d;    /* Sidebar Text */
    }

    /* 2. LAYOUT & BACKGROUNDS */
    .stApp {
        background-color: var(--c-teal-deep);
        color: var(--c-cream);
    }
    
    /* THE SIDEBAR - CREAM */
    section[data-testid="stSidebar"] {
        background-color: var(--c-cream) !important;
        border-right: 1px solid var(--c-gold-muted);
    }
    
    /* Sidebar Text Overrides (Dark on Cream) */
    section[data-testid="stSidebar"] * {
        color: var(--c-teal-deep) !important;
    }
    
    /* 3. NAVIGATION MENU (Clean List) */
    div[role="radiogroup"] label > div:first-child { display: none !important; }
    div[role="radiogroup"] label {
        padding: 12px 20px !important;
        border-radius: 0px !important;
        border-left: 3px solid transparent !important;
        margin-bottom: 4px !important;
        transition: all 0.2s ease;
        font-weight: 600 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
        font-family: 'Montserrat', 'Helvetica Neue', Arial, sans-serif !important;
    }
    div[role="radiogroup"] label:hover {
        background-color: rgba(36, 54, 59, 0.05) !important;
        border-left: 3px solid var(--c-gold-muted) !important;
        padding-left: 25px !important;
    }
    div[role="radiogroup"] label[data-checked="true"] {
        background-color: var(--c-teal-deep) !important;
        color: var(--c-cream) !important;
        border-left: 3px solid var(--c-gold-muted) !important;
    }
    div[role="radiogroup"] label[data-checked="true"] * { color: var(--c-cream) !important; }

    /* 4. HEADERS */
    h1 {
        font-family: 'Montserrat', 'Helvetica Neue', Arial, sans-serif;
        font-weight: 900 !important;
        text-transform: uppercase;
        color: var(--c-cream) !important;
        padding-bottom: 15px;
        border-bottom: 1px solid var(--c-gold-muted);
        letter-spacing: 0.08em;
    }

    h2, h3 { font-family: 'Montserrat', 'Helvetica Neue', Arial, sans-serif; color: var(--c-gold-muted) !important; text-transform: uppercase; font-weight: 700; }

    /* 5. INPUTS (FIXED VISIBILITY) */
    .stTextInput input, 
    .stTextArea textarea, 
    .stSelectbox div[data-baseweb="select"] > div,
    .stSelectbox div[data-baseweb="select"] span {
        background-color: var(--c-teal-dark) !important;
        border: 1px solid var(--c-sage) !important;
        color: #FFFFFF !important;       /* FORCE WHITE TEXT */
        caret-color: #FFFFFF !important; /* FORCE WHITE CURSOR */
        -webkit-text-fill-color: #FFFFFF !important;
        border-radius: 0px !important;
    }
    
    /* Placeholder Text Color */
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: #A0A0A0 !important;
        -webkit-text-fill-color: #A0A0A0 !important;
    }

    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: var(--c-gold-muted) !important;
        box-shadow: 0 0 8px rgba(171, 143, 89, 0.2) !important;
    }
    /* --- EXPANDER HEADER FIXES (HTML NATIVE) --- */

    /* 1. Target the Expander Container via Data Attribute */
    [data-testid="stExpander"] {
        background-color: transparent !important;
        border: none !important;
        color: var(--c-gold-muted) !important;
    }

    /* 2. Target the Summary (The Clickable Header Bar) */
    [data-testid="stExpander"] details > summary {
        background-color: var(--c-navy-dark) !important;
        border: 1px solid var(--c-gold-muted) !important;
        border-radius: 4px;
        color: var(--c-gold-muted) !important;
        transition: all 0.2s ease;
    }

    /* 3. Target the Content INSIDE the Summary (Text & Icon) */
    /* We use 'currentColor' so they automatically change on hover */
    [data-testid="stExpander"] details > summary > * {
        color: inherit !important;
        fill: currentColor !important;
        stroke: currentColor !important;
        font-weight: 600 !important;
    }

    /* 4. Target the Paragraph specifically (Double-tap for safety) */
    [data-testid="stExpander"] details > summary p {
        color: inherit !important;
    }

    /* 5. Hover State */
    [data-testid="stExpander"] details > summary:hover {
        border-color: var(--c-gold-signal) !important;
        color: var(--c-gold-signal) !important;
    }
    
/* --- DROPDOWN & POPOVER FIXES --- */

    /* 1. Target the portal and all parent containers (Existing Logic Preserved) */
    div[data-testid="portal"],
    div[data-testid="portal"] > div,
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    #portal,
    #portal > div {
        background-color: var(--c-gold-muted) !important;
        background: var(--c-gold-muted) !important;
    }

    /* 2. Target the Menu Containers (Nuclear Option Preserved) */
    ul[data-baseweb="menu"],
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    div[role="presentation"],
    div[data-baseweb="menu"],
    .stSelectbox ul[data-baseweb="menu"],
    [data-baseweb="select"] ul[data-baseweb="menu"] {
        background-color: var(--c-gold-muted) !important;
        background: var(--c-gold-muted) !important;
        border: 1px solid var(--c-gold-muted) !important;
    }

    /* 3. Target the List Items (Container Level) */
    ul[data-baseweb="menu"] li,
    li[role="option"] {
        background-color: var(--c-gold-muted) !important;
        background: var(--c-gold-muted) !important;
        color: var(--c-teal-deep) !important;
        padding: 10px 15px !important;
        transition: all 0.2s ease;
    }

    /* 4. [NEW] Target the Text Inside the List Item (The Fix) */
    /* This overrides the default Streamlit dark mode text inheritance */
    ul[data-baseweb="menu"] li div,
    li[role="option"] div {
        color: var(--c-teal-deep) !important;
        -webkit-text-fill-color: var(--c-teal-deep) !important;
    }

    /* 5. Hover State */
    ul[data-baseweb="menu"] li:hover,
    li[role="option"]:hover {
        background-color: #c9a867 !important; /* Slightly darker gold */
        background: #c9a867 !important;
    }
    
    /* [NEW] Force text color on hover */
    ul[data-baseweb="menu"] li:hover div,
    li[role="option"]:hover div {
        color: var(--c-teal-deep) !important;
        -webkit-text-fill-color: var(--c-teal-deep) !important;
    }

    /* 6. Selected State */
    ul[data-baseweb="menu"] li[aria-selected="true"],
    li[role="option"][aria-selected="true"] {
        background-color: var(--c-teal-deep) !important;
        background: var(--c-teal-deep) !important;
    }

    /* [NEW] Force text inversion on selection (Gold Text on Teal Background) */
    ul[data-baseweb="menu"] li[aria-selected="true"] div,
    li[role="option"][aria-selected="true"] div {
        color: var(--c-gold-muted) !important;
        -webkit-text-fill-color: var(--c-gold-muted) !important;
    }

    /* 6. BUTTONS (GLOBAL — one style, no variants) */
    .stButton button, .stButton > button, button[kind="primary"], button[kind="secondary"] {
        font-family: 'Montserrat', 'Helvetica Neue', Arial, sans-serif !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        text-transform: uppercase !important;
        letter-spacing: 0.1em !important;
        color: #ab8f59 !important;
        -webkit-text-fill-color: #ab8f59 !important;
        background-color: transparent !important;
        border: 1.5px solid #ab8f59 !important;
        border-radius: 0px !important;
        padding: 12px 32px !important;
        width: 100% !important;
        transition: background-color 0.2s, color 0.2s !important;
    }
    .stButton button:hover, .stButton > button:hover {
        background-color: #ab8f59 !important;
        color: #f5f5f0 !important;
        -webkit-text-fill-color: #f5f5f0 !important;
        border-color: #ab8f59 !important;
    }
    .stButton button:focus, .stButton > button:focus {
        box-shadow: none !important;
        color: #ab8f59 !important;
        -webkit-text-fill-color: #ab8f59 !important;
    }
    .stButton button:active, .stButton > button:active {
        background-color: #a6784d !important;
        color: #f5f5f0 !important;
        -webkit-text-fill-color: #f5f5f0 !important;
        border-color: #a6784d !important;
    }
    /* Button child elements inherit text color */
    .stButton button p, .stButton button span, .stButton button div,
    .stButton > button p, .stButton > button span, .stButton > button div {
        color: inherit !important;
        -webkit-text-fill-color: inherit !important;
    }

    /* 7. DASHBOARD CARDS (Static) */
    .dashboard-card {
        background-color: rgba(27, 42, 46, 0.6);
        border: 1px solid var(--c-sage);
        border-left: 4px solid var(--c-gold-muted);
        padding: 25px;
        margin-bottom: 20px;
    }
    
    /* 8. OVERRIDE ALERTS */
    div.stAlert {
        background-color: rgba(171, 143, 89, 0.1);
        border: 1px solid var(--c-gold-muted);
        color: var(--c-gold-muted);
        border-radius: 0px;
    }
    div.stAlert > div { color: var(--c-cream) !important; }
    
    /* 10. STATUS INDICATORS */
    .status-dot { height: 10px; width: 10px; border-radius: 50%; display: inline-block; margin-right: 8px; }
    .dot-green { background-color: #4cd964; box-shadow: 0 0 10px #4cd964; }
    .dot-red { background-color: #ff5f56; opacity: 0.5; }
    .dot-yellow { background-color: var(--c-gold-muted); box-shadow: 0 0 5px var(--c-gold-muted); }

    .status-row {
        background: rgba(255,255,255,0.03);
        padding: 15px;
        margin-bottom: 10px;
        border-left: 2px solid transparent;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    /* 11. FOOTER */
    .footer {
        position: fixed; left: 0; bottom: 0; width: 100%;
        background-color: var(--c-teal-deep);
        color: var(--c-sage);
        text-align: center;
        padding: 10px;
        font-size: 0.7rem;
        letter-spacing: 0.2em;
        border-top: 1px solid #30363d;
        z-index: 100;
    }

    /* 12. BRANDED HTML TABLES (Activity Log, God Mode, etc.) */
    .activity-log-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Montserrat', 'Helvetica Neue', Arial, sans-serif;
        font-size: 0.85rem;
        user-select: text;
        -webkit-user-select: text;
    }
    .activity-log-table th {
        background-color: #1b2a2e;
        color: #ab8f59;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 12px 14px;
        border-bottom: 2px solid #ab8f59;
        text-align: left;
    }
    .activity-log-table td {
        padding: 10px 14px;
        color: #f5f5f0;
        border-bottom: 1px solid rgba(92, 107, 97, 0.3);
    }
    .activity-log-table tr:hover td {
        background-color: rgba(171, 143, 89, 0.08);
    }

    /* CLEANUP */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}

</style>
""", unsafe_allow_html=True)

# --- GLOBAL TYPOGRAPHY & BUTTON CSS (from brand_ui) ---
brand_ui.inject_typography_css()
brand_ui.inject_button_css()

# --- SESSION STATE & AUTH ---
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'user_id' not in st.session_state: st.session_state['user_id'] = None
if 'username' not in st.session_state: st.session_state['username'] = None
if 'org_id' not in st.session_state: st.session_state['org_id'] = None # NEW: Org Context

# WIZARD STATE DEFAULTS
def init_wizard_state():
    if 'wiz_samples_list' not in st.session_state: st.session_state['wiz_samples_list'] = []
    if 'wiz_social_list' not in st.session_state: st.session_state['wiz_social_list'] = [] 
    if 'wiz_logo_list' not in st.session_state: st.session_state['wiz_logo_list'] = []      
    if 'dashboard_upload_open' not in st.session_state: st.session_state['dashboard_upload_open'] = False 
    if 'palette_primary' not in st.session_state: st.session_state['palette_primary'] = ["#24363b"]
    if 'palette_secondary' not in st.session_state: st.session_state['palette_secondary'] = ["#f5f5f0", "#5c6b61"]
    if 'palette_accent' not in st.session_state: st.session_state['palette_accent'] = ["#ab8f59"]
    # Dynamic Keys
    if 'file_uploader_key' not in st.session_state: st.session_state['file_uploader_key'] = 0 
    if 'social_uploader_key' not in st.session_state: st.session_state['social_uploader_key'] = 1000
    if 'logo_uploader_key' not in st.session_state: st.session_state['logo_uploader_key'] = 2000
    # Message House State
    if 'mh_brand_promise' not in st.session_state: st.session_state['mh_brand_promise'] = ""
    if 'mh_pillars_json' not in st.session_state: st.session_state['mh_pillars_json'] = ""
    if 'mh_founder_positioning' not in st.session_state: st.session_state['mh_founder_positioning'] = ""
    if 'mh_pov' not in st.session_state: st.session_state['mh_pov'] = ""
    if 'mh_boilerplate' not in st.session_state: st.session_state['mh_boilerplate'] = ""
    if 'mh_offlimits' not in st.session_state: st.session_state['mh_offlimits'] = ""
    if 'mh_preapproval_claims' not in st.session_state: st.session_state['mh_preapproval_claims'] = ""
    if 'mh_tone_constraints' not in st.session_state: st.session_state['mh_tone_constraints'] = ""

init_wizard_state()

if 'profiles' not in st.session_state: st.session_state['profiles'] = {}
if 'nav_selection' not in st.session_state: st.session_state['nav_selection'] = "DASHBOARD"
if 'tier' not in st.session_state: st.session_state['tier'] = {}
if 'usage' not in st.session_state: st.session_state['usage'] = {}
if 'subscription_status' not in st.session_state: st.session_state['subscription_status'] = 'inactive'
if '_tier_resolved_at' not in st.session_state: st.session_state['_tier_resolved_at'] = 0

ARCHETYPES = [
    "The Ruler", "The Creator", "The Sage", "The Innocent", 
    "The Outlaw", "The Magician", "The Hero", "The Lover", 
    "The Jester", "The Everyman", "The Caregiver", "The Explorer"
]
# --- ARCHETYPE DEFINITIONS ---
ARCHETYPE_INFO = {
    "The Ruler": {
        "tagline": "Power, Control, & Stability", 
        "desc": "You create order from chaos. You lead with authority and expect excellence.",
        "examples": "Rolex, Mercedes-Benz, Microsoft"
    },
    "The Creator": {
        "tagline": "Innovation, Art, & Imagination",
        "desc": "You realize a vision. You foster innovation and believe in the power of imagination.",
        "examples": "Apple, Adobe, Lego"
    },
    "The Sage": {
        "tagline": "Wisdom, Truth, & Expertise",
        "desc": "You seek the truth. You are an expert source of information and analysis.",
        "examples": "Google, BBC, McKinsey & Co"
    },
    "The Innocent": {
        "tagline": "Optimism, Safety, & Purity",
        "desc": "You just want to be happy. You are honest, pure, and offer a simple solution.",
        "examples": "Dove, Coca-Cola, Nintendo"
    },
    "The Outlaw": {
        "tagline": "Disruption, Liberation, & Revolution",
        "desc": "You break the rules. You disrupt the status quo and shock people out of complacency.",
        "examples": "Harley-Davidson, Virgin, Diesel"
    },
    "The Magician": {
        "tagline": "Transformation, Vision, & Belief",
        "desc": "You make dreams come true. You create transformative experiences.",
        "examples": "Disney, Tesla, Dyson"
    },
    "The Hero": {
        "tagline": "Mastery, Courage, & Growth",
        "desc": "You prove worth through action. You want to improve the world through mastery.",
        "examples": "Nike, BMW, FedEx"
    },
    "The Lover": {
        "tagline": "Intimacy, Passion, & Connection",
        "desc": "You create relationships. You evoke emotion, desire, and sensory pleasure.",
        "examples": "Chanel, Victoria's Secret, Alfa Romeo"
    },
    "The Jester": {
        "tagline": "Joy, Humor, & Lightness",
        "desc": "You live in the moment. You help people have a good time and lighten up.",
        "examples": "Old Spice, M&M's, Ben & Jerry's"
    },
    "The Everyman": {
        "tagline": "Belonging, Connection, & Comfort",
        "desc": "You are one of them. You are down-to-earth, supportive, and accessible.",
        "examples": "IKEA, Target, Levi's"
    },
    "The Caregiver": {
        "tagline": "Service, Nurturing, & Protection",
        "desc": "You protect people from harm. You are compassionate, generous, and supportive.",
        "examples": "Johnson & Johnson, Volvo, UNICEF"
    },
    "The Explorer": {
        "tagline": "Freedom, Discovery, & Adventure",
        "desc": "You seek new experiences. You help people escape the ordinary and find freedom.",
        "examples": "Jeep, The North Face, NASA"
    }
}
# --- HELPER FUNCTIONS ---
def nav_to(page_name):
    st.session_state['nav_selection'] = page_name
    
def activate_profile(profile_name):
    st.session_state['active_profile'] = profile_name
    # CHANGE THIS: From "BRAND ARCHITECT" to "BRAND MANAGER"
    st.session_state['nav_selection'] = "BRAND MANAGER"
    
def calculate_calibration_score(profile_data):
    """
    Calibration Scoring v2.
    Total = 100.
    - Strategy:       10 pts (2.5 per field)
    - Message House:  25 pts (mh_sub_score x 0.25)
    - Visuals:        10 pts (palette 3, visual asset 7)
    - Social:         10 pts (>=3 assets=10, >=1=3)
    - Voice Clusters: 45 pts (9 pts per fortified cluster x 5)
    Hard ceiling: If MH sub-score = 0, cap total at 55.
    """
    score = 0
    mh_sub_score = 0
    mh_filled_fields = 0
    mh_total_fields = 8
    cluster_health = {}

    # CASE A: STRUCTURED DATA
    if isinstance(profile_data, dict) and 'inputs' in profile_data:
        inputs = profile_data['inputs']

        # 1. STRATEGY (10 PTS)
        strat_score = 0
        if inputs.get('wiz_mission'): strat_score += 2.5
        if inputs.get('wiz_values'): strat_score += 2.5
        if inputs.get('wiz_guardrails'): strat_score += 2.5
        if inputs.get('wiz_archetype'): strat_score += 2.5
        score += strat_score

        # 2. MESSAGE HOUSE (25 PTS via internal 0-100 sub-score x 0.25)
        # Brand Promise: 20%
        bp = inputs.get('mh_brand_promise', '').strip()
        if bp:
            mh_sub_score += 20
            mh_filled_fields += 1

        # Pillars: up to 35% (12% per complete pillar, capped at 35)
        pillars_json = inputs.get('mh_pillars_json', '')
        pillar_pts = 0
        has_any_pillar = False
        if pillars_json:
            try:
                pillars = json.loads(pillars_json)
                for p in pillars:
                    name = p.get('name', '').strip()
                    if not name:
                        continue
                    has_any_pillar = True
                    p_completeness = 0.25  # name only
                    if p.get('tagline', '').strip():
                        p_completeness = 0.50
                    if p.get('headline_claim', '').strip():
                        p_completeness = 0.75
                    proof_count = sum(1 for j in range(1, 4) if p.get(f'proof_{j}', '').strip())
                    if proof_count >= 2:
                        p_completeness = 1.0
                    pillar_pts += 12 * p_completeness
                mh_sub_score += min(pillar_pts, 35)
                if has_any_pillar:
                    mh_filled_fields += 1
            except (json.JSONDecodeError, TypeError):
                pass

        # Proof Points: 15% (filled / 9 total x 15)
        if pillars_json:
            try:
                pillars = json.loads(pillars_json)
                total_proofs = sum(
                    1 for p in pillars
                    for j in range(1, 4)
                    if p.get(f'proof_{j}', '').strip()
                )
                mh_sub_score += (total_proofs / 9) * 15
            except (json.JSONDecodeError, TypeError):
                pass

        # Founder Positioning: 10%
        if inputs.get('mh_founder_positioning', '').strip():
            mh_sub_score += 10
            mh_filled_fields += 1

        # POV Statement: 10%
        if inputs.get('mh_pov', '').strip():
            mh_sub_score += 10
            mh_filled_fields += 1

        # Boilerplate: 5%
        if inputs.get('mh_boilerplate', '').strip():
            mh_sub_score += 5
            mh_filled_fields += 1

        # Messaging Guardrails (any of 3 sub-fields): 5%
        has_guardrail = any(
            inputs.get(k, '').strip()
            for k in ['mh_offlimits', 'mh_preapproval_claims', 'mh_tone_constraints']
        )
        if has_guardrail:
            mh_sub_score += 5
            mh_filled_fields += 1

        mh_sub_score = min(mh_sub_score, 100)
        score += mh_sub_score * 0.25

        # 3. VISUALS (10 PTS)
        vis_score = 0
        if inputs.get('palette_primary'): vis_score += 3
        v_blob = inputs.get('visual_dna', '')
        if "[ASSET:" in v_blob: vis_score += 7
        score += vis_score

        # 4. SOCIAL (10 PTS — per-platform scoring)
        soc_score = 0
        s_blob = inputs.get('social_dna', '')
        social_platforms = count_social_by_platform(s_blob)
        platforms_with_samples = sum(1 for c in social_platforms.values() if c >= 1)
        platforms_calibrated = sum(1 for c in social_platforms.values() if c >= 3)
        if platforms_calibrated >= 2: soc_score = 10
        elif platforms_calibrated >= 1: soc_score = 7
        elif platforms_with_samples >= 2: soc_score = 5
        elif platforms_with_samples >= 1: soc_score = 3
        score += soc_score

        # 5. VOICE CLUSTERS (45 PTS — 9 pts per fortified cluster)
        voice_blob = inputs.get('voice_dna', '')
        clusters = {
            "Corporate": "Corporate Affairs",
            "Crisis": "Crisis & Response",
            "Internal": "Internal Leadership",
            "Thought": "Thought Leadership",
            "Marketing": "Brand Marketing"
        }
        voice_score = 0
        for key, full_name in clusters.items():
            count = voice_blob.upper().count(f"CLUSTER: {full_name.upper()}")
            if count >= 3:
                points = 9
                status = "FORTIFIED"
                icon = brand_ui.SHIELD_ALIGNED
            elif count >= 1:
                points = 3
                status = "UNSTABLE"
                icon = brand_ui.SHIELD_DRIFT
            else:
                points = 0
                status = "EMPTY"
                icon = brand_ui.SHIELD_DEGRADATION
            voice_score += points
            cluster_health[key] = {"count": count, "status": status, "icon": icon}
        score += voice_score

    # CASE B: LEGACY/PDF (Fallback)
    else:
        text_data = str(profile_data.get('final_text', '') if isinstance(profile_data, dict) else profile_data)
        score = min(len(text_data) // 50, 100)

    # HARD CEILING: No MH data = cap at 55
    score = min(score, 100)
    if mh_sub_score == 0:
        score = min(score, 55)

    # FINAL STATUS LABEL
    if score < 40:
        status_label = "LOW DATA"
        color = "#ff4b4b"
    elif score < 80:
        status_label = "DEVELOPING"
        color = "#ffa421"
    else:
        status_label = "FORTIFIED"
        color = "#09ab3b"

    return {
        "score": score,
        "status_label": status_label,
        "color": color,
        "clusters": cluster_health,
        "mh_sub_score": mh_sub_score,
        "mh_filled_fields": mh_filled_fields,
        "mh_total_fields": mh_total_fields,
        "mh_ceiling_active": (mh_sub_score == 0),
        "social_platforms": social_platforms if isinstance(profile_data, dict) and 'inputs' in profile_data else {"LinkedIn": 0, "Instagram": 0, "Twitter/X": 0}
    }


# --- DASHBOARD HELPER FUNCTIONS ---

def count_social_by_platform(social_dna: str) -> dict:
    """Parse social_dna blob and return per-platform sample counts."""
    import re
    platforms = {"LinkedIn": 0, "Instagram": 0, "Twitter/X": 0}
    if not social_dna:
        return platforms
    for match in re.finditer(r'\[ASSET:\s*(LINKEDIN|INSTAGRAM|TWITTER|X)\s', social_dna, re.IGNORECASE):
        plat = match.group(1).upper()
        if plat == "LINKEDIN":
            platforms["LinkedIn"] += 1
        elif plat == "INSTAGRAM":
            platforms["Instagram"] += 1
        elif plat in ("TWITTER", "X"):
            platforms["Twitter/X"] += 1
    return platforms


def calculate_strategy_completion(inputs: dict) -> dict:
    """Return strategy field completion status."""
    fields = ['wiz_mission', 'wiz_values', 'wiz_guardrails', 'wiz_archetype']
    filled = sum(1 for f in fields if inputs.get(f))
    return {"filled": filled, "total": 4, "pct": (filled / 4) * 100}


def calculate_visual_completion(inputs: dict) -> dict:
    """Return visual identity completion status."""
    has_palette = bool(inputs.get('palette_primary'))
    has_visual_assets = "[ASSET:" in inputs.get('visual_dna', '')
    filled = int(has_palette) + int(has_visual_assets)
    return {"has_palette": has_palette, "has_visual_assets": has_visual_assets, "pct": (filled / 2) * 100}


def map_calibration_status(internal_label: str) -> str:
    """Map internal status labels to user-facing terminology."""
    mapping = {
        "FORTIFIED": "Calibrated",
        "UNSTABLE": "Partially Calibrated",
        "EMPTY": "Not Calibrated",
        "LOW DATA": "Not Calibrated",
        "DEVELOPING": "Partially Calibrated",
    }
    return mapping.get(internal_label, internal_label)


def format_activity_time(timestamp_str: str, created_at) -> str:
    """Format activity log timestamp for dashboard display."""
    from datetime import datetime as dt, date, timedelta
    try:
        if isinstance(created_at, str) and len(created_at) >= 10:
            event_date = dt.strptime(created_at[:10], "%Y-%m-%d").date()
        else:
            return timestamp_str or ""
        today = date.today()
        if event_date == today:
            return f"Today {timestamp_str}"
        elif event_date == today - timedelta(days=1):
            return f"Yesterday {timestamp_str}"
        else:
            return f"{event_date.strftime('%b %d')} {timestamp_str}"
    except (ValueError, TypeError):
        return timestamp_str or ""


# build_mh_context is imported from prompt_builder.py

# --- SHARED: Content Type Selector with Cluster Visibility & Override ---
def render_content_type_selector(module_name: str, key_prefix: str):
    """Shared content type selector with ordered dropdown, cluster display, and override.

    Args:
        module_name: 'generator' or 'editor'
        key_prefix: prefix for session state keys ('cg' or 'ce')

    Returns:
        (type_key, active_cluster, custom_desc, display_label)
        - type_key: content type key (e.g. 'press_release')
        - active_cluster: resolved cluster (respects override)
        - custom_desc: user description if custom type, else ''
        - display_label: clean label for prompts (e.g. 'Press Release')
    """
    # Ordered dropdown with cluster context
    _options = get_ordered_display_options(module_name)
    selected_display = st.selectbox(
        "FORMAT" if module_name == "generator" else "CONTENT TYPE",
        _options,
        key=f"{key_prefix}_type_display"
    )

    type_key = get_key_from_display(selected_display)
    config = CONTENT_TYPES.get(type_key, CONTENT_TYPES["custom"])
    default_cluster = config["cluster"]
    display_label = config["label"]

    custom_desc = ""

    if type_key != "custom":
        # Show cluster assignment + override option
        cluster_name = CLUSTER_DISPLAY_NAMES.get(default_cluster, "Unknown")
        _ov_c1, _ov_c2 = st.columns([3, 1])
        with _ov_c1:
            st.caption(f"VOICE CLUSTER: {cluster_name.upper()}")
        with _ov_c2:
            override = st.checkbox("Override", key=f"{key_prefix}_cluster_override")

        if override:
            cluster_options = list(CLUSTER_DISPLAY_NAMES.values())
            selected_cluster_label = st.selectbox(
                "SELECT VOICE CLUSTER",
                cluster_options,
                index=cluster_options.index(cluster_name),
                key=f"{key_prefix}_cluster_override_select"
            )
            active_cluster = selected_cluster_label
        else:
            active_cluster = default_cluster
    else:
        # Custom type: always show description + cluster selector
        custom_desc = st.text_input(
            "DESCRIBE THE CONTENT TYPE",
            placeholder="e.g. board update, conference abstract, investor FAQ",
            max_chars=200,
            key=f"{key_prefix}_custom_desc"
        )
        cluster_options = list(CLUSTER_DISPLAY_NAMES.values())
        selected_cluster_label = st.selectbox(
            "WHICH VOICE CLUSTER BEST FITS THIS CONTENT?",
            cluster_options,
            index=3,  # Default: Thought Leadership
            key=f"{key_prefix}_custom_cluster"
        )
        active_cluster = selected_cluster_label

    return type_key, active_cluster, custom_desc, display_label


# --- HELPER: ASSET-AWARE CONFIDENCE ENGINE ---
def calculate_content_confidence(profile_data, content_type):
    """
    Calculates confidence based on 'Risk vs. Assets'.
    Returns: Score (0-100), Label, Color, Action, and a 'Evidence-Based' Rationale.
    """
    score = 0
    # The Yin (What we have) and Yang (What we lack)
    assets_found = []
    missing_risks = []
    
    # Extract Ingredients
    inputs = profile_data.get('inputs', {})
    # Lowercase text scan for keywords
    final_text = str(profile_data.get('final_text', '')).lower()
    
    # Resolve cluster for content type
    _cc_cluster = get_cluster_for_label(content_type)

    # --- TIER 1: HIGH RISK (Crisis & Response, Corporate Affairs) ---
    # Strategy: Start at 0. Trust must be earned. Safety is paramount.
    if _cc_cluster in ["Crisis & Response", "Corporate Affairs"]:
        # 1. GUARDRAILS (The Safety Net) - Critical
        if inputs.get('wiz_guardrails'):
            score += 40
            assets_found.append("Safety Guardrails")
        else:
            missing_risks.append("Guardrails (Risk of wrong tone)")

        # 2. VALUES (The Moral Compass) - Critical
        if inputs.get('wiz_values'):
            score += 30
            assets_found.append("Core Values")
        else:
            missing_risks.append("Values (Lack of empathy anchor)")

        # 3. MISSION (The Identity)
        if inputs.get('wiz_mission'):
            score += 20
            assets_found.append("Mission Boilerplate")
        else:
            missing_risks.append("Mission Statement")

        # 4. HISTORY (The Precedent)
        if _cc_cluster == "Crisis & Response" and ("crisis" in final_text or "statement" in final_text):
            score += 10
            assets_found.append("Crisis History")
        elif _cc_cluster == "Corporate Affairs" and ("press" in final_text or "release" in final_text):
            score += 10
            assets_found.append("Press History")

        # HARD CAP: If Guardrails are missing, cannot exceed 50%.
        if not inputs.get('wiz_guardrails'):
            score = min(score, 50)

    # --- TIER 2: STRATEGIC INTERNAL (Internal Leadership) ---
    # Strategy: Start at 20. Needs Authority and Tone.
    elif _cc_cluster == "Internal Leadership":
        score = 20 # Base trust
        
        # 1. TONE (The Voice) - Critical
        if inputs.get('wiz_tone'): 
            score += 30
            assets_found.append("Tone Definitions")
        else:
            missing_risks.append("Tone Keywords")
            
        # 2. WRITING SAMPLES (The Proof)
        if "analysis:" in final_text or len(final_text) > 1000:
            score += 30
            assets_found.append("Analyzed Voice Samples")
        else:
            missing_risks.append("Writing Samples")
            
        # 3. MISSION (Alignment)
        if inputs.get('wiz_mission'): 
            score += 20
            assets_found.append("Strategic Alignment")
            
        # HARD CAP: If Tone is missing, max 60.
        if not inputs.get('wiz_tone'):
            score = min(score, 60)

    # --- TIER 3: CREATIVE & EXTERNAL (Blog, Speech, Social) ---
    # Strategy: Start at 30. Needs Style and Rhythm.
    else:
        score = 30 # Base trust
        
        # 1. DEEP CONTEXT (The Rhythm)
        if len(final_text) > 1500:
            score += 40
            assets_found.append("Deep Voice Data")
        elif len(final_text) > 500:
            score += 20
            assets_found.append("Basic Context")
        else:
            missing_risks.append("Sufficient Text Data")
            
        # 2. TONE (The Vibe)
        if inputs.get('wiz_tone'): 
            score += 30
            assets_found.append("Tone Guidelines")
        else:
            missing_risks.append("Tone Definitions")
            
        # HARD CAP: If context is shallow, max 50.
        if len(final_text) < 500:
            score = min(score, 50)

    # --- FINAL CALCULATIONS & OUTPUT ---
    score = min(100, score)
    
    # Construct Evidence-Based Rationale
    if assets_found:
        found_str = f"Using: {', '.join(assets_found)}."
    else:
        found_str = "No specific assets found."
        
    if missing_risks:
        missing_str = f"Missing: {', '.join(missing_risks)}."
    else:
        missing_str = ""

    rationale = f"{found_str} {missing_str}"

    # Visual Output
    if score >= 80:
        return {"score": score, "label": "HIGH PRECISION", "color": "#09ab3b", "action": None, "rationale": rationale}
    elif score >= 50:
        return {"score": score, "label": "CAPABLE", "color": "#ffa421", "action": f"Add {missing_risks[0]}" if missing_risks else "Add Context", "rationale": rationale}
    else:
        return {"score": score, "label": "LOW DATA", "color": "#ff4b4b", "action": f"Needs {missing_risks[0]}" if missing_risks else "Build Profile", "rationale": rationale}

# --- HELPER: SOCIAL CALIBRATION ---
def calculate_social_confidence(profile_data, platform):
    """
    Checks if the profile contains specific examples for the target platform.
    """
    score = 0
    missing = []
    
    # We scan the 'final_text' because that's where the analyzed social samples live
    # format from Architect is: "Platform: LinkedIn. Analysis: ..."
    final_text = profile_data.get('final_text', '')
    
    # 1. PLATFORM SPECIFICITY (50 pts)
    # Does the profile actually contain analyzed posts for this platform?
    if f"Platform: {platform}" in final_text:
        score += 50
    else:
        missing.append(f"{platform} Examples")
        
    # 2. BRAND VOICE FOUNDATION (30 pts)
    inputs = profile_data.get('inputs', {})
    if inputs.get('wiz_tone'): score += 15
    if inputs.get('wiz_values'): score += 15
    
    # 3. VISUALS (20 pts) - Important for Insta/LinkedIn
    if inputs.get('palette_primary'): score += 20
    
    # Formatting
    if score >= 80:
        return {"score": score, "label": "DIALECT MATCHED", "color": "#09ab3b", "action": None}
    elif score >= 50:
        return {"score": score, "label": "GENERIC VOICE", "color": "#ffa421", "action": f"Add {missing[0]}"}
    else:
        return {"score": score, "label": "UNINITIATED", "color": "#ff4b4b", "action": "Upload Social Screenshots"}

def convert_to_html_brand_card(brand_name, content):
    content = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    content = re.sub(r'^#+\s*(.*)', r'<h3 style="color: #ab8f59; border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-top: 20px;">\1</h3>', content, flags=re.MULTILINE)
    content = re.sub(r'^\*\s*(.*)', r'<div style="margin-left: 20px; margin-bottom: 5px;">• \1</div>', content, flags=re.MULTILINE)
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Montserrat', 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f0; color: #24363b; padding: 40px; line-height: 1.6; }}
            .brand-card {{ max-width: 800px; margin: 0 auto; background: white; padding: 60px; border-top: 10px solid #24363b; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
            h1 {{ font-size: 3em; color: #24363b; text-transform: uppercase; margin-bottom: 10px; letter-spacing: 0.05em; }}
            .subtitle {{ font-size: 1.2em; color: #ab8f59; font-weight: bold; letter-spacing: 0.2em; text-transform: uppercase; margin-bottom: 40px; }}
            strong {{ color: #1b2a2e; font-weight: 700; }}
            .footer {{ margin-top: 60px; font-size: 0.7rem; color: #aaa; text-align: center; border-top: 1px solid #eee; padding-top: 20px; letter-spacing: 0.1em; }}
            .content {{ white-space: pre-wrap; font-family: inherit; }}
        </style>
    </head>
    <body>
        <div class="brand-card">
            <h1>{brand_name}</h1>
            <div class="subtitle">Brand Fidelity Profile</div>
            <div class="content">{content}</div>
            <div class="footer">GENERATED BY SIGNET // INTELLIGENT BRAND FIDELITY</div>
        </div>
    </body>
    </html>
    """
    return html_template

# --- CALLBACKS ---
def add_voice_sample_callback():
    s_type = st.session_state.get('wiz_sample_type', 'Generic')
    s_text = st.session_state.get('wiz_temp_text', '')
    u_key = f"uploader_{st.session_state['file_uploader_key']}"
    s_file = st.session_state.get(u_key, None)
    content = ""
    source = ""
    if s_text.strip():
        content = s_text
        source = "Text Paste"
    elif s_file:
        source = f"File ({s_file.name})"
        try:
            if s_file.type == "application/pdf":
                content = logic.extract_text_from_pdf(s_file)
            elif "image" in s_file.type:
                content = f"[IMAGE CONTENT: {s_file.name}]" 
            else:
                content = s_file.getvalue().decode("utf-8", errors='ignore')
        except Exception as e:
            content = f"[Extraction Failed: {str(e)}]"
    if content:
        entry = f"TYPE: {s_type} | SOURCE: {source}\nCONTENT: {content}"
        st.session_state['wiz_samples_list'].append(entry)
        st.session_state['wiz_temp_text'] = ""
        st.session_state['file_uploader_key'] += 1

def add_social_callback():
    s_platform = st.session_state.get('wiz_social_platform', 'Other')
    u_key = f"social_up_{st.session_state['social_uploader_key']}"
    s_file = st.session_state.get(u_key, None)
    if s_file:
        st.session_state['wiz_social_list'].append({'platform': s_platform, 'file': s_file})
        st.session_state['social_uploader_key'] += 1

def add_logo_callback():
    u_key = f"logo_up_{st.session_state['logo_uploader_key']}"
    s_file = st.session_state.get(u_key, None)
    if s_file:
        st.session_state['wiz_logo_list'].append({'file': s_file})
        st.session_state['logo_uploader_key'] += 1

def add_palette_color(key):
    st.session_state[key].append("#ffffff")

def remove_palette_color(key, index):
    st.session_state[key].pop(index)

# --- PASSWORD RESET TOKEN HANDLING ---
_reset_token = st.query_params.get("reset_token")
_checkout_success = st.query_params.get("checkout") == "success"

# --- LOGIN / AUTH SCREEN (HERO LAYOUT V3 - FIXED) ---
if not st.session_state['authenticated']:

    # Handle password reset token flow
    if _reset_token:
        _reset_username = db.validate_reset_token(_reset_token)
        st.markdown("""<style>
            .stApp { background-color: #f5f5f0 !important; }
            section[data-testid="stSidebar"] { display: none; }
            [data-testid="stAppViewContainer"], [data-testid="stMain"],
            [data-testid="stMainBlockContainer"], [data-testid="stHeader"],
            [data-testid="stBottom"] { background-color: transparent !important; background: transparent !important; }
            .stTextInput input { background-color: #ffffff !important; color: #24363b !important;
                border: 1px solid #c0c0c0 !important; -webkit-text-fill-color: #24363b !important; }
        </style>""", unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)
        _rc1, _rc2, _rc3 = st.columns([1, 1.2, 1])
        with _rc2:
            st.markdown("<h4 style='text-align:center; color:#ab8f59; letter-spacing:2px; margin-bottom:20px;'>RESET PASSWORD</h4>", unsafe_allow_html=True)
            if not _reset_username:
                st.error("This reset link is invalid or has expired. Please request a new one.")
                if st.button("Back to Login"):
                    st.query_params.clear()
                    st.rerun()
            else:
                with st.form("reset_password_form"):
                    rp_new = st.text_input("New Password", type="password", key="rp_new")
                    rp_confirm = st.text_input("Confirm Password", type="password", key="rp_confirm")
                    if st.form_submit_button("Set New Password"):
                        if not rp_new or len(rp_new) < 8:
                            st.error("Password must be at least 8 characters.")
                        elif rp_new != rp_confirm:
                            st.error("Passwords do not match.")
                        else:
                            db.reset_user_password(_reset_username, rp_new)
                            db.consume_reset_token(_reset_token)
                            st.success("Password updated. You can now log in.")
                            st.query_params.clear()
                            import time as _rst; _rst.sleep(2)
                            st.rerun()
        st.stop()

    # 1. GLOBAL STYLES + LOGIN CARD CSS
    st.markdown("""<style>
        .stApp {
            background-color: #f5f5f0 !important;
            background-image: linear-gradient(rgba(36, 54, 59, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(36, 54, 59, 0.05) 1px, transparent 1px), radial-gradient(circle at 0% 0%, rgba(92, 107, 97, 0.5) 0%, rgba(92, 107, 97, 0.1) 40%, transparent 70%), radial-gradient(circle at 100% 100%, rgba(36, 54, 59, 0.4) 0%, rgba(36, 54, 59, 0.1) 40%, transparent 70%);
            background-size: 40px 40px, 40px 40px, 100% 100%, 100% 100%;
        }
        section[data-testid="stSidebar"] { display: none; }
        /* Force internal containers transparent so .stApp cream+grid shows through */
        [data-testid="stAppViewContainer"],
        [data-testid="stMain"],
        [data-testid="stMainBlockContainer"],
        [data-testid="stHeader"],
        [data-testid="stBottom"] {
            background-color: transparent !important;
            background: transparent !important;
        }
        .stTextInput input { 
            background-color: #ffffff !important; 
            color: #24363b !important; 
            border: 1px solid #c0c0c0 !important; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
            -webkit-text-fill-color: #24363b !important; 
        } 
        .stTextInput input:focus { border-color: #24363b !important; }
        .stTextInput label, .stTextArea label {
            color: #ab8f59 !important;
            -webkit-text-fill-color: #ab8f59 !important;
        }
        
        /* FIX: TARGET THE RIGHT COLUMN TO CREATE THE CARD LOOK WITHOUT HTML WRAPPERS */
        div[data-testid="column"]:nth-of-type(2) > div[data-testid="stVerticalBlock"] {
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
            border-top: 5px solid #24363b;
        }

        /* --- TYPOGRAPHY & LAYOUT --- */
        .login-content-left h1 {
            font-family: 'Montserrat', sans-serif !important;
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: 0.12em;
            color: #24363b;
            margin-bottom: 28px;
            line-height: 1.2;
        }

        .login-content-left p,
        .login-content-left a,
        .login-content-left span {
            font-family: 'Montserrat', sans-serif !important;
        }

        .login-value {
            font-family: 'Montserrat', sans-serif !important;
            font-size: 1.1rem;
            line-height: 1.7;
            color: #24363b;
            margin: 28px 0;
            max-width: 600px;
        }

        .login-workflow {
            font-family: 'Montserrat', sans-serif !important;
            font-size: 1rem;
            line-height: 1.7;
            color: #24363b;
            margin-bottom: 32px;
            max-width: 600px;
        }

        .login-credibility {
            font-family: 'Montserrat', sans-serif !important;
            font-size: 0.85rem;
            color: #24363b;
            line-height: 1.5;
            margin-top: 24px;
        }

        .login-credibility a {
            color: #24363b;
            text-decoration: none;
            font-weight: 600;
        }

        /* --- RESPONSIVE --- */
        @media (max-width: 768px) {
            .login-content-left h1 { font-size: 1.2rem; }
            .login-value { font-size: 1rem; }
        }
    </style>""", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # 2. BALANCED COLUMNS
    c1, c2 = st.columns([1, 1], gap="large")
    
    # --- LEFT COLUMN: THE PITCH ---
    with c1:
        if os.path.exists("Signet_Logo_Color.png"):
            st.image("Signet_Logo_Color.png", width=180)
        else:
            st.markdown("<div style='font-size: 3rem; color: #24363b; font-weight: 800; letter-spacing: 0.15em; margin-bottom: 20px;'>SIGNET</div>", unsafe_allow_html=True)
            
        # FIX: HTML is flush-left to prevent "Black Box" code block rendering
        st.markdown("""
<div class="login-content-left">
<h1>Brand Fidelity Engine</h1>
<p class="login-value">Whether you manage one brand or ten, every piece of content should sound exactly like the brand it represents. Signet makes sure it does.</p>
<p class="login-workflow">Define your brand profile. Audit your drafts against it. Generate new content that stays aligned. The engine calibrates to your positioning&nbsp;&mdash; and gets more precise the more you put in.</p>
<p class="login-credibility">Built by <a href="https://castellanpr.com" target="_blank">Castellan PR</a>. For agencies, in-house teams, and independent practitioners.</p>
</div>
""", unsafe_allow_html=True)
# --- RIGHT COLUMN: THE LOGIN ---
    with c2:
        st.markdown("<h4 style='text-align: center; color: #ab8f59; margin-bottom: 20px; letter-spacing: 2px;'>ACCESS TERMINAL</h4>", unsafe_allow_html=True)
        
        # --- NEW: SELF-SEALING ADMIN SETUP ---
        if db.get_user_count() == 0:
            st.warning("SYSTEM RESET: CREATE ADMIN ACCOUNT")
            with st.form("setup_admin_hero"):
                new_admin_user = st.text_input("Admin Username", max_chars=64)
                new_admin_pass = st.text_input("Admin Password", type="password", max_chars=64)
                new_admin_email = st.text_input("Admin Email", max_chars=120)
                new_admin_org = st.text_input("Admin Org / Agency Name", max_chars=100)
                if st.form_submit_button("Initialize System"):
                    if new_admin_user and new_admin_pass:
                        db.create_user(new_admin_user, new_admin_email, new_admin_pass, org_id=new_admin_org, is_admin=True)
                        st.success("Admin Created! Please Log In.")
                        st.rerun()
            st.divider()
        # -------------------------------------

        login_tab, reg_tab = st.tabs(["LOGIN", "REGISTER"])
        
        with login_tab:
            l_user = st.text_input("USERNAME", key="l_user", max_chars=64)
            l_pass = st.text_input("PASSWORD", type="password", key="l_pass", max_chars=64)
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("ENTER", type="primary", width="stretch"):
                # 1. CHECK CREDENTIALS
                user_data = db.check_login(l_user, l_pass) 
                
                if user_data:
                    # 2. SET SESSION STATE
                    st.session_state['authenticated'] = True
                    st.session_state['user_id'] = user_data['username']
                    st.session_state['username'] = user_data['username']
                    # --- NEW: ORG CONTEXT ---
                    st.session_state['org_id'] = user_data.get('org_id', user_data['username']) # Default to self if no org
                    st.session_state['is_admin'] = user_data['is_admin']

                    # 3. RESOLVE TIER & SYNC SUBSCRIPTION
                    import time as _time
                    user_email = user_data.get('email', '')
                    tier_config = sub_manager.resolve_user_tier(user_data['username'])
                    st.session_state['tier'] = tier_config
                    st.session_state['subscription_status'] = tier_config.get('_subscription_status', 'inactive')
                    st.session_state['status'] = st.session_state['subscription_status']  # backward compat
                    st.session_state['_tier_resolved_at'] = _time.time()
                    st.session_state['usage'] = sub_manager.check_usage_limit(user_data['username'])
                    db.update_last_login(user_data['username'])

                    # 3b. CHECK SUSPENSION STATUS
                    _is_susp, _susp_reason = db.is_user_suspended(user_data['username'])
                    st.session_state['is_suspended'] = _is_susp
                    st.session_state['suspend_reason'] = _susp_reason

                    # 4. LOAD PROFILES & RERUN
                    st.session_state['profiles'] = db.get_profiles(user_data['username'])

                    # 5. ANALYTICS: Session start + onboarding milestone
                    _sid = str(uuid.uuid4())
                    st.session_state['_analytics_session_id'] = _sid
                    _org = user_data.get('org_id') or user_data['username']
                    _brand_count = db.count_user_brands(_org, exclude_sample=True)
                    db.track_event("session_start", user_data['username'],
                                   metadata={"tier": tier_config.get('_tier_key', 'solo'),
                                             "brand_count": _brand_count, "source": "direct"},
                                   session_id=_sid, org_id=_org)

                    st.rerun()
                else:
                    st.error("Invalid Credentials")

            # --- Account Recovery Links ---
            st.markdown("<br>", unsafe_allow_html=True)
            rc1, rc2 = st.columns(2)
            with rc1:
                if st.button("Forgot Username?", key="forgot_username_btn"):
                    st.session_state['_show_forgot_username'] = True
            with rc2:
                if st.button("Forgot Password?", key="forgot_password_btn"):
                    st.session_state['_show_forgot_password'] = True

            if st.session_state.get('_show_forgot_username'):
                with st.form("forgot_username_form"):
                    fu_email = st.text_input("Enter your email address", key="fu_email")
                    if st.form_submit_button("Send Username Reminder"):
                        # Anti-enumeration: always show the same message
                        found = db.get_user_by_email(fu_email)
                        if found and fu_email:
                            email_helper.send_username_reminder(fu_email, found)
                        st.success("If an account exists with that email, we've sent a reminder.")
                        st.session_state['_show_forgot_username'] = False

            if st.session_state.get('_show_forgot_password'):
                with st.form("forgot_password_form"):
                    fp_email = st.text_input("Enter your email address", key="fp_email")
                    if st.form_submit_button("Send Reset Link"):
                        # Anti-enumeration: always show the same message
                        fp_username = db.get_user_by_email(fp_email)
                        if fp_username and fp_email:
                            _token = db.create_reset_token(fp_username)
                            # Look up actual email from user record for safety
                            _fp_user = db.get_user_full(fp_username)
                            _fp_addr = _fp_user.get('email', fp_email) if _fp_user else fp_email
                            email_helper.send_password_reset(_fp_addr, _token)
                        st.success("If an account exists with that email, we've sent a reset link.")
                        st.session_state['_show_forgot_password'] = False

        with reg_tab:
            r_user = st.text_input("CHOOSE USERNAME", key="r_user", max_chars=64)
            r_pass = st.text_input("CHOOSE PASSWORD", type="password", key="r_pass", max_chars=64)
            r_email = st.text_input("EMAIL", key="r_email", max_chars=120) 
            # --- REAL MVP: ORG CREATION ---
            r_org = st.text_input("ORGANIZATION / AGENCY NAME", key="r_org", max_chars=100)
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("CREATE ACCOUNT", width="stretch"):
                # Create user as Admin of their new Org
                if db.create_user(r_user, r_email, r_pass, org_id=r_org, is_admin=True):
                    # Start 14-day trial
                    db.set_trial_start(r_user)
                    # Auto-load Meridian Labs sample brand
                    db.load_sample_brand(r_user)
                    # Analytics: registration + onboarding milestone
                    db.track_event("user_registered", r_user,
                                   metadata={"source": "direct", "trial": True}, org_id=r_org)
                    db.check_milestone(r_user, "account_created", org_id=r_org)
                    # Welcome email (silent failure — never blocks registration)
                    if r_email:
                        email_helper.send_welcome_email(r_email, r_user)
                    st.success(f"Account created! Your 14-day trial is active. Please log in.")
                else:
                    st.error("Username already taken.")

    st.markdown("<br><div style='text-align: center; color: #5c6b61; font-size: 0.7rem; letter-spacing: 0.1em;'>castellanpr.com</div>", unsafe_allow_html=True)
    st.stop()
    
# --- SIDEBAR ---
with st.sidebar:
    # 0. STYLE INJECTION
    st.markdown("""
        <style>
        /* 1. Sidebar Nav Buttons */
        div[data-testid="stButton"] button {
            border-color: #ab8f59 !important;
            color: #ab8f59 !important;
            border-width: 1px !important;
            background-color: transparent !important;
        }
        div[data-testid="stButton"] button:hover {
            border-color: #ab8f59 !important;
            color: #1b2a2e !important;
            background-color: #ab8f59 !important;
        }
        div[data-testid="stButton"] button:active {
            background-color: #ab8f59 !important;
            color: #1b2a2e !important;
        }
        
        /* 2. Primary Action Buttons */
        button[kind="primary"] {
            background-color: #ab8f59 !important;
            color: #1b2a2e !important;
            -webkit-text-fill-color: #1b2a2e !important;
            border: none !important;
            font-weight: 800 !important;
        }
        button[kind="primary"] p {
            color: #1b2a2e !important;
            -webkit-text-fill-color: #1b2a2e !important;
        }
        button[kind="primary"]:hover {
            background-color: #f0c05a !important;
            color: #1b2a2e !important;
            -webkit-text-fill-color: #1b2a2e !important;
        }
        
        /* 3. Navigation Header */
        .nav-header {
            font-size: 0.8rem;
            font-weight: 700;
            color: #5c6b61;
            letter-spacing: 1px;
            margin-top: 10px !important;
            margin-bottom: 5px;
        }

        /* 4. Expander Styling - CRITICAL FIX FOR LEGIBILITY */
        /* Forces the expander to be opaque Cream so text is readable */
        div[data-testid="stExpander"] {
            background-color: #f5f5f0 !important;
            border: 1px solid #ab8f59 !important;
            border-radius: 4px;
            color: #24363b !important;
        }
        div[data-testid="stExpander"] details {
            background-color: #f5f5f0 !important;
        }
        div[data-testid="stExpander"] summary {
            color: #24363b !important;
            font-weight: 700 !important;
        }
        div[data-testid="stExpander"] div[role="group"] {
            color: #24363b !important;
        }
        /* Target the specific p tags inside if needed */
        div[data-testid="stExpander"] p, div[data-testid="stExpander"] span {
            color: #24363b !important;
        }
        div[data-testid="stExpander"] code {
            color: #24363b !important;
            background-color: rgba(0,0,0,0.06);
            padding: 1px 4px;
            border-radius: 3px;
            font-size: 0.82rem;
        }
        </style>
    """, unsafe_allow_html=True)

    # 1. BRANDING
    if os.path.exists("Signet_Logo_Color.png"):
        st.image("Signet_Logo_Color.png", use_container_width=True) 
    else:
        st.markdown('<div style="font-size: 2rem; color: #24363b; font-weight: 900; letter-spacing: 0.1em; text-align: center; margin-bottom: 20px;">SIGNET</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True)

    # 2. USER & STATUS BADGE
    raw_user = (st.session_state.get('username') or 'User').upper()
    import html
    user_tag = html.escape(raw_user) 
    
    # GOD MODE: Auto-Grant Agency Tier to Admin
    if raw_user == "NICK_ADMIN":
        st.session_state['status'] = "ACTIVE"
        
    status_tag = st.session_state.get('status', 'trial').upper()
    
    st.caption(f"OPERATIVE: {user_tag}")
    
    if status_tag == "ACTIVE":
        st.markdown("""
            <div style='background-color: #ab8f59; border: 1px solid #1b2a2e; padding: 6px 12px; border-radius: 4px; display: inline-block; margin-bottom: 10px;'>
                <span style='color: #1b2a2e !important; font-size: 0.75rem; font-weight: 800; letter-spacing: 1px; -webkit-text-fill-color: #1b2a2e;'>AGENCY TIER</span>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style='background-color: #3d3d3d; border: 1px solid #5c6b61; padding: 6px 12px; border-radius: 4px; display: inline-block; margin-bottom: 10px;'>
                <span style='color: #f5f5f0 !important; font-size: 0.75rem; font-weight: 800; letter-spacing: 1px; -webkit-text-fill-color: #f5f5f0;'>TRIAL LICENSE</span>
            </div>
            """, unsafe_allow_html=True)
    
    # 3. ACTIVE PROFILE & CONFIDENCE METER
    profile_names = list(st.session_state.get('profiles', {}).keys())
    selector_options = ["Create New..."] + profile_names
    
    default_ix = 0
    current = st.session_state.get('active_profile_name')
    if current in selector_options:
        default_ix = selector_options.index(current)

    active_profile_selection = st.selectbox("ACTIVE PROFILE", selector_options, index=default_ix)
    
    if active_profile_selection == "Create New...":
        pass 
    elif active_profile_selection != st.session_state.get('active_profile_name'):
        st.session_state['active_profile_name'] = active_profile_selection
        st.rerun()
    
    if active_profile_selection != "Create New..." and active_profile_selection in st.session_state['profiles']:
        current_profile = st.session_state['profiles'][active_profile_selection]
        
        # --- DYNAMIC SCORE CALCULATION ---
        cal_data = calculate_calibration_score(current_profile)
        score = cal_data['score']
        
        st.markdown(f"""
            <style>
                .sb-container {{ margin-bottom: 0px; margin-top: 10px; }}
                .sb-track {{ width: 100%; height: 6px; background: #dcdcd9; border-radius: 999px; overflow: hidden; margin-bottom: 6px; }}
                .sb-fill {{ height: 100%; width: {score}%; background: {cal_data['color']}; border-radius: 999px; transition: width 0.5s ease; }}
                .sb-status {{ font-size: 0.7rem; font-weight: 800; color: {cal_data['color']}; display: flex; justify-content: space-between; }}
            </style>
            <div class="sb-container">
                <span style="font-size: 0.7rem; font-weight: 700; color: #5c6b61;">ENGINE CONFIDENCE</span>
                <div class="sb-track"><div class="sb-fill"></div></div>
                <div class="sb-status">
                    <span>{cal_data['status_label']}</span>
                    <span>{score}%</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # --- DIAGNOSTICS & CAPABILITIES TOOLTIP ---
        if 'clusters' in cal_data and cal_data['clusters']:
            with st.expander("ENGINE DIAGNOSTICS"):
                # 1. Cluster Health Table
                for name, data in cal_data['clusters'].items():
                    # Explicit dark text color for legibility
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:4px; color:#24363b; font-weight:600;">
                        <span>{data['icon']} {name}</span>
                        <span>{data['count']}/3</span>
                    </div>
                    """, unsafe_allow_html=True)

                # MESSAGE HOUSE ROW
                mh_sub = cal_data.get('mh_sub_score', 0)
                mh_filled = cal_data.get('mh_filled_fields', 0)
                mh_total = cal_data.get('mh_total_fields', 8)
                mh_icon = brand_ui.SHIELD_ALIGNED if mh_sub >= 80 else (brand_ui.SHIELD_DRIFT if mh_sub > 0 else brand_ui.SHIELD_DEGRADATION)
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; font-size:0.8rem; margin-bottom:4px; color:#24363b; font-weight:600;">
                    <span>{mh_icon} Message House</span>
                    <span>{mh_filled}/{mh_total}</span>
                </div>
                """, unsafe_allow_html=True)

                st.markdown("---")

                # 2. System Capabilities (Instructional)
                st.markdown("<span style='color:#24363b; font-weight:800; font-size:0.75rem;'>SYSTEM CAPABILITIES:</span>", unsafe_allow_html=True)
                if score < 40:
                    st.markdown(brand_ui.render_severity("degradation", "INSUFFICIENT: Engine relies on generic calibration. High risk of generic output."), unsafe_allow_html=True)
                elif score < 90:
                    st.markdown(brand_ui.render_severity("drift", "PARTIAL: Safe for fortified clusters only. Verify output carefully."), unsafe_allow_html=True)
                else:
                    st.markdown(brand_ui.render_severity("aligned", "OPERATIONAL: Engine is fully fortified across all domains."), unsafe_allow_html=True)

                st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

                # 3. Next Step (Actionable)
                st.markdown("<span style='color:#24363b; font-weight:800; font-size:0.75rem;'>NEXT OBJECTIVE:</span>", unsafe_allow_html=True)
                if cal_data.get('mh_ceiling_active'):
                    st.markdown(
                        "<span style='color:#ff4b4b; font-size:0.75rem; font-weight:700;'>"
                        "ENGINE CAPPED at 55%: Configure the Message House in Brand Architect to enable full scoring."
                        "</span>",
                        unsafe_allow_html=True
                    )
                elif cal_data.get('mh_sub_score', 0) < 50 and cal_data.get('mh_sub_score', 0) > 0:
                    st.markdown(
                        "<span style='color:#ffa421; font-size:0.75rem;'>"
                        "Message House partially complete. Finish pillars and proof points to strengthen scoring."
                        "</span>",
                        unsafe_allow_html=True
                    )
                else:
                    # Find the first weak cluster
                    weakest = next((k for k, v in cal_data['clusters'].items() if v['count'] < 3), None)
                    if weakest:
                        needed = 3 - cal_data['clusters'][weakest]['count']
                        st.markdown(f"<span style='color:#24363b; font-size:0.75rem;'>Upload {needed} more **{weakest}** samples to fortify this cluster.</span>", unsafe_allow_html=True)
                    else:
                        st.markdown("<span style='color:#24363b; font-size:0.75rem;'>System fully calibrated.</span>", unsafe_allow_html=True)

    # TRIAL BANNER
    _sb_is_trial = st.session_state.get('tier', {}).get('_is_trial')
    if _sb_is_trial:
        _sb_trial_days = st.session_state.get('tier', {}).get('_trial_days_remaining', 0)
        st.markdown(f"""
            <div style="background:rgba(171,143,89,0.12); border:1px solid #ab8f59; padding:10px 12px;
                        border-radius:4px; margin-bottom:12px; text-align:center;">
                <div style="font-weight:700; color:#24363b; font-size:0.8rem; letter-spacing:0.05em;">TRIAL</div>
                <div style="color:#3d3d3d; font-size:0.75rem; margin-top:4px;">{_sb_trial_days} days remaining</div>
            </div>
        """, unsafe_allow_html=True)

    # 4. NAVIGATION
    st.markdown('<div class="nav-header">APPS</div>', unsafe_allow_html=True)

    def set_page(page):
        st.session_state['app_mode'] = page
        
    # DAILY TOOLS
    st.button("DASHBOARD", width="stretch", on_click=set_page, args=("DASHBOARD",))
    st.button("VISUAL COMPLIANCE", width="stretch", on_click=set_page, args=("VISUAL COMPLIANCE",))
    st.button("COPY EDITOR", width="stretch", on_click=set_page, args=("COPY EDITOR",))
    st.button("CONTENT GENERATOR", width="stretch", on_click=set_page, args=("CONTENT GENERATOR",))
    st.button("SOCIAL MEDIA ASSISTANT", width="stretch", on_click=set_page, args=("SOCIAL MEDIA ASSISTANT",))
    st.button("ACTIVITY LOG", width="stretch", on_click=set_page, args=("ACTIVITY LOG",))
    
    # ADMIN TOOLS (NO DIVIDER)
    st.button("BRAND ARCHITECT", width="stretch", on_click=set_page, args=("BRAND ARCHITECT",))
    st.button("TEAM MANAGEMENT", width="stretch", on_click=set_page, args=("TEAM MANAGEMENT",))
    st.button("SUBSCRIPTION", width="stretch", on_click=set_page, args=("SUBSCRIPTION",))

    # SUPER ADMIN ONLY
    _sb_tier = st.session_state.get('tier', {}).get('_tier_key', '')
    _sb_user = (st.session_state.get('username') or '').upper()
    if _sb_tier == 'super_admin' or _sb_user == 'NICK_ADMIN':
        st.markdown("---")
        st.button("ADMIN PANEL", width="stretch", on_click=set_page, args=("ADMIN PANEL",))

    # Footer Spacer
    st.markdown('<div style="margin-bottom: 30px;"></div>', unsafe_allow_html=True)
    
    # 5. TRUST FOOTER
    current_org = st.session_state.get('org_id', 'Unknown')
    st.markdown(f"""
        <div style='font-size: 0.7rem; color: #5c6b61; margin-top: 10px; margin-bottom: 20px;'>
            <strong>SECURE INSTANCE</strong><br>
            Org: {current_org}<br>
            End-to-End Encrypted.
        </div>
    """, unsafe_allow_html=True)

    with st.expander("CHANGE PASSWORD"):
        with st.form("change_password_form"):
            cp_current = st.text_input("Current Password", type="password", key="cp_current")
            cp_new = st.text_input("New Password", type="password", key="cp_new")
            cp_confirm = st.text_input("Confirm New Password", type="password", key="cp_confirm")
            if st.form_submit_button("Update Password"):
                _cp_user = st.session_state.get('username', '')
                if not cp_current or not cp_new:
                    st.error("All fields are required.")
                elif len(cp_new) < 8:
                    st.error("New password must be at least 8 characters.")
                elif cp_new != cp_confirm:
                    st.error("New passwords do not match.")
                elif not db.check_login(_cp_user, cp_current):
                    st.error("Current password is incorrect.")
                else:
                    db.reset_user_password(_cp_user, cp_new)
                    st.success("Password updated.")

    if st.button("LOGOUT", width="stretch"):
        # End impersonation if active
        if st.session_state.get('admin_session'):
            admin_panel._end_impersonation()
        st.session_state['authenticated'] = False
        st.session_state['username'] = None
        st.session_state['profiles'] = {}
        st.session_state.pop('admin_session', None)
        st.session_state.pop('tier', None)
        st.session_state.pop('usage', None)
        st.session_state.pop('subscription_status', None)
        st.rerun()

# --- BRIDGE VARIABLES ---
app_mode = st.session_state.get('app_mode', 'DASHBOARD')
active_profile = st.session_state.get('active_profile_name')

# --- ANALYTICS: Debounced page_view tracking ---
if st.session_state.get('_last_tracked_page') != app_mode:
    _pa_user = st.session_state.get('username')
    _pa_sid = st.session_state.get('_analytics_session_id')
    if _pa_user and _pa_sid:
        db.track_event("page_view", _pa_user,
                       metadata={"page": app_mode},
                       session_id=_pa_sid,
                       org_id=st.session_state.get('org_id'))
    st.session_state['_last_tracked_page'] = app_mode
        
def _get_tier_key() -> str:
    return st.session_state.get('tier', {}).get('_tier_key', 'solo')

def _is_super_admin() -> bool:
    raw_user = (st.session_state.get('username') or '').upper()
    return _get_tier_key() == 'super_admin' or raw_user == 'NICK_ADMIN'

def _subscription_active() -> bool:
    return st.session_state.get('subscription_status', 'inactive') == 'active'

def _is_trial_user() -> bool:
    return bool(st.session_state.get('tier', {}).get('_is_trial'))

def _trial_days_remaining() -> int:
    return st.session_state.get('tier', {}).get('_trial_days_remaining', 0)

def _is_sample_brand_active() -> bool:
    """True if the currently selected brand is the sample brand."""
    active = st.session_state.get('active_profile_name', '')
    return active and 'Meridian Labs' in active and '(Sample' in active


def _show_trial_gate():
    """Renders a trial gate notice when a trial user selects a non-sample brand."""
    st.markdown("""
        <div style="background:rgba(171,143,89,0.08); border-left:3px solid #ab8f59;
                    padding:16px 20px; margin:12px 0 20px 0; border-radius:2px;">
            <div style="font-weight:700; color:#24363b; font-size:0.95rem;">Trial Mode</div>
            <div style="color:#3d3d3d; margin-top:6px; font-size:0.85rem; line-height:1.5;">
                During your trial, you can run modules against the <strong>Meridian Labs sample brand</strong>
                to explore the platform. Select the sample brand from the sidebar to continue.<br><br>
                Subscribe to unlock full access with your own brands.
            </div>
        </div>
    """, unsafe_allow_html=True)


def _track_module_and_cost(module_name, metadata_extra=None):
    """Fire module_action and api_cost events after an AI module action."""
    try:
        _user = st.session_state.get('username', '')
        _sid = st.session_state.get('_analytics_session_id')
        _org = st.session_state.get('org_id')
        _profiles = st.session_state.get('profiles', {})
        _active = st.session_state.get('active_profile_name')
        _cal = 0
        if _active and _active in _profiles:
            _p = _profiles[_active]
            if isinstance(_p, dict):
                _cal = _p.get('calibration_score', 0)

        meta = {"module": module_name, "engine_confidence": _cal}
        if metadata_extra:
            meta.update(metadata_extra)
        db.track_event("module_action", _user, metadata=meta,
                       session_id=_sid, org_id=_org)

        # Onboarding: first module run
        db.check_milestone(_user, "first_module_run", session_id=_sid, org_id=_org)

        # API cost tracking from logic engine
        usage = logic_engine._last_usage
        if usage:
            cost = db.estimate_api_cost(
                usage['input_tokens'], usage['output_tokens'],
                model=logic_engine.model
            )
            db.track_event("api_cost", _user, metadata={
                "module": module_name,
                "model": logic_engine.model,
                "input_tokens": usage['input_tokens'],
                "output_tokens": usage['output_tokens'],
                "estimated_cost_usd": cost,
            }, session_id=_sid, org_id=_org)
            logic_engine._last_usage = None
    except Exception:
        pass  # Tracking never breaks the app


def _get_engine_confidence():
    """Return current active brand's calibration score."""
    _profiles = st.session_state.get('profiles', {})
    _active = st.session_state.get('active_profile_name')
    if _active and _active in _profiles:
        _p = _profiles[_active]
        if isinstance(_p, dict):
            return _p.get('calibration_score', 0)
    return 0


def render_feedback(module_name, action_id_key, question="Did this match your brand?"):
    """Render inline feedback row below module output. One click, three options."""
    action_id = st.session_state.get(action_id_key)
    if not action_id:
        return
    feedback_key = f"feedback_{module_name}_{action_id}"

    if st.session_state.get(feedback_key):
        st.markdown(
            '<p style="color: #5c6b61; font-size: 14px; margin-top: 20px; letter-spacing: 0.02em;">'
            'Thanks. This helps the platform improve.</p>',
            unsafe_allow_html=True
        )
        return

    st.markdown(
        f'<p style="color: #5c6b61; font-size: 14px; margin-top: 20px; letter-spacing: 0.02em; text-transform: uppercase;">'
        f'{question}</p>',
        unsafe_allow_html=True
    )
    _fb_cols = st.columns([1, 1, 1, 3])
    for col, (label, rating) in zip(
        [_fb_cols[0], _fb_cols[1], _fb_cols[2]],
        [("YES", "yes"), ("CLOSE", "close"), ("NO", "no")]
    ):
        with col:
            if st.button(label, key=f"fb_{module_name}_{action_id}_{rating}"):
                st.session_state[feedback_key] = rating
                try:
                    _user = st.session_state.get('username', '')
                    _sid = st.session_state.get('_analytics_session_id')
                    _org = st.session_state.get('org_id')
                    _brand = st.session_state.get('active_profile_name', '')
                    db.track_event("output_feedback", _user, metadata={
                        "module": module_name,
                        "action_id": action_id,
                        "rating": rating,
                        "engine_confidence": _get_engine_confidence(),
                    }, brand_id=_brand, session_id=_sid, org_id=_org)
                except Exception:
                    pass
                st.rerun()


def show_paywall():
    """Renders inline inactive subscription message (no st.stop — module UI still visible)."""
    _pw_is_trial_expired = st.session_state.get('tier', {}).get('_subscription_status') == 'inactive' and \
                           db.get_trial_info(st.session_state.get('username', '')).get('trial_expired') if \
                           db.get_trial_info(st.session_state.get('username', '')) else False
    _pw_title = "Trial Expired" if _pw_is_trial_expired else "Subscription Inactive"
    _pw_desc = (
        "Your 14-day trial has ended. Your brand data is safe &mdash; subscribe to pick up where you left off."
        if _pw_is_trial_expired else
        "Your subscription is inactive. Your brand data is safe &mdash; reactivate anytime to pick up where you left off."
    )
    st.markdown(f"""
        <style>
            .paywall-card {{
                background-color: #1b2a2e;
                border: 1px solid #ab8f59;
                padding: 40px;
                text-align: center;
                border-radius: 4px;
                margin-top: 20px;
                margin-bottom: 20px;
                box-shadow: 0 20px 50px rgba(0,0,0,0.5);
            }}
            .paywall-icon {{ margin-bottom: 20px; display: flex; justify-content: center; }}
            .paywall-title {{
                color: #f5f5f0; font-family: 'Montserrat', 'Helvetica Neue', Arial, sans-serif;
                font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;
                font-size: 1.5rem; margin-bottom: 10px;
            }}
            .paywall-desc {{ color: #5c6b61; margin-bottom: 30px; font-size: 1rem; line-height: 1.6; }}
        </style>
        <div class="paywall-card">
            <div class="paywall-icon">
                <svg width="40" height="48" viewBox="0 0 20 24" xmlns="http://www.w3.org/2000/svg">
                    <path d="M10 0L20 4V12C20 18.6 14.2 22.8 10 24C5.8 22.8 0 18.6 0 12V4L10 0Z" fill="#ab8f59"/>
                    <line x1="6" y1="4" x2="13" y2="12" stroke="#24363b" stroke-width="2" stroke-linecap="round"/>
                    <line x1="13" y1="12" x2="8" y2="20" stroke="#24363b" stroke-width="2" stroke-linecap="round"/>
                    <line x1="14" y1="6" x2="10" y2="15" stroke="#24363b" stroke-width="1.5" stroke-linecap="round"/>
                </svg>
            </div>
            <div class="paywall-title">{_pw_title}</div>
            <div class="paywall-desc">{_pw_desc}</div>
        </div>
    """, unsafe_allow_html=True)
    if st.button("VIEW PLANS", use_container_width=True):
        st.session_state['app_mode'] = "SUBSCRIPTION"
        st.rerun()


def _show_suspension_notice():
    """Renders a suspension notice if the current user is suspended."""
    if st.session_state.get('is_suspended'):
        st.markdown("""
        <div style="background:rgba(166,120,77,0.08); border-left:3px solid #a6784d;
                    padding:16px 20px; margin:12px 0; border-radius:2px;">
            <div style="font-weight:700; color:#24363b; font-size:0.95rem;">Account Suspended</div>
            <div style="color:#3d3d3d; margin-top:6px; font-size:0.85rem; line-height:1.5;">
                Your account has been temporarily suspended. If you believe this is an error,
                contact support@castellanpr.com.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return True
    return False


def _is_suspended():
    return st.session_state.get('is_suspended', False)


# --- IMPERSONATION BANNER ---
if st.session_state.get('admin_session'):
    _imp_user = st.session_state.get('username', 'Unknown')
    _imp_tier = st.session_state.get('tier', {}).get('display_name', 'Unknown')
    st.markdown(f"""
        <div style="background-color: #cc3300; color: white; padding: 10px 20px; text-align: center;
                    font-weight: 800; letter-spacing: 0.1em; font-size: 0.85rem; margin-bottom: 15px;
                    border-radius: 4px;">
            ADMIN MODE: Viewing as {_imp_user} ({_imp_tier})
        </div>
    """, unsafe_allow_html=True)
    if st.button("Return to Admin Panel", key="imp_return_btn"):
        admin_panel._end_impersonation()

# --- ANNOUNCEMENT BANNER ---
_announcement = db.get_platform_setting("announcement") if st.session_state.get('authenticated') else None
if _announcement:
    st.info(_announcement)

# --- POST-CHECKOUT RETURN ---
if _checkout_success and st.session_state.get('authenticated'):
    st.markdown("""
        <div style="background:rgba(171,143,89,0.12); border:1px solid #ab8f59; padding:16px 20px;
                    border-radius:4px; margin-bottom:16px; text-align:center;">
            <div style="font-weight:700; color:#24363b; font-size:1rem; letter-spacing:0.05em;">SUBSCRIPTION PROCESSING</div>
            <div style="color:#3d3d3d; margin-top:8px; font-size:0.85rem; line-height:1.5;">
                Your subscription is being activated. This usually takes a few seconds.
                If your status doesn't update automatically, click the button below.
            </div>
        </div>
    """, unsafe_allow_html=True)
    _pcc1, _pcc2, _pcc3 = st.columns([1, 1, 1])
    with _pcc2:
        if st.button("SYNC NOW", use_container_width=True):
            import time as _pct
            st.session_state.pop('_tier_resolved_at', None)
            _new_tier = sub_manager.resolve_user_tier(st.session_state.get('username', ''))
            st.session_state['tier'] = _new_tier
            st.session_state['subscription_status'] = _new_tier.get('_subscription_status', 'inactive')
            st.session_state['status'] = st.session_state['subscription_status']
            st.session_state['_tier_resolved_at'] = _pct.time()
            st.session_state['usage'] = sub_manager.check_usage_limit(st.session_state.get('username', ''))
            st.query_params.clear()
            st.rerun()

# --- ADMIN PANEL ROUTING ---
if app_mode == "ADMIN PANEL":
    admin_panel.render_admin_panel()

# --- MODULES ---

# 1. DASHBOARD
elif app_mode == "DASHBOARD":
    
    # --- DATA RETRIEVAL ---
    profiles = st.session_state.get('profiles', {})
    active_profile_name = st.session_state.get('active_profile_name')
    username = st.session_state.get('username')
    org_id = st.session_state.get('org_id')
    is_admin = st.session_state.get('is_admin', False)
    
    # --- EMPTY STATE: NEW USER (0 PROFILES) ---
    if len(profiles) == 0:
        st.markdown("""
        <div style='text-align: center; padding: 60px 20px 40px 20px;'>
            <h2 style='color: #ab8f59; margin-bottom: 20px; font-size: 2rem; letter-spacing: 0.1em;'>
                BRAND FIDELITY BEGINS HERE
            </h2>
            <p style='font-size: 1.1rem; line-height: 1.6; margin-bottom: 40px; max-width: 700px; margin-left: auto; margin-right: auto;'>
                Whether you manage one brand or ten, every piece of content should sound exactly like the brand it represents. Signet makes sure it does.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("BUILD BRAND PROFILE", use_container_width=True, type="primary"):
                st.session_state['app_mode'] = "BRAND ARCHITECT"
                st.rerun()

            # Sample brand button (empty state)
            _has_sample = db.has_sample_brand(st.session_state.get('user_id', ''))
            if _has_sample:
                st.button("Sample Brand Already Loaded", use_container_width=True, disabled=True, key="empty_sample_loaded")
            else:
                if st.button("Try a Sample Brand", use_container_width=True, key="empty_load_sample"):
                    _uid = st.session_state.get('user_id', '')
                    db.load_sample_brand(_uid)
                    st.session_state['profiles'] = db.get_profiles(_uid)
                    st.success("Sample brand loaded! Meridian Labs is now available in your brand list. Explore the Brand Architect to see how a complete brand profile is structured, then try generating content or running an audit.")
                    import time as _t; _t.sleep(2)
                    st.rerun()

        st.markdown("""
        <div style='max-width: 600px; margin: 40px auto 0 auto; padding: 20px; border-left: 3px solid #5c6b61;'>
            <p style='margin-bottom: 10px; font-weight: 600; color: #ab8f59;'>A Brand Profile contains:</p>
            <ul style='line-height: 1.8;'>
                <li>Voice Samples (3+ reference samples per communication type)</li>
                <li>Visual Identity (color palette, logo specifications)</li>
                <li>Strategy &amp; Message House (mission, values, guardrails, positioning)</li>
            </ul>
            <p style='margin-top: 20px; color: #5c6b61;'>
                Once calibrated, all modules are ready to use.
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.stop()  # Don't show the rest of dashboard
    
    # --- RETURNING USER STATE (1+ PROFILES) ---
    # Profile selector (auto-select if only one profile)
    if len(profiles) == 1:
        selected_profile = list(profiles.keys())[0]
        st.session_state['active_profile_name'] = selected_profile
    else:
        selected_profile = st.selectbox(
            "SELECT BRAND PROFILE",
            list(profiles.keys()),
            index=list(profiles.keys()).index(active_profile_name) if active_profile_name in profiles else 0,
            key="dash_profile_selector"
        )
        st.session_state['active_profile_name'] = selected_profile

    selected_profile = selected_profile or list(profiles.keys())[0]
    current_profile = profiles[selected_profile]

    # Calculate calibration data
    cal_data = calculate_calibration_score(current_profile)
    score = cal_data.get('score', 0)
    status_label = cal_data.get('status_label', 'UNKNOWN')
    cluster_health = cal_data.get('clusters', {})
    social_platforms = cal_data.get('social_platforms', {"LinkedIn": 0, "Instagram": 0, "Twitter/X": 0})
    mh_sub = cal_data.get('mh_sub_score', 0)
    mh_ceiling = cal_data.get('mh_ceiling_active', False)
    mh_filled = cal_data.get('mh_filled_fields', 0)
    mh_total = cal_data.get('mh_total_fields', 8)

    # Get structured inputs for completion helpers
    _dash_inputs = current_profile.get('inputs', {}) if isinstance(current_profile, dict) else {}

    # Calibration color
    if score < 40:
        cal_color = "#bd0000"
    elif score < 80:
        cal_color = "#eeba2b"
    else:
        cal_color = "#5c6b61"

    # ========================================
    # PANEL 1: BRAND HEADER (full-width)
    # ========================================
    _p1_left, _p1_right = st.columns([3, 1])
    with _p1_left:
        st.markdown(f"""
        <div style='padding: 10px 0 5px 0;'>
            <div style='font-size: 1.6rem; font-weight: 700; color: #f5f5f0; letter-spacing: 0.05em;'>{selected_profile}</div>
            <div style='font-size: 0.85rem; color: #5c6b61; margin-top: 2px;'>{len(profiles)} brand{'s' if len(profiles) != 1 else ''} loaded</div>
        </div>
        """, unsafe_allow_html=True)
    with _p1_right:
        st.markdown(f"""
        <div style='text-align: right; padding: 5px 0;'>
            <div style='font-size: 0.75rem; color: #ab8f59; letter-spacing: 0.1em;'>ENGINE CONFIDENCE</div>
            <div style='font-size: 2.2rem; font-weight: 800; color: {cal_color}; line-height: 1.1;'>{int(score)}%</div>
            <div style='font-size: 0.8rem; color: {cal_color};'>{map_calibration_status(status_label)}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='border-bottom: 1px solid #5c6b61; margin: 5px 0 20px 0;'></div>", unsafe_allow_html=True)

    # ========================================
    # PANEL 2: CALIBRATION OVERVIEW
    # ========================================
    _p2_left, _p2_right = st.columns([1, 1])

    with _p2_left:
        st.markdown("<div style='font-size: 0.9rem; color: #ab8f59; letter-spacing: 0.1em; margin-bottom: 12px; font-weight: 600;'>CALIBRATION SUMMARY</div>", unsafe_allow_html=True)

        # Strategy card
        strat = calculate_strategy_completion(_dash_inputs)
        _strat_pct = strat['pct']
        st.markdown(f"""
        <div style='background: rgba(27, 42, 46, 0.5); border-left: 3px solid #5c6b61; padding: 10px 12px; margin-bottom: 8px;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span style='font-size: 0.8rem; font-weight: 600;'>Strategy</span>
                <span style='font-size: 0.8rem; color: #ab8f59;'>{strat['filled']}/{strat['total']} Fields</span>
            </div>
            <div style='background: #1b2a2e; height: 4px; margin-top: 6px; border-radius: 2px;'>
                <div style='background: #5c6b61; height: 4px; width: {_strat_pct}%; border-radius: 2px;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Message House card
        _mh_pct = min(mh_sub, 100)
        _mh_color = "#ff4b4b" if mh_ceiling else ("#ffa421" if mh_sub < 50 else "#5c6b61")
        _mh_label = "Not Configured" if mh_ceiling else (f"{mh_filled}/{mh_total} Fields" if mh_sub < 50 else f"{mh_filled}/{mh_total} Fields")
        st.markdown(f"""
        <div style='background: rgba(27, 42, 46, 0.5); border-left: 3px solid {_mh_color}; padding: 10px 12px; margin-bottom: 8px;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span style='font-size: 0.8rem; font-weight: 600;'>Message House</span>
                <span style='font-size: 0.8rem; color: {_mh_color};'>{_mh_label}</span>
            </div>
            <div style='background: #1b2a2e; height: 4px; margin-top: 6px; border-radius: 2px;'>
                <div style='background: {_mh_color}; height: 4px; width: {_mh_pct}%; border-radius: 2px;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if mh_ceiling:
            st.markdown("<div style='font-size: 0.75rem; color: #ff4b4b; margin: -4px 0 8px 12px;'>Engine capped at 55% — configure Message House to unlock full calibration.</div>", unsafe_allow_html=True)

        # Visual Identity card
        vis = calculate_visual_completion(_dash_inputs)
        _vis_pct = vis['pct']
        _vis_status = []
        if vis['has_palette']: _vis_status.append("Palette")
        if vis['has_visual_assets']: _vis_status.append("Assets")
        _vis_label = " + ".join(_vis_status) if _vis_status else "Not Configured"
        st.markdown(f"""
        <div style='background: rgba(27, 42, 46, 0.5); border-left: 3px solid #5c6b61; padding: 10px 12px; margin-bottom: 8px;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span style='font-size: 0.8rem; font-weight: 600;'>Visual Identity</span>
                <span style='font-size: 0.8rem; color: #ab8f59;'>{_vis_label}</span>
            </div>
            <div style='background: #1b2a2e; height: 4px; margin-top: 6px; border-radius: 2px;'>
                <div style='background: #5c6b61; height: 4px; width: {_vis_pct}%; border-radius: 2px;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Social Calibration card
        _soc_total = sum(social_platforms.values())
        _soc_calibrated = sum(1 for c in social_platforms.values() if c >= 3)
        _soc_pct = min((_soc_calibrated / 3) * 100, 100)
        _soc_label = f"{_soc_calibrated}/3 Platforms" if _soc_total > 0 else "Not Configured"
        st.markdown(f"""
        <div style='background: rgba(27, 42, 46, 0.5); border-left: 3px solid #5c6b61; padding: 10px 12px; margin-bottom: 8px;'>
            <div style='display: flex; justify-content: space-between; align-items: center;'>
                <span style='font-size: 0.8rem; font-weight: 600;'>Social Calibration</span>
                <span style='font-size: 0.8rem; color: #ab8f59;'>{_soc_label}</span>
            </div>
            <div style='background: #1b2a2e; height: 4px; margin-top: 6px; border-radius: 2px;'>
                <div style='background: #5c6b61; height: 4px; width: {_soc_pct}%; border-radius: 2px;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with _p2_right:
        st.markdown("<div style='font-size: 0.9rem; color: #ab8f59; letter-spacing: 0.1em; margin-bottom: 12px; font-weight: 600;'>CALIBRATION DETAIL</div>", unsafe_allow_html=True)

        # Voice Clusters (5 rows — each rendered individually for SVG compatibility)
        cluster_display_names = {
            "Corporate": "Corporate Affairs",
            "Crisis": "Crisis & Response",
            "Internal": "Internal Leadership",
            "Thought": "Thought Leadership",
            "Marketing": "Brand Marketing"
        }
        for key, full_name in cluster_display_names.items():
            data = cluster_health.get(key, {"count": 0, "status": "EMPTY"})
            count = data.get('count', 0)
            status = data.get('status', 'EMPTY')
            icon = data.get('icon', brand_ui.SHIELD_DEGRADATION)
            pct = min((count / 3) * 100, 100)
            mapped = map_calibration_status(status)
            _status_color = "#5c6b61" if status == "FORTIFIED" else ("#eeba2b" if status == "UNSTABLE" else "#5c6b61")
            st.markdown(f"""<div style='display: flex; align-items: center; gap: 8px; margin-bottom: 6px; padding: 6px 0;'>
                <span style='flex-shrink: 0;'>{icon}</span>
                <span style='flex: 1; font-size: 0.8rem; min-width: 120px;'>{full_name}</span>
                <div style='flex: 1; background: #1b2a2e; height: 4px; border-radius: 2px; min-width: 60px;'>
                    <div style='background: {_status_color}; height: 4px; width: {pct}%; border-radius: 2px;'></div>
                </div>
                <span style='font-size: 0.75rem; color: #5c6b61; min-width: 50px; text-align: right;'>{count}/3</span>
                <span style='font-size: 0.7rem; color: {_status_color}; min-width: 110px; text-align: right;'>{mapped}</span>
            </div>""", unsafe_allow_html=True)

        # Social Platforms (3 rows)
        st.markdown("<div style='font-size: 0.8rem; color: #ab8f59; margin: 8px 0 6px 0; font-weight: 600;'>SOCIAL PLATFORMS</div>", unsafe_allow_html=True)
        for plat_name, plat_count in social_platforms.items():
            plat_pct = min((plat_count / 3) * 100, 100)
            if plat_count >= 3:
                plat_status = "Calibrated"
                plat_color = "#5c6b61"
            elif plat_count >= 1:
                plat_status = "Partially Calibrated"
                plat_color = "#eeba2b"
            else:
                plat_status = "Not Calibrated"
                plat_color = "#5c6b61"
            st.markdown(f"""<div style='display: flex; align-items: center; gap: 8px; margin-bottom: 6px; padding: 4px 0;'>
                <span style='flex: 1; font-size: 0.8rem; min-width: 80px;'>{plat_name}</span>
                <div style='flex: 1; background: #1b2a2e; height: 4px; border-radius: 2px; min-width: 60px;'>
                    <div style='background: {plat_color}; height: 4px; width: {plat_pct}%; border-radius: 2px;'></div>
                </div>
                <span style='font-size: 0.75rem; color: #5c6b61; min-width: 50px; text-align: right;'>{plat_count}/3</span>
                <span style='font-size: 0.7rem; color: {plat_color}; min-width: 110px; text-align: right;'>{plat_status}</span>
            </div>""", unsafe_allow_html=True)

    st.markdown("<div style='border-bottom: 1px solid rgba(92, 107, 97, 0.3); margin: 20px 0;'></div>", unsafe_allow_html=True)

    # ========================================
    # PANEL 3: RECENT ACTIVITY
    # ========================================
    _p3_left, _p3_right = st.columns([3, 1])
    with _p3_left:
        st.markdown("<div style='font-size: 0.9rem; color: #ab8f59; letter-spacing: 0.1em; font-weight: 600;'>RECENT ACTIVITY</div>", unsafe_allow_html=True)
    with _p3_right:
        if st.button("VIEW FULL LOG", use_container_width=True, key="dash_view_log"):
            st.session_state.app_mode = "ACTIVITY LOG"
            st.rerun()

    try:
        logs = db.get_org_logs(org_id, limit=15)
        if not is_admin:
            logs = [log for log in logs if log.get('username') == username]

        if logs:
            _is_impersonating = bool(st.session_state.get('admin_session'))
            _log_html = ""
            for log in logs:
                _ts = log.get('timestamp', '')
                _created = log.get('created_at', '')
                _time_display = format_activity_time(_ts, _created)
                _activity = log.get('activity_type', 'UNKNOWN')
                _asset = log.get('asset_name', '')
                _verdict = log.get('verdict', '')
                _score_val = log.get('score', 0)
                _log_user = log.get('username', '')

                if 'VISUAL' in _activity:
                    _detail = f"{'PASS' if _score_val > 60 else 'REVIEW'} ({_score_val}%)"
                elif 'EDIT' in _activity or 'COPY' in _activity:
                    _detail = _verdict
                elif 'GENERATION' in _activity or 'CONTENT' in _activity:
                    try:
                        _meta = json.loads(log.get('metadata_json', '{}'))
                        _wc = _meta.get('word_count', '')
                        _detail = f"{_wc} words" if isinstance(_wc, int) else _verdict
                    except (json.JSONDecodeError, TypeError):
                        _detail = _verdict
                else:
                    _detail = _verdict

                _user_col = f"<span style='color: #5c6b61; margin-right: 8px;'>{_log_user}</span>" if _is_impersonating or is_admin else ""
                _asset_display = f" &mdash; {_asset}" if _asset else ""
                _log_html += f"""
                <div style='background: rgba(27, 42, 46, 0.4); padding: 8px 12px; margin-bottom: 4px; border-left: 2px solid #5c6b61; font-size: 0.8rem;'>
                    <span style='color: #ab8f59;'>{_time_display}</span>
                    <span style='color: #5c6b61; margin: 0 6px;'>|</span>
                    {_user_col}<span style='font-weight: 600;'>{_activity}</span>{_asset_display}
                    <span style='color: #5c6b61; margin: 0 6px;'>|</span>
                    <span>{_detail}</span>
                </div>
                """
            st.markdown(_log_html, unsafe_allow_html=True)
        else:
            st.markdown("<div style='color: #5c6b61; font-size: 0.85rem; padding: 15px 0;'>No activity recorded yet. Run an audit or generate content to see results here.</div>", unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading activity log: {e}")

    st.markdown("<div style='border-bottom: 1px solid rgba(92, 107, 97, 0.3); margin: 20px 0;'></div>", unsafe_allow_html=True)

    # ========================================
    # PANEL 4: QUICK ACTIONS
    # ========================================
    st.markdown("<div style='font-size: 0.9rem; color: #ab8f59; letter-spacing: 0.1em; margin-bottom: 12px; font-weight: 600;'>QUICK ACTIONS</div>", unsafe_allow_html=True)
    _qa1, _qa2, _qa3, _qa4 = st.columns(4)
    with _qa1:
        if st.button("VISUAL AUDIT", use_container_width=True, key="dash_qa_visual"):
            st.session_state['app_mode'] = "VISUAL COMPLIANCE"
            st.rerun()
        st.caption("Audit images against palette standards")
    with _qa2:
        if st.button("COPY EDITOR", use_container_width=True, key="dash_qa_copy"):
            st.session_state['app_mode'] = "COPY EDITOR"
            st.rerun()
        st.caption("Enforce voice across written content")
    with _qa3:
        if st.button("CONTENT GENERATOR", use_container_width=True, key="dash_qa_content"):
            st.session_state['app_mode'] = "CONTENT GENERATOR"
            st.rerun()
        st.caption("Generate brand-calibrated copy")
    with _qa4:
        if st.button("SOCIAL ASSISTANT", use_container_width=True, key="dash_qa_social"):
            st.session_state['app_mode'] = "SOCIAL MEDIA ASSISTANT"
            st.rerun()
        st.caption("Cross-channel consistency analysis")

    # ========================================
    # BRAND MANAGEMENT (below 3-col layout)
    # ========================================
    st.markdown("---")
    st.markdown("### BRAND MANAGEMENT")

    _bm_uid = st.session_state.get('user_id', '')
    _bm_org_id, _bm_org_role, _bm_tier_key = db.get_brand_owner_info(_bm_uid)
    _bm_is_owner = _bm_org_role in ('owner', 'admin') or _bm_tier_key == 'super_admin' or _bm_org_id == _bm_uid
    _bm_is_sa = _get_tier_key() == 'super_admin' or (st.session_state.get('username') or '').upper() == 'NICK_ADMIN'

    bm_col1, bm_col2 = st.columns(2)

    with bm_col1:
        # Sample brand load/remove
        _bm_has_sample = db.has_sample_brand(_bm_uid)
        if _bm_has_sample:
            st.markdown("**Meridian Labs (Sample Brand)** is loaded.")
            if st.button("Remove Sample Brand", key="dash_remove_sample"):
                st.session_state['_confirm_remove_sample'] = True
            if st.session_state.get('_confirm_remove_sample'):
                st.warning("Remove the sample brand? You can reload it anytime.")
                _rc1, _rc2 = st.columns(2)
                with _rc1:
                    if st.button("Yes, Remove", key="dash_confirm_remove_sample", type="primary"):
                        db.delete_sample_brand(_bm_uid)
                        st.session_state['profiles'] = db.get_profiles(_bm_uid)
                        # Clear active profile if it was the sample brand
                        if st.session_state.get('active_profile_name', '').startswith("Meridian Labs"):
                            remaining = list(st.session_state['profiles'].keys())
                            st.session_state['active_profile_name'] = remaining[0] if remaining else None
                        st.session_state.pop('_confirm_remove_sample', None)
                        st.rerun()
                with _rc2:
                    if st.button("Cancel", key="dash_cancel_remove_sample"):
                        st.session_state.pop('_confirm_remove_sample', None)
                        st.rerun()
        else:
            if st.button("Load Sample Brand", key="dash_load_sample"):
                db.load_sample_brand(_bm_uid)
                st.session_state['profiles'] = db.get_profiles(_bm_uid)
                st.success("Sample brand loaded! Meridian Labs is now available in your brand list.")
                import time as _t; _t.sleep(1.5)
                st.rerun()

    with bm_col2:
        # Brand deletion
        brand_check = sub_manager.check_brand_limit(_bm_uid)
        st.caption(f"Brands: {brand_check['current']} / {'Unlimited' if brand_check['max'] == -1 else brand_check['max']}")

        # Downgrade notice: over limit
        if not brand_check['allowed'] and brand_check['max'] > 0 and brand_check['current'] > brand_check['max']:
            st.markdown("""
                <div style="background:rgba(166,120,77,0.08); border-left:3px solid #a6784d;
                            padding:10px 12px; margin-bottom:10px; border-radius:2px; font-size:0.8rem; color:#3d3d3d;">
                    Your brands are preserved, but you can't create new ones until you're under your plan limit.
                </div>
            """, unsafe_allow_html=True)

        _del_candidates = [
            name for name in profiles.keys()
            if not db.is_profile_sample(_bm_uid, name)
        ]
        if _del_candidates:
            del_brand = st.selectbox("Select brand to delete", [""] + _del_candidates, key="dash_del_brand")
            if del_brand:
                if not (_bm_is_owner or _bm_is_sa):
                    st.info("Contact your account admin to delete this brand.")
                else:
                    if st.button("Delete Brand", type="secondary", key="dash_del_btn"):
                        st.session_state['_confirm_delete_brand'] = del_brand

                    if st.session_state.get('_confirm_delete_brand') == del_brand:
                        st.warning(
                            f"Deleting **{del_brand}** will permanently remove all brand data "
                            "including strategy, message house, voice samples, visual identity, "
                            "and usage history. This cannot be undone."
                        )
                        confirm_name = st.text_input(
                            "Type the brand name to confirm deletion",
                            key="dash_del_confirm_input"
                        )
                        if st.button("Confirm Delete", type="primary", key="dash_del_confirm_btn"):
                            if confirm_name.strip() == del_brand:
                                # Handle if deleting the active profile
                                if st.session_state.get('active_profile_name') == del_brand:
                                    remaining = [n for n in profiles.keys() if n != del_brand]
                                    st.session_state['active_profile_name'] = remaining[0] if remaining else None

                                db.delete_profile(_bm_uid, del_brand)
                                st.session_state['profiles'] = db.get_profiles(_bm_uid)
                                st.session_state.pop('_confirm_delete_brand', None)

                                # Analytics: brand deleted
                                db.track_event("brand_deleted", st.session_state.get('username', ''),
                                               metadata={"name": del_brand},
                                               session_id=st.session_state.get('_analytics_session_id'),
                                               org_id=st.session_state.get('org_id'))

                                new_count = db.count_user_brands(_bm_org_id)
                                max_b = brand_check['max']
                                slots_msg = f"{new_count} / {'Unlimited' if max_b == -1 else max_b}"
                                st.success(f"Brand deleted. You now have {slots_msg} brand slots used.")
                                import time as _t; _t.sleep(1.5)
                                st.rerun()
                            else:
                                st.error("Brand name does not match. Deletion cancelled.")

# 2. VISUAL COMPLIANCE (The 5-Pillar Scorecard)
elif app_mode == "VISUAL COMPLIANCE":
    st.title("VISUAL COMPLIANCE AUDIT")
    brand_ui.render_module_help("visual_audit")

    # Trial gate: must use sample brand
    if _is_trial_user() and not _is_sample_brand_active():
        _show_trial_gate()

    # --- CSS INJECTION ---
    st.markdown("""
        <style>
        div.stButton > button[kind="primary"] {
            background-color: #ab8f59 !important;
            color: #1b2a2e !important;
            -webkit-text-fill-color: #1b2a2e !important;
            border: none !important;
            font-weight: 800 !important;
            letter-spacing: 1px !important;
        }
        div.stButton > button[kind="primary"] p {
            color: #1b2a2e !important;
            -webkit-text-fill-color: #1b2a2e !important;
        }
        .score-card {
            background-color: #1E1E1E;
            border: 1px solid #333;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        .metric-label {
            color: #888;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: 700;
            color: #ab8f59;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # --- SUBSCRIPTION GATE ---
    if not _is_super_admin() and not _subscription_active():
        show_paywall()

    # --- HELPER: ASSET LIBRARY RETRIEVAL (UPDATED) ---
    def get_all_visual_assets(profile_data):
        """Parses visual and social sample blobs to find ALL saved images."""
        inputs = profile_data.get('inputs', {})
        assets = {}
        
        # WE NOW SCAN BOTH VISUAL AND SOCIAL SAMPLE BLOBS
        sources = [inputs.get('visual_dna', ''), inputs.get('social_dna', '')]

        import base64
        from io import BytesIO

        for source_text in sources:
            if not source_text: continue
            
            chunks = source_text.split("----------------\n")
            for chunk in chunks:
                if "[VISUAL_REF:" in chunk:
                    # Extract Name from Header [ASSET: TYPE - NAME]
                    lines = chunk.strip().split('\n')
                    name = "Unknown Asset"
                    if lines and "[ASSET:" in lines[0]:
                        name = lines[0].replace("[ASSET:", "").replace("]", "").strip()
                    
                    # Extract Image
                    for line in lines:
                        if line.startswith("[VISUAL_REF:"):
                            b64 = line.replace("[VISUAL_REF:", "").replace("]", "").strip()
                            if b64.startswith("data:image"): 
                                try:
                                    b64_clean = b64.split(",")[1]
                                    image_data = base64.b64decode(b64_clean)
                                    
                                    # Handle Duplicates (e.g. multiple "LinkedIn Post" assets)
                                    key = name
                                    count = 2
                                    while key in assets:
                                        key = f"{name} ({count})"
                                        count += 1
                                        
                                    assets[key] = Image.open(BytesIO(image_data))
                                except: 
                                    pass
        return assets

    # --- HELPER: COLLAGE MAKER ---
    def create_reference_collage(image_list):
        """Stitches multiple reference images into one 'Reference Sheet' for the AI."""
        if not image_list: return None
        if len(image_list) == 1: return image_list[0]
        
        # Resize all to same height (e.g., 300px) to make a clean strip
        target_height = 300
        resized_imgs = []
        total_width = 0
        
        for img in image_list:
            aspect = img.width / img.height
            new_width = int(target_height * aspect)
            resized = img.resize((new_width, target_height))
            resized_imgs.append(resized)
            total_width += new_width + 10 # 10px padding
            
        # Create canvas
        collage = Image.new('RGB', (total_width, target_height), (255, 255, 255))
        x_offset = 0
        for img in resized_imgs:
            collage.paste(img, (x_offset, 0))
            x_offset += img.width + 10
            
        return collage

    # 1. Check if Profile is Active
    active_profile_name = st.session_state.get('active_profile_name')
    if not active_profile_name or active_profile_name not in st.session_state.get('profiles', {}):
        st.warning("No Brand Profile Loaded. Please select one in the Sidebar.")
    else:
        profile_data = st.session_state['profiles'][active_profile_name]

        # --- PERSISTENCE CHECK ---
        if 'active_audit_result' in st.session_state and st.session_state['active_audit_result']:
            result = st.session_state['active_audit_result']
            image = st.session_state.get('active_audit_image')
            
            c_info, c_reset = st.columns([3, 1])
            with c_info: st.info("RESTORED PREVIOUS SESSION")
            with c_reset: 
                if st.button("START NEW AUDIT", type="secondary", use_container_width=True):
                    del st.session_state['active_audit_result']
                    del st.session_state['active_audit_image']
                    st.rerun()
            
            st.divider()
            # Result Display Logic is below...
        else:
            # --- UPLOAD & CONFIGURATION ---
            c1, c2 = st.columns([1, 1])
            
            with c1:
                st.markdown("### 1. UPLOAD CANDIDATE")
                uploaded_file = st.file_uploader("Upload the draft to check", type=['png', 'jpg', 'jpeg', 'webp'])
                if uploaded_file:
                    image = Image.open(uploaded_file)
                    st.image(image, caption="Candidate", use_container_width=True)
            
            with c2:
                st.markdown("### 2. CONTEXT & STANDARDS")
                _va_labels = [v["label"] for v in VISUAL_ASSET_TYPES.values()]
                asset_type = st.selectbox("What are we auditing?", _va_labels)

                # Retrieve All Assets (Updated Function)
                all_assets = get_all_visual_assets(profile_data)

                # Determine Smart Defaults based on Asset Type
                default_selections = []
                # 1. Always look for Logo
                for name in all_assets.keys():
                    if "LOGO" in name.upper(): default_selections.append(name)

                # 2. Look for Context Matches
                _va_keyword_map = {
                    "Social Media Graphic": "SOCIAL",
                    "Marketing Page / Website": "WEB",
                    "Email Template": "EMAIL",
                    "Presentation Slide": "SLIDE",
                    "Advertisement": "AD",
                    "Document / Letterhead": "DOC",
                    "Logo Usage": "LOGO",
                }
                key = _va_keyword_map.get(asset_type, "")
                for name in all_assets.keys():
                    if key and key in name.upper() and name not in default_selections:
                        default_selections.append(name)
                
                # Cap defaults at 3 to allow room for user choice
                default_selections = default_selections[:3]

                st.markdown("##### 3. REFERENCE ANCHORS")
                if all_assets:
                    selected_asset_names = st.multiselect(
                        "Compare against (Max 5 recommended):", 
                        options=list(all_assets.keys()),
                        default=default_selections
                    )
                    
                    # Preview the Reference Sheet
                    if selected_asset_names:
                        selected_imgs = [all_assets[n] for n in selected_asset_names]
                        collage = create_reference_collage(selected_imgs)
                        st.image(collage, caption="Active Reference Sheet (Brand Benchmark)", use_container_width=True)
                    else:
                        st.info("No visual references selected. Auditing based on Text Rules only.")
                else:
                    st.markdown(brand_ui.render_severity("drift", "No visual assets found in Brand Manager."), unsafe_allow_html=True)
                    st.caption("The engine will rely on your Color Palette and Tone rules. Upload assets in 'Social Media' or 'Visual ID' to enable comparison.")
                    selected_asset_names = []

            st.divider()

            # --- OPTIONAL CONTEXT ---
            asset_description = st.text_input(
                "Asset context (optional — helps the AI select the right voice cluster for comparison)",
                placeholder="e.g. 'New landing page hero section' or 'Email newsletter header'",
                key="va_asset_description",
            )

            _show_suspension_notice()
            if st.button("RUN COMPLIANCE CHECK", type="primary", use_container_width=True,
                         disabled=not (_is_super_admin() or _subscription_active()) or _is_suspended()):
                if uploaded_file:
                    inputs = profile_data.get('inputs', {})

                    # Check if brand has enough data for any meaningful audit
                    _has_palette = bool(inputs.get('palette_primary'))
                    _has_any_brand = _has_palette or bool(inputs.get('wiz_tone')) or bool(inputs.get('wiz_guardrails'))
                    if not _has_any_brand:
                        st.error("This brand doesn't have enough data for a meaningful audit. Add at least a hex palette or brand strategy in the Brand Architect first.")
                    else:
                        # 1. PREPARE REFERENCE IMAGE
                        reference_image_obj = None
                        if selected_asset_names:
                            imgs = [all_assets[n] for n in selected_asset_names]
                            reference_image_obj = create_reference_collage(imgs)

                        _asset_ctx = asset_description.strip() if asset_description else asset_type

                        # --- LAYER 1: COLOR COMPLIANCE (deterministic, fast) ---
                        with st.spinner("Layer 1/3: Analyzing color compliance..."):
                            color_result = visual_audit.run_color_compliance(image, inputs)

                        # Show color results immediately
                        _cs = color_result.get('score')
                        if color_result.get('skipped'):
                            st.info("Color compliance skipped — no hex palette defined.")
                        elif _cs is not None:
                            _cc = "#09ab3b" if _cs >= 80 else "#ffa421" if _cs >= 50 else "#ff4b4b"
                            st.markdown(f"<div style='padding:8px; border-left:3px solid {_cc};'><strong>Color Compliance:</strong> {_cs}/100</div>", unsafe_allow_html=True)

                        # --- LAYER 2: VISUAL IDENTITY (AI) ---
                        with st.spinner("Layer 2/3: Analyzing visual identity..."):
                            visual_result = visual_audit.run_visual_identity_check(
                                image, inputs,
                                color_result.get('detected_hexes', []),
                                reference_image=reference_image_obj,
                            )

                        # --- LAYER 3: COPY & MESSAGING (AI) ---
                        with st.spinner("Layer 3/3: Extracting and analyzing copy..."):
                            copy_result = visual_audit.run_copy_compliance(image, inputs)

                        # --- ASSEMBLE UNIFIED REPORT ---
                        ai_was_used = (
                            (visual_result.get('score') is not None and 'error' not in visual_result)
                            or (copy_result.get('score') is not None and not copy_result.get('skipped') and 'error' not in copy_result)
                        )

                        # Scoring
                        weights = {}
                        if color_result.get('score') is not None:
                            weights['color'] = (color_result['score'], 0.30)
                        if visual_result.get('score') is not None:
                            weights['visual'] = (visual_result['score'], 0.30)
                        if copy_result.get('score') is not None and not copy_result.get('skipped'):
                            weights['copy'] = (copy_result['score'], 0.40)

                        if weights:
                            _tw = sum(w for _, w in weights.values())
                            overall_score = int(sum(s * (w / _tw) for s, w in weights.values()))
                        else:
                            overall_score = 0
                        overall_score = max(0, min(100, overall_score))

                        if overall_score >= 90: verdict = "STRONG COMPLIANCE"
                        elif overall_score >= 70: verdict = "NEEDS ATTENTION"
                        else: verdict = "SIGNIFICANT ISSUES"

                        # Collect findings
                        all_findings = []
                        for f in color_result.get('findings', []):
                            f['section'] = 'Color Compliance'
                            all_findings.append(f)
                        for f in visual_result.get('findings', []):
                            f['section'] = 'Visual Identity'
                            all_findings.append(f)
                        for f in copy_result.get('findings', []):
                            f['section'] = 'Copy & Messaging'
                            all_findings.append(f)

                        # Build summary
                        _n_crit = sum(1 for f in all_findings if f.get('severity') == 'CRITICAL')
                        _n_warn = sum(1 for f in all_findings if f.get('severity') == 'WARNING')
                        _n_pass = sum(1 for f in all_findings if f.get('type') == 'pass')
                        _sum_parts = []
                        if _n_crit: _sum_parts.append(f"{_n_crit} critical issue{'s' if _n_crit != 1 else ''}")
                        if _n_warn: _sum_parts.append(f"{_n_warn} warning{'s' if _n_warn != 1 else ''}")
                        if _n_pass: _sum_parts.append(f"{_n_pass} check{'s' if _n_pass != 1 else ''} passed")
                        exec_summary = ". ".join(_sum_parts) + "." if _sum_parts else "Audit completed."

                        result = {
                            'overall_score': overall_score,
                            'verdict': verdict,
                            'summary': exec_summary,
                            'brand_name': inputs.get('wiz_name', 'Unknown'),
                            'asset_context': _asset_ctx,
                            'timestamp': __import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M'),
                            'color_result': color_result,
                            'visual_result': visual_result,
                            'copy_result': copy_result,
                            'all_findings': all_findings,
                            'scores': {
                                'color': color_result.get('score'),
                                'visual': visual_result.get('score'),
                                'copy': copy_result.get('score'),
                            },
                            'ai_was_used': ai_was_used,
                        }

                        # Save state
                        st.session_state['active_audit_result'] = result
                        st.session_state['active_audit_image'] = image

                        # Log to DB
                        db.log_event(
                            org_id=st.session_state.get('org_id', 'Unknown'),
                            username=st.session_state.get('username', 'Unknown'),
                            activity_type="VISUAL AUDIT",
                            asset_name=uploaded_file.name,
                            score=overall_score,
                            verdict=verdict,
                            metadata={'scores': result['scores'], 'summary': exec_summary}
                        )

                        # Record AI action ONLY if AI was actually used
                        if ai_was_used:
                            sub_manager.record_ai_action(st.session_state.get('user_id', ''), 'visual_audit', f"Audit: {uploaded_file.name} — {verdict} ({overall_score}%)")
                            st.session_state['usage'] = sub_manager.check_usage_limit(st.session_state.get('user_id', ''))
                            _track_module_and_cost("visual_audit", {"filename": uploaded_file.name})

                        st.session_state['_action_id_visual_audit'] = str(uuid.uuid4())[:8]
                        st.rerun()
                else:
                    st.warning("Please upload an image.")

        # ═══════════════════════════════════════════════════════
        # UNIFIED AUDIT REPORT DISPLAY
        # ═══════════════════════════════════════════════════════
        if st.session_state.get('active_audit_result'):
            result = st.session_state['active_audit_result']
            _scores = result.get('scores', {})
            _findings = result.get('all_findings', [])

            # --- REPORT HEADER ---
            overall_score = result.get('overall_score', 0)
            score_color = "#ff4b4b"
            if overall_score >= 70: score_color = "#ffa421"
            if overall_score >= 90: score_color = "#09ab3b"

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1b2a2e 0%, #24363b 100%); border: 1px solid {score_color}; padding: 20px 30px; border-radius: 4px; margin-bottom: 20px;">
                <div style="font-size: 0.75rem; color: #ab8f59; letter-spacing: 2px; font-weight: 700; margin-bottom: 4px;">BRAND COMPLIANCE AUDIT — {html.escape(result.get('brand_name', ''))}</div>
                <div style="font-size: 0.7rem; color: #5c6b61;">Audited: {result.get('timestamp', '')} | Asset: {html.escape(result.get('asset_context', 'Screenshot'))}</div>
            </div>
            """, unsafe_allow_html=True)

            # --- SCORE + LAYER BARS ---
            sc_left, sc_right = st.columns([1, 2])
            with sc_left:
                st.markdown(f"""
                <div style="background-color: #1b2a2e; border: 1px solid {score_color}; padding: 30px; border-radius: 4px; text-align: center;">
                    <h2 style="color: {score_color}; margin: 0; font-size: 3.5rem; font-weight: 800; letter-spacing: -2px;">{overall_score}</h2>
                    <p style="color: #5c6b61; margin: 0; letter-spacing: 2px; font-weight: 700; text-transform: uppercase; font-size: 0.8rem;">{result.get('verdict', 'ANALYZED')}</p>
                </div>
                """, unsafe_allow_html=True)
                st.caption(result.get('summary', ''))

            with sc_right:
                def render_bar(label, val, weight_txt, skipped=False):
                    if skipped or val is None:
                        st.markdown(f"""
                        <div style="margin-bottom: 8px;">
                            <div style="display:flex; justify-content:space-between; font-size:0.8rem; font-weight:700; color:#a0a0a0;">
                                <span>{label} <span style="font-weight:400; font-style:italic;">{weight_txt}</span></span>
                                <span style="color:#5c6b61;">Skipped</span>
                            </div>
                            <div style="width:100%; height:6px; background:#3d3d3d; border-radius:3px;"></div>
                        </div>
                        """, unsafe_allow_html=True)
                        return
                    try: val = int(val)
                    except: val = 0
                    color = "#09ab3b" if val > 80 else "#ffa421" if val > 50 else "#ff4b4b"
                    st.markdown(f"""
                    <div style="margin-bottom: 8px;">
                        <div style="display:flex; justify-content:space-between; font-size:0.8rem; font-weight:700; color:#a0a0a0;">
                            <span>{label} <span style="font-weight:400; font-style:italic;">{weight_txt}</span></span>
                            <span style="color:{color};">{val}/100</span>
                        </div>
                        <div style="width:100%; height:6px; background:#3d3d3d; border-radius:3px; overflow:hidden;">
                            <div style="width:{val}%; height:100%; background:{color};"></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                _color_skip = result.get('color_result', {}).get('skipped', False)
                _copy_skip = result.get('copy_result', {}).get('skipped', False)
                render_bar("COLOR COMPLIANCE", _scores.get('color'), "(30%)", skipped=_color_skip)
                render_bar("VISUAL IDENTITY", _scores.get('visual'), "(30%)")
                render_bar("COPY & MESSAGING", _scores.get('copy'), "(40%)", skipped=_copy_skip)

            st.divider()

            # --- CSS FOR FINDINGS ---
            st.markdown("""
            <style>
                .geo-bullet-red { display: inline-block; width: 8px; height: 8px; background-color: #ff4b4b; margin-right: 8px; transform: rotate(45deg); }
                .geo-bullet-orange { display: inline-block; width: 8px; height: 8px; background-color: #ffa421; margin-right: 8px; border-radius: 50%; }
                .geo-bullet-green { display: inline-block; width: 8px; height: 8px; background-color: #09ab3b; margin-right: 8px; }
                .audit-item { font-size: 0.85rem; color: #24363b; margin-bottom: 12px; border-left: 2px solid #3d3d3d; padding-left: 12px; line-height: 1.4; }
                .audit-item strong { color: #24363b; }
            </style>
            """, unsafe_allow_html=True)

            # --- SECTION 1: COLOR COMPLIANCE ---
            with st.expander("1. COLOR COMPLIANCE", expanded=True):
                cr = result.get('color_result', {})
                if cr.get('skipped'):
                    st.info(cr.get('reasoning', 'Skipped.'))
                else:
                    st.markdown(f"**Score:** {cr.get('score', 0)}/100")
                    if cr.get('detected_colors_with_pct'):
                        det_swatches = " ".join(
                            f"<span style='display:inline-block;width:20px;height:20px;background:{h};border:1px solid #555;margin-right:4px;vertical-align:middle;'></span><code>{h}</code><span style='font-size:0.72rem;color:#5c6b61;margin-right:10px;'> ({pct}%)</span>"
                            for h, pct in cr['detected_colors_with_pct']
                        )
                        st.markdown(f"**Detected Colors:** {det_swatches}", unsafe_allow_html=True)
                    elif cr.get('detected_hexes'):
                        det_swatches = " ".join(
                            f"<span style='display:inline-block;width:20px;height:20px;background:{h};border:1px solid #555;margin-right:4px;vertical-align:middle;'></span><code>{h}</code>"
                            for h in cr['detected_hexes']
                        )
                        st.markdown(f"**Detected Colors:** {det_swatches}", unsafe_allow_html=True)
                    if cr.get('brand_hexes'):
                        brand_swatches = " ".join(
                            f"<span style='display:inline-block;width:20px;height:20px;background:{h};border:1px solid #555;margin-right:4px;vertical-align:middle;'></span><code>{h}</code>"
                            for h in cr['brand_hexes']
                        )
                        st.markdown(f"**Brand Palette:** {brand_swatches}", unsafe_allow_html=True)
                    st.caption(cr.get('reasoning', ''))
                    for f in cr.get('findings', []):
                        _icon = {"pass": "&#10004;", "warning": "&#9888;", "fail": "&#10008;"}.get(f.get('type'), '')
                        _col = {"PASS": "#09ab3b", "WARNING": "#ffa421", "CRITICAL": "#ff4b4b"}.get(f.get('severity'), '#a0a0a0')
                        st.markdown(f"<div class='audit-item' style='border-left-color:{_col};'>{_icon} {html.escape(f.get('text', ''))}</div>", unsafe_allow_html=True)

            # --- SECTION 2: VISUAL IDENTITY COMPLIANCE ---
            with st.expander("2. VISUAL IDENTITY COMPLIANCE", expanded=True):
                vr = result.get('visual_result', {})
                if vr.get('error'):
                    st.warning(f"Visual identity check could not be completed: {vr.get('error', '')}")
                elif vr.get('score') is not None:
                    st.markdown(f"**Score:** {vr.get('score', 0)}/100")
                    if vr.get('summary'):
                        st.caption(vr['summary'])
                    for f in vr.get('findings', []):
                        _type = f.get('type', 'pass')
                        if _type == 'pass':
                            _prefix, _bul, _col = "BRAND FIDELITY", "geo-bullet-green", "#09ab3b"
                        elif _type == 'warning':
                            _prefix, _bul, _col = "BRAND DRIFT", "geo-bullet-orange", "#ffa421"
                        else:
                            _prefix, _bul, _col = "BRAND DEGRADATION", "geo-bullet-red", "#ff4b4b"
                        _guideline = f.get('guideline', '')
                        _sev = f" (Severity: {f.get('severity')})" if f.get('severity') in ('CRITICAL', 'WARNING') else ""
                        st.markdown(
                            f"<div class='audit-item' style='border-left-color:{_col};'>"
                            f"<div class='{_bul}'></div><strong>{_prefix}</strong> — {_guideline}: {html.escape(f.get('text', ''))}{_sev}</div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.info("Visual identity check was not performed.")

            # --- SECTION 3: COPY & MESSAGING COMPLIANCE ---
            with st.expander("3. COPY & MESSAGING COMPLIANCE", expanded=True):
                cpr = result.get('copy_result', {})
                if cpr.get('skipped'):
                    st.info(cpr.get('summary', 'Copy compliance skipped.'))
                elif cpr.get('error'):
                    st.warning(f"Copy analysis could not be completed: {cpr.get('error', '')}")
                elif cpr.get('score') is not None:
                    st.markdown(f"**Score:** {cpr.get('score', 0)}/100")
                    if cpr.get('text_summary'):
                        st.markdown(f"**Extracted Text Summary:** {cpr['text_summary']}")
                    if cpr.get('summary'):
                        st.caption(cpr['summary'])
                    for f in cpr.get('findings', []):
                        _type = f.get('type', 'pass')
                        if _type == 'pass':
                            _prefix, _bul, _col = "BRAND FIDELITY", "geo-bullet-green", "#09ab3b"
                        elif _type == 'warning':
                            _prefix, _bul, _col = "BRAND DRIFT", "geo-bullet-orange", "#ffa421"
                        else:
                            _prefix, _bul, _col = "BRAND DEGRADATION", "geo-bullet-red", "#ff4b4b"
                        _guideline = f.get('guideline', '')
                        _sev = f" (Severity: {f.get('severity')})" if f.get('severity') in ('CRITICAL', 'WARNING') else ""
                        st.markdown(
                            f"<div class='audit-item' style='border-left-color:{_col};'>"
                            f"<div class='{_bul}'></div><strong>{_prefix}</strong> — {_guideline}: {html.escape(f.get('text', ''))}{_sev}</div>",
                            unsafe_allow_html=True
                        )
                    # Show extracted text in expander
                    if cpr.get('extracted_text'):
                        with st.expander("View Extracted Text"):
                            st.text(cpr['extracted_text'])
                else:
                    st.info("Copy & messaging check was not performed.")

            # --- RECOMMENDATIONS ---
            recs = [f for f in _findings if f.get('type') in ('fail', 'warning')]
            if recs:
                with st.expander("RECOMMENDATIONS (Prioritized)"):
                    _sorted = sorted(recs, key=lambda x: {"CRITICAL": 0, "WARNING": 1, "NOTE": 2}.get(x.get('severity', 'NOTE'), 2))
                    for i, f in enumerate(_sorted, 1):
                        _sev = f.get('severity', 'NOTE')
                        _col = {"CRITICAL": "#ff4b4b", "WARNING": "#ffa421"}.get(_sev, "#a0a0a0")
                        _section = f.get('section', '')
                        st.markdown(
                            f"<div style='margin-bottom:10px; padding:8px 12px; border-left:3px solid {_col}; font-size:0.85rem;'>"
                            f"<strong style='color:{_col};'>{_sev}</strong> [{_section}] {html.escape(f.get('text', ''))}</div>",
                            unsafe_allow_html=True
                        )

            render_feedback("visual_audit", "_action_id_visual_audit",
                            question="Were these findings accurate?")

    # --- REAL MVP: TEAM MANAGEMENT (Only for Admins) ---
    if app_mode == "TEAM MANAGEMENT":
        st.title("TEAM MANAGEMENT")
        
        # Check permissions
        if not st.session_state.get('is_admin', False) and raw_user != "NICK_ADMIN":
            st.error("ACCESS DENIED. This area is restricted to Organization Admins.")
            st.stop()
            
        current_org = st.session_state.get('org_id', 'Unknown')
        st.markdown(f"**ORGANIZATION:** {current_org}")
        st.divider()
        
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.markdown("### ACTIVE SEATS")
            users = db.get_users_by_org(current_org)
            if users:
                import pandas as pd
                df = pd.DataFrame(users, columns=["USERNAME", "EMAIL", "IS ADMIN", "CREATED AT"])
                df['IS ADMIN'] = df['IS ADMIN'].apply(lambda x: "ADMIN" if x else "MEMBER")
                st.dataframe(df, hide_index=True, use_container_width=True)
            else:
                st.info("No team members found.")
                
        with c2:
            st.markdown("### ADD TEAM MEMBER")
            _team_tier = st.session_state.get('tier', {}).get('_tier_key', 'solo')
            if _team_tier == 'solo' and not _is_super_admin():
                st.info("The **Solo** plan supports 1 seat. Upgrade to Agency or Enterprise to add team members.")
            else:
                _seat_check = sub_manager.check_seat_limit(current_org)
                if not _seat_check['allowed']:
                    _tier_name = st.session_state.get('tier', {}).get('display_name', 'your plan')
                    st.warning(f"Seat limit reached ({_seat_check['current']}/{_seat_check['max']}) for {_tier_name}. Contact us to upgrade.")
                else:
                    with st.form("add_team_member"):
                        new_user = st.text_input("USERNAME", max_chars=64)
                        new_email = st.text_input("EMAIL", max_chars=120)
                        new_pass = st.text_input("TEMP PASSWORD", type="password", max_chars=64)
                        submitted = st.form_submit_button("CREATE SEAT")

                        if submitted:
                            if new_user and new_pass:
                                if db.create_user(new_user, new_email, new_pass, org_id=current_org, is_admin=False):
                                    st.success(f"User {new_user} added to {current_org}!")
                                    st.rerun()
                                else:
                                    st.error("Operation Failed: Either the username exists OR you have reached your Seat Limit.")
                            else:
                                st.warning("All fields required.")

# 3. COPY EDITOR (Stateful, Diff View, Rationale, Calibrated)
elif app_mode == "COPY EDITOR":
    st.title("COPY EDITOR")
    brand_ui.render_module_help("copy_editor")

    # Trial gate: must use sample brand
    if _is_trial_user() and not _is_sample_brand_active():
        _show_trial_gate()

    # --- CSS INJECTION ---
    st.markdown("""
        <style>
        div.stButton > button[kind="primary"] {
            background-color: #ab8f59 !important;
            color: #1b2a2e !important;
            -webkit-text-fill-color: #1b2a2e !important;
            border: none !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
        }
        div.stButton > button[kind="primary"] p {
            color: #1b2a2e !important;
            -webkit-text-fill-color: #1b2a2e !important;
        }
        .rationale-box {
            background-color: rgba(171, 143, 89, 0.1);
            border-left: 3px solid #ab8f59;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 0.9rem;
            color: #e0e0e0;
        }
        .calibration-bar {
            width: 100%;
            height: 8px;
            background-color: #3d3d3d;
            border-radius: 4px;
            margin-top: 5px;
            margin-bottom: 5px;
            overflow: hidden;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- SUBSCRIPTION GATE ---
    if not _is_super_admin() and not _subscription_active():
        show_paywall()

    # --- HELPER: UNIFIED CONFIDENCE MODEL (FEW-SHOT + SAFETY) ---
    def calculate_copy_confidence(profile_data, content_type):
        """
        Combines 'Few-Shot' asset counting (Performance) with 'Risk' checks (Safety).
        """
        inputs = profile_data.get('inputs', {})
        voice_dna = inputs.get('voice_dna', '')
        
        score = 0
        color = "#ff4b4b" # Red
        label = "LOW DATA"
        rationale_parts = []
        action = ""

        # 1. ASSET VOLUME CHECK (The Research Layer)
        type_key = content_type.upper().split(" ")[0] # "INTERNAL", "PRESS", "BLOG"
        asset_count = voice_dna.upper().count(f"TYPE: {type_key}") + voice_dna.upper().count(f"ASSET: {type_key}")
        
        if asset_count >= 3:
            score += 50
            rationale_parts.append(f"High Stability ({asset_count} samples)")
        elif asset_count >= 1:
            score += 30
            rationale_parts.append(f"Low Stability ({asset_count} sample)")
            action = f"Upload {3-asset_count} more {content_type} samples for stable style transfer."
        else:
            rationale_parts.append("Zero-Shot (No samples)")
            action = f"Upload at least 3 {content_type} examples to Voice Calibration."

        # 2. RISK & COMPLIANCE CHECK (The Safety Layer)
        has_guardrails = len(inputs.get('wiz_guardrails', '')) > 10
        has_mission = len(inputs.get('wiz_mission', '')) > 10
        
        if has_guardrails:
            score += 30
            rationale_parts.append("Guardrails Active")
        else:
            action = "Add Guardrails in Strategy to ensure safety."
            
        if has_mission:
            score += 20
            rationale_parts.append("Mission Aligned")

        # 3. FINAL VERDICT
        if asset_count < 3 and score > 60:
            score = 60
            label = "CALIBRATING"
        elif score > 80:
            label = "HIGH CONFIDENCE"
            color = "#09ab3b"
        elif score > 50:
            label = "CALIBRATING"
            color = "#ffa421"
            
        return {
            "score": score,
            "color": color,
            "label": label,
            "rationale": ", ".join(rationale_parts) + ".",
            "action": action
        }

    if not active_profile: 
        st.warning("NO PROFILE SELECTED. Please choose a Brand Profile from the sidebar.")
    else:
        # --- STATE INITIALIZATION (GLOBAL PERSISTENCE) ---
        if 'ce_draft' not in st.session_state: st.session_state['ce_draft'] = ""
        if 'ce_sender' not in st.session_state: st.session_state['ce_sender'] = ""
        if 'ce_audience' not in st.session_state: st.session_state['ce_audience'] = ""
        if 'ce_result' not in st.session_state: st.session_state['ce_result'] = None
        if 'ce_rationale' not in st.session_state: st.session_state['ce_rationale'] = None
        if 'ce_rejected' not in st.session_state: st.session_state['ce_rejected'] = False
        if 'ce_reject_analysis' not in st.session_state: st.session_state['ce_reject_analysis'] = None
        if 'ce_findings' not in st.session_state: st.session_state['ce_findings'] = None

        # --- INPUT SECTION ---
        c1, c2 = st.columns([2, 1])
        
        with c1: 
            # Bind text area to session state via key
            st.text_area(
                "DRAFT TEXT", 
                height=350, 
                placeholder="Paste your rough draft here...",
                key="ce_draft",
                max_chars=10000
            )
            
            # Context Inputs
            cc1, cc2, cc3 = st.columns(3)
            with cc1:
                _ce_type_key, _ce_active_cluster, _ce_custom_desc, _ce_display_label = render_content_type_selector("editor", "ce")
                content_type = _ce_display_label
            with cc2:
                st.text_input("SENDER / VOICE", placeholder="e.g. CEO", key="ce_sender", max_chars=100)
            with cc3:
                st.text_input("TARGET AUDIENCE", placeholder="e.g. Investors", key="ce_audience", max_chars=100)
                
        with c2: 
            # --- DYNAMIC CALIBRATION METER ---
            profile_data = st.session_state['profiles'][active_profile]
            metrics = calculate_copy_confidence(profile_data, content_type)
            
            st.markdown(f"""<div class="dashboard-card" style="padding: 15px;">
                <div style="font-size:0.7rem; color:#5c6b61; font-weight:700;">TASK CONFIDENCE: {content_type.upper()}</div>
                <div style="font-size:1.6rem; font-weight:800; color:{metrics['color']}; margin-top:5px;">{metrics['score']}%</div>
                <div class="calibration-bar">
                    <div style="width:{metrics['score']}%; height:100%; background-color:{metrics['color']};"></div>
                </div>
                <div style="font-size:0.8rem; color:#f5f5f0; font-weight:700; margin-top:5px;">{metrics['label']}</div>
                <div style="font-size:0.7rem; color:#a0a0a0; margin-top:8px; line-height:1.2;"><em>{metrics['rationale']}</em></div>
            </div>""", unsafe_allow_html=True)
            
            # Dynamic Call to Action
            if metrics['action']:
                st.markdown(f"""
                    <div style="border-left: 2px solid {metrics['color']}; padding-left: 10px; margin-top: 10px; font-size: 0.8rem; color: #a0a0a0;">
                        <strong>Optimization Tip:</strong><br>
                        {metrics['action']}
                    </div>
                """, unsafe_allow_html=True)
                if st.button("GO TO CALIBRATION", type="secondary"):
                    st.session_state['app_mode'] = "BRAND MANAGER"
                    st.rerun()
            
            st.markdown("<br>", unsafe_allow_html=True)
            edit_intensity = st.select_slider(
                "EDIT INTENSITY", 
                options=["Polish", "Standard", "Aggressive"], 
                value="Standard",
                help="Polish: Fixes typos/minor tone. Aggressive: Total structural rewrite."
            )

            _show_suspension_notice()
            if st.button("REWRITE AND ALIGN", type="primary", use_container_width=True,
                         disabled=not (_is_super_admin() or _subscription_active()) or _is_suspended()):
                # Access via state key
                if st.session_state['ce_draft']:
                    st.session_state['ce_rejected'] = False
                    st.session_state['ce_reject_analysis'] = None
                    with st.spinner("CALIBRATING TONE & SYNTAX..."):
                        
                        # --- BRAND CONTEXT (via shared builder) ---
                        _ce_cluster = _ce_active_cluster
                        prof_text = build_brand_context(
                            profile_data,
                            include_voice_samples=True,
                            cluster_filter=_ce_cluster,
                        )

                        # Cluster override note for prompt
                        _ce_default_cluster = CONTENT_TYPES.get(_ce_type_key, {}).get("cluster")
                        _ce_override_note = ""
                        if _ce_cluster and _ce_default_cluster and _ce_cluster != _ce_default_cluster:
                            _ce_override_note = f"\nNote: The user has overridden the default voice cluster. Default for {content_type} is {_ce_default_cluster}, but the user selected {_ce_cluster}. Use voice samples from the {_ce_cluster} cluster.\n"

                        # Length context for auditing
                        _ce_std_range = get_word_range(_ce_type_key, "standard")
                        _ce_draft_wc = len(st.session_state['ce_draft'].split())
                        _ce_type_desc = content_type
                        if _ce_type_key == "custom" and _ce_custom_desc:
                            _ce_type_desc = f"Custom — {_ce_custom_desc}"

                        # Engineered Prompt
                        prompt_wrapper = f"""
CONTEXT:
- Brand: {active_profile}
- Type: {_ce_type_desc}
- Communication Style: {_ce_cluster or 'General'}{_ce_override_note}
- Sender: {st.session_state['ce_sender']}
- Audience: {st.session_state['ce_audience']}
- Intensity: {edit_intensity}
- Expected length for a {_ce_type_desc}: {_ce_std_range[0]}-{_ce_std_range[1]} words. The submitted draft is {_ce_draft_wc} words.

STEP 0: ORGANIZATION CHECK
Read the draft content below. Does it clearly belong to a different organization than "{active_profile}"?
Check for:
- A different company, institution, or entity referenced as "we", "our", or the author
- Letterhead, sign-off, or attribution to a named organization that is not "{active_profile}"
- Content that a natural reader would attribute to a specific, different organization

If the content CLEARLY belongs to a different organization:
Return ONLY this format (no rewrite):
TRIAGE: REJECT
IDENTIFIED ORG: [the organization the content appears to belong to]
ANALYSIS:
[Bullet list: what signals indicate this is wrong-org content]
RECOMMENDATION:
[What the user should do — switch brand profile, rewrite from scratch, etc.]

If the content does NOT clearly belong to a different organization (generic content, internal draft, or content that could reasonably be for this brand):
Proceed to STEP 1.

STEP 1: RATIONALE
Analyze the draft against the brand voice. Explain 3 key changes you are making and why.

STEP 2: REWRITE
Provide the rewritten text. Ensure all GUARDRAILS are strictly followed.

STEP 3: CLAIM CLASSIFICATION AND PROOF POINT VALIDATION

Review every assertion in the draft. Classify each into one of three categories before deciding whether to flag it:

CATEGORY 1 — PERFORMANCE CLAIMS (check against proof points)
These are measurable assertions about outcomes, results, metrics, capabilities, or competitive positioning. They include statistics, percentages, comparisons, superlatives about performance, and any statement that a skeptical reader would want evidence for.
Examples: revenue figures, growth metrics, customer outcomes, speed claims, reliability claims, market position claims.
→ CHECK these against the brand's approved proof point inventory (in the message house pillars above).
→ If the claim matches an approved proof point: ALIGNED.
→ If the claim contradicts an approved proof point (e.g., brand says 200+ teams but draft says 500+): DEGRADATION. Cite the conflicting proof point.
→ If the claim does not match any approved proof point but does not contradict one either: DRIFT. Note: "This performance claim is not codified in the approved proof point inventory. If accurate, consider adding it to the brand profile. Verify before publishing."

CATEGORY 2 — FACTUAL STATEMENTS (verify against brand profile if possible)
These are verifiable facts about the company that are NOT performance claims: locations, founding dates, team size, executive names, certifications held, integrations supported, product features that exist.
→ If the fact matches information in the brand profile (boilerplate, strategy fields): ALIGNED. No finding needed.
→ If the fact contradicts information in the brand profile (e.g., draft says "Founded in 2024" but boilerplate says "Founded in 2023"): DEGRADATION. Flag as a CONSISTENCY finding. Cite the specific contradiction.
→ If the fact cannot be verified against the brand profile (it's not mentioned anywhere): DRIFT. Note: "This factual statement is not reflected in the brand profile. If accurate, no action needed."
→ DO NOT flag basic factual statements as proof point violations. Headquarters, founding dates, team size, executive names, and certifications are facts, not claims.

CATEGORY 3 — POSITIONING & OPINION STATEMENTS (check against guardrails and positioning)
These are beliefs, perspectives, value statements, and competitive framing that reflect how the brand positions itself. They are not measurable but should align with the brand's documented positioning.
→ CHECK against the brand promise, POV statement, pillar headline claims, and messaging guardrails.
→ If aligned with documented positioning: ALIGNED.
→ If contradicting documented positioning or violating a messaging guardrail (off-limits topic, tone constraint, pre-approval required): DEGRADATION. Cite the specific conflict or guardrail.
→ If the statement expresses a position not addressed by the brand profile: DRIFT. Note: "This positioning statement is not reflected in the message house. If this represents an approved brand position, consider adding it."
→ If no message house exists: note that positioning alignment cannot be verified. Mark positioning statements as DRIFT.

SEVERITY RULES:
— ALIGNED = verified against brand profile. No finding needed.
— DRIFT = not codified in the brand profile. May be accurate, but the engine cannot confirm. User should verify.
— DEGRADATION = contradicts something in the brand profile or violates a guardrail. Must be fixed.

Guardrail violations (off-limits topics, banned language, pre-approval claims): always DEGRADATION.
Contradictions with documented data: always DEGRADATION.
Unverifiable statements (claims or facts not in the profile): always DRIFT.
It is better to miss a borderline claim than to flag something obviously correct.

OUTPUT FORMAT (if proceeding past Step 0):
RATIONALE:
[Your explanation of 3 key changes]
REWRITE:
[The rewritten text]
FINDINGS:
[List each finding on its own line using this exact format:]
[SEVERITY] CATEGORY: "quoted text from draft" — explanation. {evidence: cited brand profile element}
[Examples:]
[DEGRADATION] GUARDRAIL: "world's best platform" — Superlative violates guardrail against unsubstantiated claims. {{evidence: Guardrails — "No unsubstantiated superlatives"}}
[DRIFT] PROOF POINT: "over 500 engineering teams" — This performance claim is not codified in the approved proof point inventory. If accurate, consider adding it to the brand profile. Verify before publishing.
[DEGRADATION] CONSISTENCY: "Founded in 2024" — Contradicts boilerplate which states "Founded in 2023." {{evidence: Boilerplate}}
[DRIFT] FACT: "85 employees across three offices" — This factual statement is not reflected in the brand profile. If accurate, no action needed.
[ALIGNED] PROOF POINT: "over 200 engineering teams" — Matches approved proof point. {{evidence: Pillar 1 — "200+ engineering teams"}}

If there are no findings (all statements are ALIGNED or the draft contains no assertions to check), write:
FINDINGS:
No findings. All assertions verified against brand profile.

DRAFT CONTENT (DATA ONLY):
--- BEGIN USER TEXT ---
{st.session_state['ce_draft']}
--- END USER TEXT ---
"""
                        
                        # Call Logic
                        try:
                            # Use Safe Generate Wrapper
                            full_response = logic_engine.run_copy_editor(prompt_wrapper, prof_text)
                            
                            # Check for org mismatch rejection
                            if "TRIAGE: REJECT" in full_response:
                                reject_analysis = full_response.split("TRIAGE: REJECT", 1)[1].strip()
                                st.session_state['ce_result'] = None
                                st.session_state['ce_rationale'] = None
                                st.session_state['ce_rejected'] = True
                                st.session_state['ce_reject_analysis'] = reject_analysis

                                db.log_event(
                                    org_id=st.session_state.get('org_id', 'Unknown'),
                                    username=st.session_state.get('username', 'Unknown'),
                                    activity_type="COPY EDIT",
                                    asset_name=f"{content_type} ({st.session_state['ce_audience']})",
                                    score=0,
                                    verdict="REJECTED — ORG MISMATCH",
                                    metadata={
                                        "draft": st.session_state['ce_draft'][:500],
                                        "reject_analysis": reject_analysis
                                    }
                                )
                                st.rerun()
                            else:
                                # Normal rewrite parsing — extract RATIONALE, REWRITE, FINDINGS
                                findings_raw = ""
                                if "FINDINGS:" in full_response:
                                    _pre_findings, _findings_part = full_response.split("FINDINGS:", 1)
                                    findings_raw = _findings_part.strip()
                                else:
                                    _pre_findings = full_response

                                if "REWRITE:" in _pre_findings:
                                    parts = _pre_findings.split("REWRITE:")
                                    rationale = parts[0].replace("RATIONALE:", "").strip()
                                    rewrite = parts[1].strip()
                                else:
                                    rationale = "Automated alignment to brand voice."
                                    rewrite = _pre_findings

                                st.session_state['ce_rejected'] = False
                                st.session_state['ce_reject_analysis'] = None
                                st.session_state['ce_result'] = rewrite
                                st.session_state['ce_rationale'] = rationale
                                st.session_state['ce_findings'] = findings_raw if findings_raw else None

                                db.log_event(
                                    org_id=st.session_state.get('org_id', 'Unknown'),
                                    username=st.session_state.get('username', 'Unknown'),
                                    activity_type="COPY EDIT",
                                    asset_name=f"{content_type} ({st.session_state['ce_audience']})",
                                    score=metrics['score'],
                                    verdict="REWRITTEN",
                                    metadata={
                                        "draft": st.session_state['ce_draft'],
                                        "rewrite": rewrite,
                                        "rationale": rationale
                                    }
                                )
                                _ce_detail = f"Rewrite: {st.session_state['ce_draft'][:60]}..."
                                sub_manager.record_ai_action(st.session_state.get('user_id', ''), 'copy_editor', _ce_detail)
                                st.session_state['usage'] = sub_manager.check_usage_limit(st.session_state.get('user_id', ''))
                                st.session_state['_action_id_copy_editor'] = str(uuid.uuid4())[:8]
                                _track_module_and_cost("copy_editor", {
                                    "content_type": content_type,
                                    "input_length": len(st.session_state.get('ce_draft', '')),
                                })
                                st.rerun()

                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("Please enter text to rewrite.")

        # --- OUTPUT SECTION (Stateful) ---

        # Org mismatch rejection display
        if st.session_state.get('ce_rejected') and st.session_state.get('ce_reject_analysis'):
            st.divider()
            st.markdown("""
            <div style='border-left: 3px solid #a6784d; padding: 15px 20px; background: rgba(166, 120, 77, 0.08); margin-bottom: 20px;'>
                <div style='font-size: 0.9rem; font-weight: 700; color: #a6784d; margin-bottom: 10px;'>ORGANIZATION MISMATCH — REWRITE BLOCKED</div>
                <div style='font-size: 0.85rem; line-height: 1.6;'>
                    The submitted draft appears to belong to a different organization than the active brand profile.
                    The engine will not rewrite content that originates from a different entity — this prevents
                    cross-brand contamination.
                </div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div style='background: rgba(27, 42, 46, 0.5); padding: 15px 20px; border-left: 2px solid #5c6b61;'>
                <div style='font-size: 0.8rem; color: #ab8f59; margin-bottom: 8px; font-weight: 600;'>ANALYSIS</div>
                <div style='font-size: 0.85rem; line-height: 1.7;'>{st.session_state['ce_reject_analysis']}</div>
            </div>
            """, unsafe_allow_html=True)

        elif st.session_state['ce_result']:
            st.divider()

            # Message House notice
            _ce_inputs = st.session_state['profiles'].get(active_profile, {}).get('inputs', {}) if active_profile else {}
            if not build_mh_context(_ce_inputs):
                st.info("Message house not configured. Proofing limited to tone and voice pattern matching. Configure the Message House in Brand Architect for claim-level compliance checking.")

            # Rationale Box
            if st.session_state['ce_rationale']:
                _ce_rat_escaped = html.escape(st.session_state['ce_rationale']).replace('\n', '<br>')
                st.markdown(f"""
                    <div class="rationale-box">
                        <strong>STRATEGIC RATIONALE:</strong><br>
                        {_ce_rat_escaped}
                    </div>
                """, unsafe_allow_html=True)
            
            # View Toggle
            t1, t2 = st.tabs(["FINAL DRAFT", "DIFF VIEW"])

            with t1:
                st.text_area("FINAL COPY (Ready to Ship)", value=st.session_state['ce_result'], height=400)

            with t2:
                # Side-by-side comparison
                d1, d2 = st.columns(2)
                with d1:
                    st.caption("ORIGINAL")
                    st.info(st.session_state['ce_draft'])
                with d2:
                    st.caption("REWRITTEN")
                    st.success(st.session_state['ce_result'])

            # --- FINDINGS PANEL ---
            if st.session_state.get('ce_findings'):
                _findings_text = st.session_state['ce_findings']
                # Skip if no real findings
                if "No findings" not in _findings_text:
                    st.markdown("---")
                    st.markdown("##### COMPLIANCE FINDINGS")

                    # Parse findings into structured groups
                    _finding_pattern = re.compile(
                        r'\[(ALIGNED|DRIFT|DEGRADATION)\]\s*(PROOF POINT|GUARDRAIL|CONSISTENCY|FACT|POSITIONING|TONE|VOICE|MESSAGE HOUSE)[:\s]*"([^"]+)"\s*—\s*(.*?)(?=\n\[(?:ALIGNED|DRIFT|DEGRADATION)\]|\Z)',
                        re.DOTALL
                    )
                    _parsed = _finding_pattern.findall(_findings_text)

                    if _parsed:
                        # Group by severity
                        _degradations = [(cat, quote, expl) for sev, cat, quote, expl in _parsed if sev == "DEGRADATION"]
                        _drifts = [(cat, quote, expl) for sev, cat, quote, expl in _parsed if sev == "DRIFT"]
                        _aligned = [(cat, quote, expl) for sev, cat, quote, expl in _parsed if sev == "ALIGNED"]

                        # DEGRADATION findings (broken shield — must fix)
                        if _degradations:
                            st.markdown(f"""<div style="border-left: 3px solid #ff4b4b; padding: 10px 15px; margin-bottom: 12px; background: rgba(255, 75, 75, 0.06);">
                                <div style="font-size: 0.75rem; font-weight: 700; color: #ff4b4b; letter-spacing: 0.05em; margin-bottom: 8px;">DEGRADATION — {len(_degradations)} FINDING{'S' if len(_degradations) != 1 else ''} (FIX REQUIRED)</div>
                            """, unsafe_allow_html=True)
                            for _d_cat, _d_quote, _d_expl in _degradations:
                                _d_expl_esc = html.escape(_d_expl.strip())
                                _d_quote_esc = html.escape(_d_quote.strip())
                                st.markdown(f"""<div style="margin-bottom: 8px; font-size: 0.85rem; line-height: 1.5;">
                                    <span style="color: #ff4b4b; font-weight: 600;">{html.escape(_d_cat)}</span>:
                                    "<em>{_d_quote_esc}</em>" — {_d_expl_esc}
                                </div>""", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)

                        # DRIFT findings (cracked shield — verify)
                        if _drifts:
                            st.markdown(f"""<div style="border-left: 3px solid #ab8f59; padding: 10px 15px; margin-bottom: 12px; background: rgba(171, 143, 89, 0.06);">
                                <div style="font-size: 0.75rem; font-weight: 700; color: #ab8f59; letter-spacing: 0.05em; margin-bottom: 8px;">DRIFT — {len(_drifts)} FINDING{'S' if len(_drifts) != 1 else ''} (VERIFY BEFORE PUBLISHING)</div>
                            """, unsafe_allow_html=True)
                            for _dr_cat, _dr_quote, _dr_expl in _drifts:
                                _dr_expl_esc = html.escape(_dr_expl.strip())
                                _dr_quote_esc = html.escape(_dr_quote.strip())
                                st.markdown(f"""<div style="margin-bottom: 8px; font-size: 0.85rem; line-height: 1.5;">
                                    <span style="color: #ab8f59; font-weight: 600;">{html.escape(_dr_cat)}</span>:
                                    "<em>{_dr_quote_esc}</em>" — {_dr_expl_esc}
                                </div>""", unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)

                        # ALIGNED findings (gold shield — verified, collapsed)
                        if _aligned:
                            with st.expander(f"ALIGNED — {len(_aligned)} VERIFIED STATEMENT{'S' if len(_aligned) != 1 else ''}"):
                                for _a_cat, _a_quote, _a_expl in _aligned:
                                    _a_expl_esc = html.escape(_a_expl.strip())
                                    _a_quote_esc = html.escape(_a_quote.strip())
                                    st.markdown(f"""<div style="margin-bottom: 6px; font-size: 0.85rem; line-height: 1.5; color: #a0a0a0;">
                                        <span style="color: #5c6b61; font-weight: 600;">{html.escape(_a_cat)}</span>:
                                        "<em>{_a_quote_esc}</em>" — {_a_expl_esc}
                                    </div>""", unsafe_allow_html=True)
                    else:
                        # Couldn't parse structured findings — show raw
                        _findings_escaped = html.escape(_findings_text).replace('\n', '<br>')
                        st.markdown(f"""<div style="border-left: 2px solid #5c6b61; padding: 10px 15px; font-size: 0.85rem; line-height: 1.6;">
                            {_findings_escaped}
                        </div>""", unsafe_allow_html=True)

            render_feedback("copy_editor", "_action_id_copy_editor",
                            question="Were these findings accurate?")

# 4. CONTENT GENERATOR (Stateful, Calibrated, Structured)
elif app_mode == "CONTENT GENERATOR":
    st.title("CONTENT GENERATOR")
    brand_ui.render_module_help("content_generator")

    # Trial gate: must use sample brand
    if _is_trial_user() and not _is_sample_brand_active():
        _show_trial_gate()

    # --- CSS INJECTION ---
    st.markdown("""
        <style>
        div.stButton > button[kind="primary"] {
            background-color: #ab8f59 !important;
            color: #1b2a2e !important;
            -webkit-text-fill-color: #1b2a2e !important;
            border: none !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
        }
        div.stButton > button[kind="primary"] p {
            color: #1b2a2e !important;
            -webkit-text-fill-color: #1b2a2e !important;
        }
        .rationale-box {
            background-color: rgba(171, 143, 89, 0.1);
            border-left: 3px solid #ab8f59;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 0.9rem;
            color: #e0e0e0;
        }
        .calibration-bar {
            width: 100%;
            height: 8px;
            background-color: #3d3d3d;
            border-radius: 4px;
            margin-top: 5px;
            margin-bottom: 5px;
            overflow: hidden;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- SUBSCRIPTION GATE ---
    if not _is_super_admin() and not _subscription_active():
        show_paywall()

    # --- HELPER: HYBRID CONFIDENCE (FEW-SHOT + SAFETY) ---
    def calculate_content_confidence(profile_data, content_type):
        """
        Combines 'Few-Shot' asset counting (Performance) with 'Risk' checks (Safety).
        """
        inputs = profile_data.get('inputs', {})
        voice_dna = inputs.get('voice_dna', '')
        
        score = 0
        color = "#ff4b4b" # Red
        label = "LOW DATA"
        rationale_parts = []
        action = ""

        # 1. ASSET VOLUME CHECK (The Research Layer)
        # We count how many times this specific format appears in the voice samples
        type_key = content_type.upper().split(" ")[0] # "INTERNAL", "PRESS", "BLOG"
        asset_count = voice_dna.upper().count(f"TYPE: {type_key}") + voice_dna.upper().count(f"ASSET: {type_key}")
        
        if asset_count >= 3:
            score += 50
            rationale_parts.append(f"High Stability ({asset_count} samples)")
        elif asset_count >= 1:
            score += 30
            rationale_parts.append(f"Low Stability ({asset_count} sample)")
            action = f"Upload {3-asset_count} more {content_type} samples for stable style transfer."
        else:
            rationale_parts.append("Zero-Shot (No samples)")
            action = f"Upload at least 3 {content_type} examples to Voice Calibration."

        # 2. RISK & COMPLIANCE CHECK (The Safety Layer)
        has_guardrails = len(inputs.get('wiz_guardrails', '')) > 10
        has_mission = len(inputs.get('wiz_mission', '')) > 10
        
        if has_guardrails:
            score += 30
            rationale_parts.append("Guardrails Active")
        else:
            action = "Add Guardrails in Strategy to ensure safety."
            
        if has_mission:
            score += 20
            rationale_parts.append("Mission Aligned")

        # 3. FINAL VERDICT
        # Cap score if asset count is low, regardless of guardrails (Style cannot be forced)
        if asset_count < 3 and score > 60:
            score = 60
            label = "CALIBRATING"
        elif score > 80:
            label = "HIGH CONFIDENCE"
            color = "#09ab3b"
        elif score > 50:
            label = "CALIBRATING"
            color = "#ffa421"
            
        return {
            "score": score,
            "color": color,
            "label": label,
            "rationale": ", ".join(rationale_parts) + ".",
            "action": action
        }

    if not active_profile:
        st.warning("NO PROFILE SELECTED. Please choose a Brand Profile from the sidebar.")
    else:
        # --- STATE INITIALIZATION (Safety Fallback) ---
        # Note: Best practice is to have these at top of app.py, but we include checks here.
        if 'cg_topic' not in st.session_state: st.session_state['cg_topic'] = ""
        if 'cg_key_points' not in st.session_state: st.session_state['cg_key_points'] = ""
        if 'cg_result' not in st.session_state: st.session_state['cg_result'] = None
        if 'cg_rationale' not in st.session_state: st.session_state['cg_rationale'] = None

        # --- 1. INPUTS & DYNAMIC CALIBRATION ---
        c1, c2 = st.columns([2, 1])
        
        with c1:
            # Topic
            st.markdown("##### 1. CORE PARAMETERS")
            # Using key= automatically binds to st.session_state['cg_topic']
            st.text_input("TOPIC / HEADLINE", key="cg_topic", placeholder="e.g. Q3 Financial Results", max_chars=200)
            
            # Expanded Format List
            cc1, cc2 = st.columns(2)
            with cc1:
                _cg_type_key, _cg_active_cluster, _cg_custom_desc, _cg_display_label = render_content_type_selector("generator", "cg")
                content_type = _cg_display_label

            with cc2:
                _cg_length = st.select_slider(
                    "TARGET LENGTH",
                    options=["brief", "standard", "detailed"],
                    value="standard",
                    format_func=lambda x: get_length_label(_cg_type_key, x),
                    key="cg_length")
                _cg_word_range = get_word_range(_cg_type_key, _cg_length)
                st.caption(f"Target: {_cg_word_range[0]}-{_cg_word_range[1]} words")
            
            # Audience Context
            cc3, cc4 = st.columns(2)
            with cc3:
                sender = st.text_input("VOICE / SENDER", placeholder="e.g. CEO", max_chars=100)
            with cc4:
                audience = st.text_input("TARGET AUDIENCE", placeholder="e.g. Public, Shareholders", max_chars=100)

            # Key Points
            st.markdown("##### 2. MESSAGE DISCIPLINE")
            # Using key= automatically binds to st.session_state['cg_key_points']
            st.text_area(
                "KEY MESSAGES (BULLET POINTS)", 
                height=150, 
                placeholder="- Revenue up 20%\n- New product launch in Q4\n- Focus on sustainability",
                help="The AI will strictly adhere to these facts.",
                key="cg_key_points",
                max_chars=2000
            )

        with c2:
            # --- DYNAMIC CALIBRATION METER ---
            profile_data = st.session_state['profiles'][active_profile]
            metrics = calculate_content_confidence(profile_data, content_type)
            
            st.markdown(f"""<div class="dashboard-card" style="padding: 15px; margin-top: 28px;">
                <div style="font-size:0.7rem; color:#5c6b61; font-weight:700;">TASK CONFIDENCE: {content_type.upper()}</div>
                <div style="font-size:1.6rem; font-weight:800; color:{metrics['color']}; margin-top:5px;">{metrics['score']}%</div>
                <div class="calibration-bar">
                    <div style="width:{metrics['score']}%; height:100%; background-color:{metrics['color']};"></div>
                </div>
                <div style="font-size:0.8rem; color:#f5f5f0; font-weight:700; margin-top:5px;">{metrics['label']}</div>
                <div style="font-size:0.7rem; color:#a0a0a0; margin-top:8px; line-height:1.2;"><em>{metrics['rationale']}</em></div>
            </div>""", unsafe_allow_html=True)
            
            # Dynamic Warning / Call to Action
            if metrics['action']:
                st.markdown(f"""
                    <div style="border-left: 2px solid {metrics['color']}; padding-left: 10px; margin-top: 10px; font-size: 0.8rem; color: #a0a0a0;">
                        <strong>Optimization Tip:</strong><br>
                        {metrics['action']}
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)

            _show_suspension_notice()
            if st.button("GENERATE DRAFT", type="primary", use_container_width=True,
                         disabled=not (_is_super_admin() or _subscription_active()) or _is_suspended()):
                # Access via state keys
                if st.session_state['cg_topic'] and st.session_state['cg_key_points']:
                    with st.spinner("ARCHITECTING CONTENT..."):
                        
                        # --- BRAND CONTEXT (via shared builder) ---
                        _cg_cluster = _cg_active_cluster
                        prof_text = build_brand_context(
                            profile_data,
                            include_voice_samples=True,
                            cluster_filter=_cg_cluster,
                        )

                        # Cluster override note for prompt
                        _cg_default_cluster = CONTENT_TYPES.get(_cg_type_key, {}).get("cluster")
                        _cg_override_note = ""
                        if _cg_cluster and _cg_default_cluster and _cg_cluster != _cg_default_cluster:
                            _cg_override_note = f"\nNote: The user has overridden the default voice cluster. Default for {content_type} is {_cg_default_cluster}, but the user selected {_cg_cluster}. Use voice samples from the {_cg_cluster} cluster.\n"

                        # Build content type context for the prompt
                        _cg_type_desc = content_type
                        if _cg_type_key == "custom" and _cg_custom_desc:
                            _cg_type_desc = f"Custom — {_cg_custom_desc}"

                        # Engineered Prompt (Constraint-Based)
                        prompt_wrapper = f"""
                        CONTEXT:
                        - Type: {_cg_type_desc}
                        - Communication Style: {_cg_cluster or 'General'}{_cg_override_note}
                        - Target Length: {_cg_word_range[0]}-{_cg_word_range[1]} words
                        - Sender: {sender}
                        - Audience: {audience}

                        CORE TASK: Write a {_cg_type_desc} about "{st.session_state['cg_topic']}".

                        TARGET LENGTH: {_cg_word_range[0]}-{_cg_word_range[1]} words.
                        This is a hard constraint. The output must fall within this range.
                        If the content naturally requires more or fewer words, err toward the middle of the range.

                        STRICT CONSTRAINTS:
                        1. You must cover these KEY POINTS:
                        --- BEGIN POINTS ---
                        {st.session_state['cg_key_points']}
                        --- END POINTS ---
                        2. Do NOT invent facts outside these points.
                        3. Use the Brand Voice defined below.
                        4. Adhere to all CRITICAL GUARDRAILS.

                        STEP 1: STRATEGY
                        Briefly outline the tone and structure you will use to meet the audience's needs.

                        STEP 2: DRAFT
                        Write the content.

                        OUTPUT FORMAT:
                        STRATEGY:
                        [Reasoning]
                        DRAFT:
                        [Content]
                        """
                        
                        try:
                            # Use content generator logic
                            full_response = logic_engine.run_content_generator(
                                st.session_state['cg_topic'], 
                                content_type, 
                                st.session_state['cg_key_points'], 
                                prof_text
                            )
                            
                            # Heuristic Parsing
                            if "DRAFT:" in full_response:
                                parts = full_response.split("DRAFT:")
                                rationale = parts[0].replace("STRATEGY:", "").strip()
                                draft = parts[1].strip()
                            else:
                                rationale = "Generated based on key points."
                                draft = full_response
                            
                            # Update State
                            st.session_state['cg_result'] = draft
                            st.session_state['cg_rationale'] = rationale
                            
                            # LOGGING TO DB (GOD MODE)
                            # Records: Type, Topic, Draft, and Confidence Score
                            db.log_event(
                                org_id=st.session_state.get('org_id', 'Unknown'),
                                username=st.session_state.get('username', 'Unknown'),
                                activity_type="GENERATOR",
                                asset_name=f"{content_type}: {st.session_state['cg_topic']}",
                                score=metrics['score'],
                                verdict="CREATED",
                                metadata={
                                    "topic": st.session_state['cg_topic'],
                                    "key_points": st.session_state['cg_key_points'],
                                    "draft": draft,
                                    "rationale": rationale
                                }
                            )
                            _cg_detail = f"Generate: {st.session_state['cg_topic'][:60]}"
                            sub_manager.record_ai_action(st.session_state.get('user_id', ''), 'content_generator', _cg_detail)
                            st.session_state['usage'] = sub_manager.check_usage_limit(st.session_state.get('user_id', ''))
                            st.session_state['_action_id_content_generator'] = str(uuid.uuid4())[:8]
                            _track_module_and_cost("content_generator", {
                                "content_type": content_type,
                                "input_length": len(st.session_state.get('cg_topic', '') + st.session_state.get('cg_key_points', '')),
                            })
                            st.rerun()

                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("Topic and Key Points are required.")

        # --- 3. OUTPUT DISPLAY ---
        if st.session_state['cg_result']:
            st.divider()
            
            if st.session_state['cg_rationale']:
                _cg_rat_escaped = html.escape(st.session_state['cg_rationale']).replace('\n', '<br>')
                st.markdown(f"""
                    <div class="rationale-box">
                        <strong>GENERATION STRATEGY:</strong><br>
                        {_cg_rat_escaped}
                    </div>
                """, unsafe_allow_html=True)
            
            st.subheader("FINAL DRAFT")
            st.text_area("Copy to Clipboard", value=st.session_state['cg_result'], height=500)

            render_feedback("content_generator", "_action_id_content_generator")

# 5. SOCIAL MEDIA ASSISTANT (Platform-Aware, Goal-Oriented, Trend-Aware)
elif app_mode == "SOCIAL MEDIA ASSISTANT":
    st.title("SOCIAL MEDIA ASSISTANT")
    brand_ui.render_module_help("social_assistant")

    # Trial gate: must use sample brand
    if _is_trial_user() and not _is_sample_brand_active():
        _show_trial_gate()

    # --- CSS INJECTION ---
    st.markdown("""
        <style>
        div.stButton > button[kind="primary"] {
            background-color: #ab8f59 !important;
            color: #1b2a2e !important;
            -webkit-text-fill-color: #1b2a2e !important;
            border: none !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
        }
        div.stButton > button[kind="primary"] p {
            color: #1b2a2e !important;
            -webkit-text-fill-color: #1b2a2e !important;
        }
        .calibration-bar {
            width: 100%;
            height: 8px;
            background-color: #3d3d3d;
            border-radius: 4px;
            margin-top: 5px;
            margin-bottom: 5px;
            overflow: hidden;
        }
        .sm-strategy-box {
            background-color: rgba(171, 143, 89, 0.1);
            border-left: 3px solid #ab8f59;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 0.9rem;
            color: #e0e0e0;
            line-height: 1.6;
        }
        .sm-strategy-box strong { color: #ab8f59; }
        .sm-post-card {
            background-color: #1b2a2e;
            border: 1px solid #3d4f4a;
            border-radius: 6px;
            padding: 18px;
            margin-bottom: 12px;
            font-size: 0.9rem;
            color: #f5f5f0;
            line-height: 1.7;
            white-space: pre-wrap;
        }
        .sm-hashtag-box {
            background-color: rgba(9, 171, 59, 0.08);
            border-left: 3px solid #09ab3b;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 0.9rem;
            color: #e0e0e0;
            line-height: 1.6;
        }
        .sm-hashtag-box strong { color: #09ab3b; }
        .sm-alignment-box {
            background-color: rgba(92, 107, 97, 0.15);
            border-left: 3px solid #5c6b61;
            padding: 15px;
            margin-bottom: 20px;
            font-size: 0.9rem;
            color: #e0e0e0;
            line-height: 1.6;
        }
        .sm-alignment-box strong { color: #a0b5a8; }
        </style>
    """, unsafe_allow_html=True)

    # --- SUBSCRIPTION GATE ---
    if not _is_super_admin() and not _subscription_active():
        show_paywall()

    # --- HELPER: RESEARCH-BASED FEW-SHOT CONFIDENCE ---
    def calculate_social_confidence(profile_data, target_platform):
        """
        Calculates confidence based on LMM Few-Shot Learning research.
        """
        inputs = profile_data.get('inputs', {})
        social_dna = inputs.get('social_dna', '')
        
        # 1. Count Specific Assets (The "N-Shot" Count)
        if target_platform:
            clean_plat = target_platform.upper().split(" ")[0] 
            asset_count = social_dna.upper().count(f"ASSET: {clean_plat}")
        else:
            asset_count = 0
        
        # 2. Determine Score & Rationale
        if asset_count >= 3:
            score = 85
            color = "#09ab3b" # Green
            label = "HIGH CONFIDENCE"
            rationale = f"Pattern Stability Achieved. {asset_count} {target_platform} assets found (Few-Shot threshold met)."
            action = ""
            
        elif asset_count >= 1:
            score = 55
            color = "#ffa421" # Orange
            label = "CALIBRATING"
            rationale = f"Pattern Unstable. Only {asset_count} {target_platform} asset found. AI may overfit to this single example."
            action = f"Upload {3 - asset_count} more {target_platform} screenshots to reach pattern stability."
            
        else:
            score = 25
            color = "#ff4b4b" # Red
            label = "LOW DATA"
            rationale = f"Zero-Shot Mode. No {target_platform} data found. Relying on generic best practices."
            action = f"Upload at least 3 {target_platform} screenshots to train the engine."

        return {
            "score": score,
            "color": color,
            "label": label,
            "rationale": rationale,
            "action": action
        }

    if not active_profile:
        st.warning("NO PROFILE SELECTED. Please choose a Brand Profile from the sidebar.")
    else:
        # --- STATE INITIALIZATION (GLOBAL PERSISTENCE) ---
        if 'sm_topic' not in st.session_state: st.session_state['sm_topic'] = ""
        if 'sm_platform' not in st.session_state: st.session_state['sm_platform'] = "LinkedIn"
        if 'sm_length' not in st.session_state: st.session_state['sm_length'] = "standard"
        if 'sm_goal' not in st.session_state: st.session_state['sm_goal'] = "Reach (Awareness)"
        if 'sm_results' not in st.session_state: st.session_state['sm_results'] = None
        if 'sm_strategy_brief' not in st.session_state: st.session_state['sm_strategy_brief'] = None
        if 'sm_hashtags' not in st.session_state: st.session_state['sm_hashtags'] = None
        if 'sm_alignment' not in st.session_state: st.session_state['sm_alignment'] = None
        
        # --- INPUTS & CALIBRATION ---
        c1, c2 = st.columns([2, 1])
        
        with c1:
            st.markdown("##### 1. PLATFORM STRATEGY")
            cc1, cc2 = st.columns(2)
            with cc1:
                # Trigger Calibration (Persisted via key)
                st.selectbox(
                    "NETWORK",
                    ["LinkedIn", "X (Twitter)", "Instagram"],
                    key="sm_platform"
                )
            with cc2:
                st.selectbox(
                    "OBJECTIVE",
                    ["Reach (Awareness)", "Engagement (Comments)", "Conversion (Clicks)"],
                    key="sm_goal"
                )

            # --- Target Length Slider (platform-aware) ---
            _sm_plat_key = get_social_platform_key(st.session_state['sm_platform'])
            _sm_length_options = ["brief", "standard", "detailed"]
            _sm_length_labels = [get_social_length_label(_sm_plat_key, l) for l in _sm_length_options]
            _sm_cur_idx = _sm_length_options.index(st.session_state.get('sm_length', 'standard'))
            _sm_selected_label = st.select_slider(
                "TARGET LENGTH",
                options=_sm_length_labels,
                value=_sm_length_labels[_sm_cur_idx],
                key="sm_length_slider"
            )
            st.session_state['sm_length'] = _sm_length_options[_sm_length_labels.index(_sm_selected_label)]

            # Platform notes
            _sm_plat_conf = SOCIAL_PLATFORMS.get(_sm_plat_key, SOCIAL_PLATFORMS["linkedin"])
            if _sm_plat_conf.get("notes"):
                st.caption(f"_{_sm_plat_conf['notes']}_")

            # --- Cluster visibility & override (default: Brand Marketing) ---
            _sm_default_cluster = "Brand Marketing"
            _sm_ov_c1, _sm_ov_c2 = st.columns([3, 1])
            with _sm_ov_c1:
                st.caption(f"VOICE CLUSTER: {_sm_default_cluster.upper()}")
            with _sm_ov_c2:
                _sm_cluster_override = st.checkbox("Override", key="sm_cluster_override")

            if _sm_cluster_override:
                _sm_cluster_options = list(CLUSTER_DISPLAY_NAMES.values())
                _sm_selected_cluster = st.selectbox(
                    "SELECT VOICE CLUSTER",
                    _sm_cluster_options,
                    index=_sm_cluster_options.index(_sm_default_cluster),
                    key="sm_cluster_override_select"
                )
                _sm_active_cluster = _sm_selected_cluster
            else:
                _sm_active_cluster = _sm_default_cluster

            st.markdown("##### 2. CONTENT CONTEXT")
            # Text Input (Persisted via key)
            st.text_input(
                "TOPIC / HOOK", 
                placeholder="e.g. Launching our new sustainability initiative",
                key="sm_topic",
                max_chars=200
            )
            
            # Image Uploader (Crucial for Visual Platforms)
            uploaded_image = st.file_uploader("ATTACH VISUAL (Optional but Recommended)", type=['png', 'jpg', 'jpeg'])
            
        with c2:
            # --- DYNAMIC CALIBRATION METER ---
            profile_data = st.session_state['profiles'][active_profile]
            # Calculate off the persisted state value
            metrics = calculate_social_confidence(profile_data, st.session_state['sm_platform'])
            
            st.markdown(f"""<div class="dashboard-card" style="padding: 15px; margin-top: 28px;">
                <div style="font-size:0.7rem; color:#5c6b61; font-weight:700;">DIALECT CONFIDENCE: {st.session_state['sm_platform'].upper()}</div>
                <div style="font-size:1.6rem; font-weight:800; color:{metrics['color']}; margin-top:5px;">{metrics['score']}%</div>
                <div class="calibration-bar">
                    <div style="width:{metrics['score']}%; height:100%; background-color:{metrics['color']};"></div>
                </div>
                <div style="font-size:0.8rem; color:#f5f5f0; font-weight:700; margin-top:5px;">{metrics['label']}</div>
                <div style="font-size:0.7rem; color:#a0a0a0; margin-top:8px; line-height:1.2;"><em>{metrics['rationale']}</em></div>
            </div>""", unsafe_allow_html=True)
            
            # Warning Logic
            if metrics['action']:
                st.markdown(f"""
                    <div style="border-left: 2px solid {metrics['color']}; padding-left: 10px; margin-top: 10px; font-size: 0.8rem; color: #a0a0a0;">
                        <strong>Optimization Tip:</strong><br>
                        {metrics['action']}
                    </div>
                """, unsafe_allow_html=True)
                if st.button("GO TO CALIBRATION LAB", type="secondary"):
                    st.session_state['app_mode'] = "BRAND MANAGER"
                    st.rerun()

            st.markdown("<br>", unsafe_allow_html=True)

            _show_suspension_notice()
            if st.button("GENERATE OPTIONS", type="primary", use_container_width=True,
                         disabled=not (_is_super_admin() or _subscription_active()) or _is_suspended()):
                # Check using session state
                if st.session_state['sm_topic']:
                    with st.spinner("SCANNING TRENDS & DRAFTING..."):

                        # --- BRAND CONTEXT (via shared builder) ---
                        if _sm_active_cluster != _sm_default_cluster:
                            # User overrode cluster — use build_brand_context with cluster filter
                            prof_text = build_brand_context(
                                profile_data,
                                include_voice_samples=True,
                                cluster_filter=_sm_active_cluster,
                            )
                        else:
                            prof_text = build_social_context(profile_data)

                        # Image Analysis (if present)
                        image_desc = ""
                        if uploaded_image:
                            img = Image.open(uploaded_image)
                            image_desc = logic_engine.analyze_social_post(img)

                        # Engineered Prompt (Trend-Aware, Transparent, Structured)
                        image_line = f"\nIMAGE CONTEXT: {image_desc}" if image_desc else ""
                        _sm_word_range = SOCIAL_PLATFORMS.get(_sm_plat_key, SOCIAL_PLATFORMS["linkedin"])["lengths"].get(st.session_state['sm_length'], (100, 200))
                        _sm_cluster_note = ""
                        if _sm_active_cluster != _sm_default_cluster:
                            _sm_cluster_note = f"\nVOICE CLUSTER OVERRIDE: The user has selected the {_sm_active_cluster} cluster instead of the default Brand Marketing. Match the tone and style of {_sm_active_cluster} voice samples.\n"
                        prompt = (
                            f"ROLE: Expert Social Media Manager for the brand defined in <brand_profile>.\n"
                            f"PLATFORM: {st.session_state['sm_platform']} (Adhere strictly to character limits and cultural norms).\n"
                            f"TARGET LENGTH: Each post option should be approximately {_sm_word_range[0]}-{_sm_word_range[1]} words.\n"
                            f"{_sm_cluster_note}"
                            f"GOAL: {st.session_state['sm_goal']}\n"
                            f"TOPIC: \"\"\"{st.session_state['sm_topic']}\"\"\""
                            f"{image_line}\n\n"

                            "STEP 0: TREND RESEARCH (CRITICAL)\n"
                            f"Use web search to identify 3 currently trending hashtags or conversation topics "
                            f"related to '{st.session_state['sm_topic']}' on {st.session_state['sm_platform']}. "
                            "Note what you find — you will reference these in your strategy and posts.\n\n"

                            "STEP 1: STRATEGY BRIEF\n"
                            "Before writing any posts, explain your approach:\n"
                            "- Which brand elements you are applying (pillars, guardrails, voice attributes, message house themes)\n"
                            f"- Platform best practices for {st.session_state['sm_platform']} that inform your choices\n"
                            f"- How you are optimizing for the goal: {st.session_state['sm_goal']}\n"
                            "- Which trending topics/hashtags you found and how you plan to integrate them\n\n"

                            "STEP 2: GENERATE 3 POST OPTIONS\n\n"

                            "OPTION 1: THE STORYTELLER\n"
                            "- Focus: Narrative, emotive, connects topic to brand values.\n"
                            "- Structure: Long-form (if platform allows), spacing for readability.\n\n"

                            "OPTION 2: THE PROVOCATEUR\n"
                            "- Focus: Pattern interrupt, hot take, or question.\n"
                            "- Structure: Short, punchy, designed to stop the scroll.\n\n"

                            "OPTION 3: THE VALUE-ADD\n"
                            "- Focus: Educational, utility, 'Save this post'.\n"
                            "- Structure: Bullet points or actionable advice.\n\n"

                            "STEP 3: HASHTAG STRATEGY\n"
                            "Recommend hashtags for each post option, explaining why each is effective "
                            "(trending, niche reach, brand alignment, etc.).\n\n"

                            "STEP 4: MESSAGE HOUSE ALIGNMENT\n"
                            "Briefly note which message house pillars and proof points each option leverages. "
                            "Flag any guardrail considerations.\n\n"

                            "OUTPUT FORMAT (use these exact section headers):\n"
                            "STRATEGY:\n[your strategy brief]\n\n"
                            "OPTION 1:\n[storyteller post]\n\n"
                            "OPTION 2:\n[provocateur post]\n\n"
                            "OPTION 3:\n[value-add post]\n\n"
                            "HASHTAGS:\n[hashtag strategy]\n\n"
                            "ALIGNMENT:\n[message house alignment notes]"
                        )

                        try:
                            response = logic_engine.run_social_generator(
                                st.session_state['sm_platform'],
                                st.session_state['sm_goal'],
                                prompt,
                                prof_text
                            )

                            # --- Parse structured response ---
                            _raw = response

                            # Extract sections by splitting on headers
                            def _extract_section(text, header, next_headers):
                                start = text.find(header)
                                if start == -1:
                                    return ""
                                start += len(header)
                                end = len(text)
                                for nh in next_headers:
                                    pos = text.find(nh, start)
                                    if pos != -1 and pos < end:
                                        end = pos
                                return text[start:end].strip()

                            headers_order = ["STRATEGY:", "OPTION 1:", "OPTION 2:", "OPTION 3:", "HASHTAGS:", "ALIGNMENT:"]

                            strategy_text = _extract_section(_raw, "STRATEGY:", headers_order[1:])
                            opt1 = _extract_section(_raw, "OPTION 1:", headers_order[2:])
                            opt2 = _extract_section(_raw, "OPTION 2:", headers_order[3:])
                            opt3 = _extract_section(_raw, "OPTION 3:", headers_order[4:])
                            hashtags_text = _extract_section(_raw, "HASHTAGS:", headers_order[5:])
                            alignment_text = _extract_section(_raw, "ALIGNMENT:", [])

                            # Fallback: if parsing fails, dump raw into option 1
                            if not opt1 and not opt2 and not opt3:
                                opt1 = _raw
                                opt2 = ""
                                opt3 = ""

                            st.session_state['sm_results'] = [opt1, opt2, opt3]
                            st.session_state['sm_strategy_brief'] = strategy_text if strategy_text else None
                            st.session_state['sm_hashtags'] = hashtags_text if hashtags_text else None
                            st.session_state['sm_alignment'] = alignment_text if alignment_text else None

                            # LOG TO DB
                            db.log_event(
                                org_id=st.session_state.get('org_id', 'Unknown'),
                                username=st.session_state.get('username', 'Unknown'),
                                activity_type="SOCIAL GEN",
                                asset_name=f"{st.session_state['sm_platform']}: {st.session_state['sm_topic']}",
                                score=metrics['score'],
                                verdict="CREATED",
                                metadata={
                                    "platform": st.session_state['sm_platform'],
                                    "goal": st.session_state['sm_goal'],
                                    "topic": st.session_state['sm_topic'],
                                    "strategy_brief": strategy_text[:200] if strategy_text else "",
                                    "hashtags": hashtags_text[:200] if hashtags_text else "",
                                    "alignment": alignment_text[:200] if alignment_text else "",
                                    "options_count": sum(1 for o in [opt1, opt2, opt3] if o)
                                }
                            )
                            _sm_detail = f"Social: {st.session_state['sm_platform']} — {st.session_state['sm_topic'][:50]}"
                            sub_manager.record_ai_action(st.session_state.get('user_id', ''), 'social_assistant', _sm_detail)
                            st.session_state['usage'] = sub_manager.check_usage_limit(st.session_state.get('user_id', ''))
                            st.session_state['_action_id_social_assistant'] = str(uuid.uuid4())[:8]
                            _track_module_and_cost("social_assistant", {
                                "platform": st.session_state.get('sm_platform', ''),
                                "has_visual": False,
                            })
                            st.rerun()

                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("Please enter a topic.")

        # --- OUTPUT DISPLAY ---
        if st.session_state['sm_results']:
            import html as html_mod
            st.divider()

            # Strategy Brief
            if st.session_state.get('sm_strategy_brief'):
                st.markdown("##### STRATEGY BRIEF")
                _strat_escaped = html_mod.escape(st.session_state['sm_strategy_brief'])
                st.markdown(f"""<div class="sm-strategy-box">
                    <strong>GENERATION STRATEGY:</strong><br><br>
                    {_strat_escaped.replace(chr(10), '<br>')}
                </div>""", unsafe_allow_html=True)

            # Post Options (Tabs)
            st.markdown("##### CAMPAIGN OPTIONS")
            t1, t2, t3 = st.tabs(["THE STORYTELLER", "THE PROVOCATEUR", "THE VALUE-ADD"])

            _options = st.session_state['sm_results']
            _tab_labels = [
                ("Narrative Focus", "Emotive storytelling that connects your topic to brand values."),
                ("Engagement Focus", "Pattern-interrupt designed to stop the scroll."),
                ("Utility Focus", "Educational content that delivers actionable value.")
            ]

            for tab, (opt, (label, desc)) in zip([t1, t2, t3], zip(_options, _tab_labels)):
                with tab:
                    _opt_text = opt.strip() if opt else ""
                    if _opt_text:
                        _opt_escaped = html_mod.escape(_opt_text)
                        st.markdown(f"""<div class="sm-post-card">{_opt_escaped.replace(chr(10), '<br>')}</div>""", unsafe_allow_html=True)
                        with st.expander("COPY TO CLIPBOARD"):
                            st.text_area(label, value=_opt_text, height=300, label_visibility="collapsed")
                    else:
                        st.info("This option was not generated.")

            # Hashtag Strategy
            if st.session_state.get('sm_hashtags'):
                st.markdown("##### HASHTAG STRATEGY")
                _hash_escaped = html_mod.escape(st.session_state['sm_hashtags'])
                st.markdown(f"""<div class="sm-hashtag-box">
                    <strong>RECOMMENDED HASHTAGS:</strong><br><br>
                    {_hash_escaped.replace(chr(10), '<br>')}
                </div>""", unsafe_allow_html=True)

            # Message House Alignment
            if st.session_state.get('sm_alignment'):
                st.markdown("##### MESSAGE HOUSE ALIGNMENT")
                _align_escaped = html_mod.escape(st.session_state['sm_alignment'])
                st.markdown(f"""<div class="sm-alignment-box">
                    <strong>BRAND ALIGNMENT NOTES:</strong><br><br>
                    {_align_escaped.replace(chr(10), '<br>')}
                </div>""", unsafe_allow_html=True)

            render_feedback("social_assistant", "_action_id_social_assistant")

# ===================================================================
# 6. BRAND ARCHITECT (UNIFIED MODULE)
# Replaces "BRAND ARCHITECT" and "BRAND MANAGER"
# ===================================================================
elif app_mode == "BRAND ARCHITECT":
    st.title("BRAND ARCHITECT")

    # Trial users: read-only notice
    _ba_trial_readonly = _is_trial_user()
    if _ba_trial_readonly:
        st.markdown("""
            <div style="background:rgba(171,143,89,0.08); border-left:3px solid #ab8f59;
                        padding:12px 16px; margin-bottom:16px; border-radius:2px;">
                <span style="font-weight:700; color:#24363b; font-size:0.9rem;">Trial Mode — Read Only</span>
                <span style="color:#3d3d3d; font-size:0.85rem; margin-left:8px;">
                    You can explore the sample brand profile. Subscribe to create and edit your own brands.
                </span>
            </div>
        """, unsafe_allow_html=True)

    # --- CSS INJECTION ---
    st.markdown("""
        <style>
        div.stButton > button[kind="primary"] {
            background-color: #ab8f59 !important;
            color: #1b2a2e !important;
            -webkit-text-fill-color: #1b2a2e !important;
            border: none !important;
            font-weight: 800 !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #f0c05a !important;
            color: #1b2a2e !important;
            -webkit-text-fill-color: #1b2a2e !important;
        }
        div.stButton > button[kind="primary"] p {
            color: #1b2a2e !important;
            -webkit-text-fill-color: #1b2a2e !important;
        }
        .asset-box {
            border: 1px solid #333;
            background-color: #1E1E1E;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 4px;
        }
        .asset-header {
            font-weight: bold;
            color: #ab8f59;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- HELPER FUNCTIONS ---
    def process_image_for_storage(file_buffer):
        """Resizes image and converts to base64 for storage."""
        try:
            import base64
            from io import BytesIO
            
            # Reset buffer pointer
            file_buffer.seek(0)
            img = Image.open(file_buffer)
            
            # Resize for thumbnail (Max 400px width)
            base_width = 400
            w_percent = (base_width / float(img.size[0]))
            h_size = int((float(img.size[1]) * float(w_percent)))
            img = img.resize((base_width, h_size), Image.Resampling.LANCZOS)
            
            # Convert to Base64
            buffered = BytesIO()
            img.save(buffered, format="PNG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            return f"data:image/png;base64,{img_str}"
        except Exception:
            return None

    def parse_assets_from_text(text_blob):
        """Splits the sample text block into manageable assets based on headers."""
        if not text_blob: return []
        # Split by the divider line we used
        raw_assets = text_blob.split("----------------\n")
        parsed = []
        for asset in raw_assets:
            if "[ASSET:" in asset:
                lines = asset.strip().split('\n')
                header = lines[0] # [ASSET: TYPE - NAME]
                
                # Extract Visual Data if present
                img_data = None
                clean_lines = []
                for line in lines[1:]:
                    if line.startswith("[VISUAL_REF:"):
                        img_data = line.replace("[VISUAL_REF:", "").replace("]", "").strip()
                    else:
                        clean_lines.append(line)
                
                content = "\n".join(clean_lines)
                parsed.append({
                    "header": header, 
                    "content": content, 
                    "full_text": asset + "----------------\n",
                    "image": img_data
                })
        return parsed

    def update_calibration_score(profile_obj):
        """Recalculates the profile completeness score based on inputs."""
        inputs = profile_obj.get('inputs', {})
        score = 0
        
        # 1. Basics (40%) - The Strategy Layer
        if inputs.get('wiz_name'): score += 10
        if inputs.get('wiz_mission'): score += 10
        if inputs.get('wiz_values'): score += 10
        if inputs.get('wiz_archetype'): score += 10
        
        # 2. Sample Layers (60%) - The Asset Layer
        has_social = len(inputs.get('social_dna', '')) > 20 or "[ASSET:" in inputs.get('social_dna', '')
        has_voice = len(inputs.get('voice_dna', '')) > 20 or "[ASSET:" in inputs.get('voice_dna', '')
        has_visual = len(inputs.get('visual_dna', '')) > 20 or "[ASSET:" in inputs.get('visual_dna', '')

        if has_social: score += 20
        if has_voice: score += 20
        if has_visual: score += 20
        
        profile_obj['calibration_score'] = min(score, 100)
        return profile_obj
        
    def extract_and_map_pdf():
        # This runs BEFORE the page redraws
        uploaded_file = st.session_state.get('arch_pdf_uploader')
        if uploaded_file:
            try:
                # USE logic_engine (The Class Instance)
                raw_text = logic_engine.extract_text_from_pdf(uploaded_file)
                data = logic_engine.generate_brand_rules_from_pdf(raw_text)
                
                # Update Session State safely
                st.session_state['wiz_name'] = data.get('wiz_name', '')
                st.session_state['wiz_mission'] = data.get('wiz_mission', '')
                
                # --- HEX CODE EXTRACTION (OVERWRITE MODE) ---
                # 1. Clear Defaults
                st.session_state['palette_primary'] = []
                st.session_state['palette_secondary'] = []
                st.session_state['palette_accent'] = [] 

                # 2. Map Primary
                if 'palette_primary' in data and isinstance(data['palette_primary'], list):
                    valid_hex = [c for c in data['palette_primary'] if isinstance(c, str) and c.startswith('#')]
                    st.session_state['palette_primary'] = valid_hex[:5]
                
                # Fallback to black if empty
                if not st.session_state['palette_primary']:
                    st.session_state['palette_primary'] = ["#000000"]

                # 3. Map Secondary
                if 'palette_secondary' in data and isinstance(data['palette_secondary'], list):
                    valid_hex = [c for c in data['palette_secondary'] if isinstance(c, str) and c.startswith('#')]
                    st.session_state['palette_secondary'] = valid_hex[:5]
                # -------------------------------
                
                # Sanitize List Fields
                raw_tone = data.get('wiz_tone', '')
                if isinstance(raw_tone, list):
                    st.session_state['wiz_tone'] = ", ".join([str(t) for t in raw_tone])
                else:
                    st.session_state['wiz_tone'] = str(raw_tone) if raw_tone else ""

                raw_values = data.get('wiz_values', '')
                if isinstance(raw_values, list):
                    st.session_state['wiz_values'] = ", ".join([str(v) for v in raw_values])
                else:
                    st.session_state['wiz_values'] = str(raw_values) if raw_values else ""

                raw_guard = data.get('wiz_guardrails', '')
                if isinstance(raw_guard, list):
                    st.session_state['wiz_guardrails'] = "\n".join([str(g) for g in raw_guard])
                else:
                    st.session_state['wiz_guardrails'] = str(raw_guard) if raw_guard else ""

                # Match Archetype
                suggested_arch = data.get('wiz_archetype')
                if suggested_arch in ARCHETYPES:
                    st.session_state['wiz_archetype'] = suggested_arch
                
                st.session_state['extraction_success'] = True
                
            except Exception as e:
                st.session_state['extraction_error'] = str(e)

    # --- MAIN INTERFACE: TABS ---
    main_tab1, main_tab2, main_tab3 = st.tabs(["BUILD NEW BRAND", "MANAGE BRAND", "IMPORT BRAND FROM PDF"])

# -----------------------------------------------------------
    # TAB 1: BUILD NEW BRAND (FORMERLY WIZARD)
    # -----------------------------------------------------------
    with main_tab1:
        if _ba_trial_readonly:
            st.info("Subscribe to create your own brands. During your trial, explore the Meridian Labs sample brand in the Manage Brand tab.")
        st.markdown("### ARCHITECT NEW BRAND")
        st.caption("Build a new brand profile from scratch.")
        
        with st.expander("1. STRATEGY (CORE)", expanded=True):
            st.text_input("BRAND NAME", key="wiz_name", max_chars=100)
            c1, c2 = st.columns(2)
            def format_archetype(option):
                if option in ARCHETYPE_INFO:
                    return f"{option} | {ARCHETYPE_INFO[option]['tagline']}"
                return option

            with c1: 
                selected_arch = st.selectbox(
                    "ARCHETYPE *", 
                    options=ARCHETYPES, 
                    index=None, 
                    placeholder="SELECT...", 
                    key="wiz_archetype",
                    format_func=format_archetype
                )
            if selected_arch:
                info = ARCHETYPE_INFO[selected_arch]
                st.markdown(f"""
                    <div style="background-color: rgba(36, 54, 59, 0.05); border-left: 3px solid #ab8f59; padding: 15px; margin-top: 10px; margin-bottom: 20px; border-radius: 0 4px 4px 0;">
                        <strong style="color: #24363b; display: block; margin-bottom: 4px;">THE AESTHETIC:</strong>
                        <span style="color: #5c6b61; font-size: 0.9rem;">{info['desc']}</span>
                        <div style="margin-top: 8px; font-size: 0.8rem; color: #888;">
                            <em>Real World Examples: {info['examples']}</em>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            with c2: st.text_input("TONE KEYWORDS", placeholder="e.g. Witty, Professional, Bold", key="wiz_tone", max_chars=100)
            st.text_area("MISSION STATEMENT", key="wiz_mission", max_chars=2000)
            st.text_area("CORE VALUES", placeholder="e.g. Transparency, Innovation, Community", key="wiz_values", max_chars=2000)
            st.text_area("BRAND GUARDRAILS (DO'S & DON'TS)", placeholder="e.g. Don't use emojis.", key="wiz_guardrails", max_chars=2000)

        with st.expander("MESSAGE HOUSE"):
            st.caption("The controlling document for all communications. Every asset Signet evaluates or generates is measured against the messaging defined here.")

            # --- BRAND PROMISE ---
            st.markdown('<span style="color:#ab8f59; font-weight:700; font-size:0.8rem; letter-spacing:0.05em;">BRAND PROMISE</span>', unsafe_allow_html=True)
            st.caption("One sentence. What your company ultimately delivers. Not a feature — a transformation.")
            bp_val = st.text_area("BRAND PROMISE", key="mh_brand_promise", height=80, max_chars=500,
                label_visibility="collapsed",
                placeholder="e.g. We build the infrastructure that makes your company legible, credible, and trusted before the moment it needs to be.")
            if bp_val and bp_val.count('.') > 2:
                st.warning("Brand promise should be 1-2 sentences for maximum impact.")

            st.markdown("---")

            # --- MESSAGE PILLARS ---
            st.markdown('<span style="color:#ab8f59; font-weight:700; font-size:0.8rem; letter-spacing:0.05em;">MESSAGE PILLARS</span>', unsafe_allow_html=True)
            st.caption("Exactly 3 pillars. Each is a full, defensible argument supporting the brand promise.")

            raw_pillars_json = st.session_state.get('mh_pillars_json', '')
            try:
                pillars_data = json.loads(raw_pillars_json) if raw_pillars_json else [{}, {}, {}]
                if len(pillars_data) < 3:
                    pillars_data += [{} for _ in range(3 - len(pillars_data))]
            except (json.JSONDecodeError, TypeError):
                pillars_data = [{}, {}, {}]

            updated_pillars = []
            for pi in range(3):
                p = pillars_data[pi] if pi < len(pillars_data) else {}
                pillar_label = p.get('name', '') or f"Click to expand Pillar {pi + 1}"
                with st.expander(f"PILLAR {pi + 1}: {pillar_label}"):
                    p_name = st.text_input("PILLAR NAME", value=p.get('name', ''), key=f"mh_pillar_{pi}_name", max_chars=100, placeholder="e.g. The Story Is the Foundation")
                    p_tagline = st.text_input("TAGLINE", value=p.get('tagline', ''), key=f"mh_pillar_{pi}_tagline", max_chars=150,
                        placeholder="e.g. Before anything goes out, we build what everything else draws from.", help="The sub-message — what this pillar argues in one sentence.")
                    p_headline = st.text_area("HEADLINE CLAIM", value=p.get('headline_claim', ''), key=f"mh_pillar_{pi}_headline", max_chars=500, height=80,
                        placeholder="e.g. The credibility gap doesn't usually open at launch. It opens six months later...", help="1-2 sentences. The core argument of this pillar.")
                    st.markdown('<span style="color:#ab8f59; font-weight:600; font-size:0.75rem;">PROOF POINTS</span>', unsafe_allow_html=True)
                    pp1 = st.text_input("Proof Point 1", value=p.get('proof_1', ''), key=f"mh_pillar_{pi}_pp1", max_chars=200, placeholder="e.g. Stat, story, or credential that supports this pillar")
                    pp2 = st.text_input("Proof Point 2", value=p.get('proof_2', ''), key=f"mh_pillar_{pi}_pp2", max_chars=200, placeholder="e.g. Client outcome or recognition")
                    pp3 = st.text_input("Proof Point 3", value=p.get('proof_3', ''), key=f"mh_pillar_{pi}_pp3", max_chars=200, placeholder="e.g. Data point or methodology")
                    updated_pillars.append({
                        'name': p_name, 'tagline': p_tagline, 'headline_claim': p_headline,
                        'proof_1': pp1, 'proof_2': pp2, 'proof_3': pp3
                    })

            st.session_state['mh_pillars_json'] = json.dumps(updated_pillars)

            st.markdown("---")

            # --- FOUNDER POSITIONING ---
            st.markdown('<span style="color:#ab8f59; font-weight:700; font-size:0.8rem; letter-spacing:0.05em;">FOUNDER POSITIONING STATEMENT</span>', unsafe_allow_html=True)
            st.caption("One sentence. Used in byline attributions and any content published under the founder's name.")
            st.text_area("FOUNDER POSITIONING STATEMENT", key="mh_founder_positioning", height=70, max_chars=1000,
                label_visibility="collapsed",
                placeholder="e.g. [Name] is the founder of [Company], a [descriptor] specializing in [domain] for [audience].")

            # --- POV STATEMENT ---
            st.markdown('<span style="color:#ab8f59; font-weight:700; font-size:0.8rem; letter-spacing:0.05em;">POINT OF VIEW (POV) STATEMENT</span>', unsafe_allow_html=True)
            st.caption("The founder's contrarian belief that drives all thought leadership. Must be something a reasonable person could disagree with.")
            st.text_area("POINT OF VIEW (POV) STATEMENT", key="mh_pov", height=80, max_chars=1000,
                label_visibility="collapsed",
                placeholder="e.g. [Founder] believes that [widely-held assumption] is [wrong/incomplete] because [evidence]. The implication is [what should change].")

            # --- BOILERPLATE ---
            st.markdown('<span style="color:#ab8f59; font-weight:700; font-size:0.8rem; letter-spacing:0.05em;">COMPANY BOILERPLATE</span>', unsafe_allow_html=True)
            st.caption("2-3 sentences max. The standard company description used at the end of press releases and in media materials.")
            boilerplate_val = st.text_area("COMPANY BOILERPLATE", key="mh_boilerplate", height=100, max_chars=1500,
                label_visibility="collapsed",
                placeholder="e.g. [Company] is a [descriptor] specializing in [domain]. Founded in [year] by [founder]...")
            if boilerplate_val:
                wc = len(boilerplate_val.split())
                sc = boilerplate_val.count('.') + boilerplate_val.count('!') + boilerplate_val.count('?')
                if wc > 80 or sc > 4:
                    st.warning(f"Boilerplate is {wc} words / ~{sc} sentences. Recommended: under 80 words and 4 sentences.")

            st.markdown("---")

            # --- MESSAGING GUARDRAILS ---
            st.markdown('<span style="color:#ab8f59; font-weight:700; font-size:0.8rem; letter-spacing:0.05em;">MESSAGING GUARDRAILS</span>', unsafe_allow_html=True)
            st.caption("Distinct from brand style guardrails — these define messaging boundaries.")
            st.markdown('<span style="color:#5c6b61; font-size:0.75rem;">OFF-LIMITS TOPICS</span>', unsafe_allow_html=True)
            st.text_area("OFF-LIMITS TOPICS", key="mh_offlimits", height=70, max_chars=1000,
                label_visibility="collapsed",
                placeholder="e.g. Client names without written approval, competitor pricing, pending features",
                help="Topics that are never addressed in external communications without documented approval.")
            st.markdown('<span style="color:#5c6b61; font-size:0.75rem;">CLAIMS REQUIRING PRE-APPROVAL</span>', unsafe_allow_html=True)
            st.text_area("CLAIMS REQUIRING PRE-APPROVAL", key="mh_preapproval_claims", height=70, max_chars=1000,
                label_visibility="collapsed",
                placeholder="e.g. New statistics, comparative claims against competitors, client outcome data",
                help="Any claims that cannot be used externally without documented sign-off.")
            st.markdown('<span style="color:#5c6b61; font-size:0.75rem;">TONE CONSTRAINTS</span>', unsafe_allow_html=True)
            st.text_area("TONE CONSTRAINTS", key="mh_tone_constraints", height=70, max_chars=1000,
                label_visibility="collapsed",
                placeholder="e.g. No unsubstantiated superlatives, no promises about earned media outcomes",
                help="Specific tonal boundaries beyond general brand voice.")

        with st.expander("2. VOICE & CALIBRATION"):
            st.caption("Upload existing content to train the engine on your voice.")
            st.selectbox("CONTENT TYPE", get_ordered_display_options("editor"), key="wiz_sample_type")
            v_tab1, v_tab2 = st.tabs(["PASTE TEXT", "UPLOAD FILE"])
            with v_tab1: st.text_area("PASTE TEXT HERE", key="wiz_temp_text", height=150, max_chars=10000)
            with v_tab2:
                u_key = f"uploader_{st.session_state['file_uploader_key']}"
                st.file_uploader("UPLOAD (PDF, DOCX, TXT, IMG)", type=["pdf", "docx", "txt", "png", "jpg"], key=u_key)
            st.button("ADD SAMPLE", on_click=add_voice_sample_callback)
            if st.session_state['wiz_samples_list']: 
                st.divider()
                st.markdown(f"**VOICE BUFFER: {len(st.session_state['wiz_samples_list'])} SAMPLES**")
                for i, sample in enumerate(st.session_state['wiz_samples_list']):
                    col_text, col_del = st.columns([4, 1])
                    with col_text: st.caption(f"> {sample.splitlines()[0]}")
                    with col_del:
                        if st.button("REMOVE", key=f"del_sample_{i}", type="secondary"):
                            st.session_state['wiz_samples_list'].pop(i)
                            st.rerun()

        with st.expander("3. SOCIAL MEDIA (BRAND BENCHMARK)"):
            st.caption("Upload 'Representative' posts that capture your ideal look & feel.")
            
            c1, c2 = st.columns([1, 2])
            with c1:
                s_plat = st.selectbox("PLATFORM", ["LinkedIn", "Instagram", "X (Twitter)"], key="wiz_social_platform")
                # CREATOR MODE: Toggle matching Manager
                wiz_soc_mode = st.radio("INPUT SOURCE", ["Upload Image", "Paste Text"], horizontal=True, key="wiz_soc_mode")
            with c2:
                s_file = None
                s_text = None
                if wiz_soc_mode == "Upload Image":
                    # --- CSS FIX FOR UPLOADER STYLE ---
                    st.markdown("""
                        <style>
                        [data-testid='stFileUploader'] section {
                            background-color: rgba(36, 54, 59, 0.05) !important;
                            border: 1px dashed #ab8f59 !important;
                        }
                        [data-testid='stFileUploader'] section > div {
                            color: #24363b !important;
                        }
                        [data-testid='stFileUploader'] section small {
                            color: #5c6b61 !important;
                        }
                        [data-testid='stFileUploader'] button {
                            border-color: #ab8f59 !important;
                            color: #24363b !important;
                        }
                        </style>
                    """, unsafe_allow_html=True)
                    # ----------------------------------
                    s_key = f"social_up_{st.session_state['social_uploader_key']}"
                    s_file = st.file_uploader("UPLOAD SCREENSHOT", type=["png", "jpg"], key=s_key)
                else:
                    s_text = st.text_area("PASTE POST TEXT", height=100, key="wiz_soc_text_area")
            
            # --- NEW: STATEFUL ANALYSIS PREVIEW ---
            if 'temp_social_analysis' not in st.session_state: st.session_state['temp_social_analysis'] = ""
            
            if st.button("ANALYZE POST"):
                if wiz_soc_mode == "Upload Image" and s_file:
                    with st.spinner("REVERSE ENGINEERING VISUAL STRATEGY..."):
                        img = Image.open(s_file)
                        st.session_state['temp_social_analysis'] = logic_engine.analyze_social_style(img)
                elif wiz_soc_mode == "Paste Text" and s_text:
                    with st.spinner("ANALYZING TEXT STRUCTURE..."):
                        st.session_state['temp_social_analysis'] = s_text
            
            # --- THE FEEDBACK LOOP ---
            if st.session_state['temp_social_analysis']:
                st.markdown("####  AI FINDINGS (REVIEW & EDIT)")
                st.caption("Edit the analysis below to ensure it matches your brand standards.")
                
                edited_analysis = st.text_area(
                    "SOCIAL SAMPLES", 
                    value=st.session_state['temp_social_analysis'], 
                    height=200,
                    key="social_edit_box",
                    max_chars=5000
                )
                
                if st.button("CONFIRM & ADD TO SAMPLES", type="primary", disabled=_ba_trial_readonly):
                    entry = {
                        "file": s_file,
                        "platform": s_plat,
                        "analysis": edited_analysis # Save the EDITED version
                    }
                    st.session_state['wiz_social_list'].append(entry)
                    st.session_state['temp_social_analysis'] = "" # Reset
                    st.session_state['social_uploader_key'] += 1 # Reset Uploader
                    st.success("Added to Social Samples Buffer")
                    st.rerun()

            # BUFFER DISPLAY
            if st.session_state['wiz_social_list']:
                st.divider()
                st.markdown(f"**SOCIAL BUFFER: {len(st.session_state['wiz_social_list'])} CONFIRMED POSTS**")
                for i, item in enumerate(st.session_state['wiz_social_list']):
                    with st.container():
                        c1, c2 = st.columns([4,1])
                        with c1: 
                            st.markdown(f"**{item['platform']}**")
                            st.caption(item['analysis'])
                        with c2: 
                            if st.button("REMOVE", key=f"del_social_{i}", type="secondary"):
                                st.session_state['wiz_social_list'].pop(i)
                                st.rerun()
                        st.divider()
            
        with st.expander("4. VISUALS (DYNAMIC PALETTE)"):
            st.markdown("##### LOGO")
            l_key = f"logo_up_{st.session_state['logo_uploader_key']}"
            st.file_uploader("UPLOAD LOGO", type=["png", "jpg", "svg"], key=l_key)
            st.button("ADD LOGO", on_click=add_logo_callback)
            if st.session_state['wiz_logo_list']:
                st.divider()
                st.markdown(f"**LOGO BUFFER: {len(st.session_state['wiz_logo_list'])} FILES**")
                for i, item in enumerate(st.session_state['wiz_logo_list']):
                    c1, c2 = st.columns([4,1])
                    with c1: st.caption(f"> {item['file'].name}")
                    with c2: 
                        if st.button("REMOVE", key=f"del_logo_{i}", type="secondary"):
                            st.session_state['wiz_logo_list'].pop(i)
                            st.rerun()
            st.divider()
            
            st.markdown("##### COLOR PALETTE")
            st.caption("Press 'Enter' after pasting a hex code for it to register.")
            
            st.markdown("**PRIMARY COLORS**")
            for i, color in enumerate(st.session_state['palette_primary']):
                c1, c2 = st.columns([4,1])
                with c1: st.session_state['palette_primary'][i] = st.color_picker(f"Primary {i+1}", color, key=f"p_{i}")
                with c2:
                    if st.button("REMOVE", key=f"del_p_{i}", type="secondary"):
                        remove_palette_color('palette_primary', i)
                        st.rerun()
            st.button("ADD PRIMARY COLOR", on_click=add_palette_color, args=('palette_primary',))
            
            st.markdown("---")
            st.markdown("**SECONDARY COLORS**")
            for i, color in enumerate(st.session_state['palette_secondary']):
                c1, c2 = st.columns([4,1])
                with c1: st.session_state['palette_secondary'][i] = st.color_picker(f"Secondary {i+1}", color, key=f"s_{i}")
                with c2:
                    if st.button("REMOVE", key=f"del_s_{i}", type="secondary"):
                        remove_palette_color('palette_secondary', i)
                        st.rerun()
            st.button("ADD SECONDARY COLOR", on_click=add_palette_color, args=('palette_secondary',))
            
            st.markdown("---")
            st.markdown("**ACCENT COLORS**")
            for i, color in enumerate(st.session_state['palette_accent']):
                c1, c2 = st.columns([4,1])
                with c1: st.session_state['palette_accent'][i] = st.color_picker(f"Accent {i+1}", color, key=f"a_{i}")
                with c2:
                    if st.button("REMOVE", key=f"del_a_{i}", type="secondary"):
                        remove_palette_color('palette_accent', i)
                        st.rerun()
            st.button("ADD ACCENT COLOR", on_click=add_palette_color, args=('palette_accent',))

        if st.button("GENERATE SYSTEM", type="primary", disabled=_ba_trial_readonly):
            # Brand limit check
            if not _is_super_admin():
                brand_check = sub_manager.check_brand_limit(st.session_state.get('user_id', ''))
                if not brand_check['allowed']:
                    tier_name = st.session_state.get('tier', {}).get('display_name', 'your current plan')
                    st.error(f"Your {tier_name} plan supports up to {brand_check['max']} brands. Delete an existing brand or upgrade to add more.")
                    if st.button("VIEW PLANS", key="ba_upgrade_brands"):
                        st.session_state['app_mode'] = "SUBSCRIPTION"
                        st.rerun()
                    st.stop()
            if not st.session_state.get("wiz_name") or not st.session_state.get("wiz_archetype"): st.error("NAME/ARCHETYPE REQUIRED")
            else:
                with st.spinner("CALIBRATING..."):
                    try:
                        palette_str = f"Primary: {', '.join(st.session_state['palette_primary'])}. Secondary: {', '.join(st.session_state['palette_secondary'])}. Accents: {', '.join(st.session_state['palette_accent'])}."
                        
                        logo_desc_list = [f"Logo Variant ({item['file'].name}): {logic_engine.describe_logo(Image.open(item['file']))}" for item in st.session_state['wiz_logo_list']]
                        logo_summary = "\n".join(logo_desc_list) if logo_desc_list else "None provided."
                        
                        # USE PRE-ANALYZED SOCIAL DATA
                        # We don't re-run analysis here. We use the stored 'analysis' string.
                        social_desc_list = [f"Platform: {item['platform']}.\nAnalysis: {item['analysis']}" for item in st.session_state['wiz_social_list']]
                        social_summary = "\n---\n".join(social_desc_list) if social_desc_list else "None provided."
                        
                        all_samples = "\n---\n".join(st.session_state['wiz_samples_list'])
                        
                        prompt = f"""
                        SYSTEM INSTRUCTION: Generate a comprehensive brand profile strictly following the numbered format below.
                        1. STRATEGY: Brand: {st.session_state.wiz_name}. Archetype: {st.session_state.wiz_archetype}. Mission: {st.session_state.wiz_mission}. Values: {st.session_state.wiz_values}
                        2. VOICE: Tone: {st.session_state.wiz_tone}. Analysis:
                        --- BEGIN SAMPLES ---
                        {all_samples}
                        --- END SAMPLES ---
                        3. VISUALS: Palette: {palette_str}. Logo: {logo_summary}. Social Samples: {social_summary}
                        4. GUARDRAILS: {st.session_state.wiz_guardrails}
                        """
                        
                        final_text_out = logic_engine.generate_brand_rules(prompt)
                        
                        profile_data = {
                            "final_text": final_text_out,
                            "inputs": {
                                "wiz_name": st.session_state.wiz_name,
                                "wiz_archetype": st.session_state.wiz_archetype,
                                "wiz_tone": st.session_state.wiz_tone,
                                "wiz_mission": st.session_state.wiz_mission,
                                "wiz_values": st.session_state.wiz_values,
                                "wiz_guardrails": st.session_state.wiz_guardrails,
                                "palette_primary": st.session_state['palette_primary'],
                                "palette_secondary": st.session_state['palette_secondary'],
                                "palette_accent": st.session_state['palette_accent'],
                                "social_dna": social_summary, # PERSIST THE SOCIAL SAMPLES
                                "mh_brand_promise": st.session_state.get('mh_brand_promise', ''),
                                "mh_pillars_json": st.session_state.get('mh_pillars_json', ''),
                                "mh_founder_positioning": st.session_state.get('mh_founder_positioning', ''),
                                "mh_pov": st.session_state.get('mh_pov', ''),
                                "mh_boilerplate": st.session_state.get('mh_boilerplate', ''),
                                "mh_offlimits": st.session_state.get('mh_offlimits', ''),
                                "mh_preapproval_claims": st.session_state.get('mh_preapproval_claims', ''),
                                "mh_tone_constraints": st.session_state.get('mh_tone_constraints', '')
                            }
                        }
                        
                        profile_name = f"{st.session_state.wiz_name} (Gen)"
                        st.session_state['profiles'][profile_name] = profile_data
                        
                        # SAVE TO DB
                        db.save_profile(st.session_state['user_id'], profile_name, profile_data)

                        # FORCE SWITCH TO NEW PROFILE
                        st.session_state['active_profile_name'] = profile_name

                        # LOG TO DB (GOD MODE)
                        db.log_event(
                            org_id=st.session_state.get('org_id', 'Unknown'),
                            username=st.session_state.get('username', 'Unknown'),
                            activity_type="PROFILE CREATED",
                            asset_name=profile_name,
                            score=100, # Baseline score for creation
                            verdict="SUCCESS",
                            metadata={"method": "Blueprint Generator"}
                        )

                        # Analytics: brand created + onboarding milestone
                        _pa_u = st.session_state.get('username', '')
                        _pa_sid = st.session_state.get('_analytics_session_id')
                        _pa_org = st.session_state.get('org_id')
                        db.track_event("brand_created", _pa_u,
                                       metadata={"name": profile_name, "method": "blueprint_generator"},
                                       session_id=_pa_sid, org_id=_pa_org)
                        db.check_milestone(_pa_u, "first_brand_created",
                                           session_id=_pa_sid, org_id=_pa_org)

                        st.session_state['wiz_samples_list'] = []
                        st.session_state['wiz_social_list'] = []
                        st.session_state['wiz_logo_list'] = []
                        st.success("CALIBRATED & SAVED TO DATABASE")
                        st.rerun()
                    except Exception as e:
                        if "ResourceExhausted" in str(e): st.error(" PROCESSING: Please wait 60 seconds.")
                        else: st.error(f"Error: {e}")

    # -----------------------------------------------------------
    # TAB 2: MANAGE BRAND (THE OLD MANAGER)
    # -----------------------------------------------------------
    with main_tab2:
        st.markdown("### MANAGE BRAND")
        st.caption("Edit, refine, and inject new assets into existing profiles.")
        
        if st.session_state['profiles']:
            p_keys = list(st.session_state['profiles'].keys())
            default_ix = 0
            if st.session_state.get('active_profile_name') in p_keys:
                default_ix = p_keys.index(st.session_state['active_profile_name'])
            target = st.selectbox("SELECT PROFILE TO MANAGE", p_keys, index=default_ix)
            profile_obj = st.session_state['profiles'][target]
            
            is_structured = isinstance(profile_obj, dict) and "inputs" in profile_obj
            final_text_view = profile_obj['final_text'] if is_structured else profile_obj
            
            # --- VIEW MODES ---
            view_tab1, view_tab2 = st.tabs(["EDITOR & INJECTOR", "LIVE PREVIEW"])
            
            with view_tab2:
                st.markdown("### CURRENT BRAND KIT")
                st.caption("This is the data the AI uses to generate and review content.")
                st.text_area("READ-ONLY VIEW", value=final_text_view, height=600, disabled=True)
                
                html_data = convert_to_html_brand_card(target, final_text_view)
                st.download_button(label="DOWNLOAD HTML REPORT", data=html_data, file_name=f"{target.replace(' ', '_')}_BrandKit.html", mime="text/html")

            with view_tab1:
                st.divider()
                
                if is_structured:
                    inputs = profile_obj['inputs']
                    
                    # --- SAFETY INIT ---
                    for key in ['social_dna', 'voice_dna', 'visual_dna']:
                        if key not in inputs: inputs[key] = ""
                    for key in ['palette_primary', 'palette_secondary', 'palette_accent']:
                        if key not in inputs: inputs[key] = []
                    for key in ['mh_brand_promise', 'mh_pillars_json', 'mh_founder_positioning',
                                'mh_pov', 'mh_boilerplate', 'mh_offlimits', 'mh_preapproval_claims', 'mh_tone_constraints']:
                        if key not in inputs: inputs[key] = ""
                    
                    # 1. STRATEGY
                    with st.expander("1. STRATEGY", expanded=True):
                        new_name = st.text_input("BRAND NAME", inputs['wiz_name'], max_chars=100)
                        idx = ARCHETYPES.index(inputs['wiz_archetype']) if inputs['wiz_archetype'] in ARCHETYPES else 0
                        def format_archetype_edit(option):
                            if option in ARCHETYPE_INFO:
                                return f"{option} | {ARCHETYPE_INFO[option]['tagline']}"
                            return option

                        new_arch = st.selectbox(
                            "ARCHETYPE", 
                            ARCHETYPES, 
                            index=idx,
                            format_func=format_archetype_edit
                        )
                        if new_arch:
                            info = ARCHETYPE_INFO[new_arch]
                            st.markdown(f"""
                                <div style="background-color: rgba(36, 54, 59, 0.05); border-left: 3px solid #ab8f59; padding: 10px; margin-top: 5px; margin-bottom: 15px;">
                                    <strong style="color: #24363b; display: block; margin-bottom: 4px;">THE AESTHETIC:</strong>
                                    <span style="color: #5c6b61; font-size: 0.85rem;">{info['desc']}</span>
                                </div>
                            """, unsafe_allow_html=True)
                        new_mission = st.text_area("MISSION", inputs['wiz_mission'], max_chars=2000)
                        new_values = st.text_area("VALUES", inputs['wiz_values'], max_chars=2000)
                    
                    # 2. VOICE
                    with st.expander("2. VOICE"):
                        new_tone = st.text_input("TONE KEYWORDS", inputs['wiz_tone'], max_chars=100)
                    
                    # 3. GUARDRAILS
                    with st.expander("3. GUARDRAILS"):
                        new_guard = st.text_area("DO'S & DON'TS", inputs['wiz_guardrails'], max_chars=2000)

                    # 3.5 MESSAGE HOUSE
                    with st.expander("MESSAGE HOUSE"):
                        st.caption("The authoritative messaging document. Changes are saved with 'SAVE STRATEGY CHANGES'.")

                        st.markdown('<span style="color:#ab8f59; font-weight:700; font-size:0.8rem; letter-spacing:0.05em;">BRAND PROMISE</span>', unsafe_allow_html=True)
                        new_mh_brand_promise = st.text_area("BRAND PROMISE", inputs['mh_brand_promise'], max_chars=500, height=80, label_visibility="collapsed", key="mgr_mh_brand_promise")
                        if new_mh_brand_promise and new_mh_brand_promise.count('.') > 2:
                            st.warning("Brand promise should be 1-2 sentences.")

                        st.markdown("---")
                        st.markdown('<span style="color:#ab8f59; font-weight:700; font-size:0.8rem; letter-spacing:0.05em;">MESSAGE PILLARS</span>', unsafe_allow_html=True)

                        try:
                            mgr_pillars = json.loads(inputs['mh_pillars_json']) if inputs['mh_pillars_json'] else [{}, {}, {}]
                            if len(mgr_pillars) < 3:
                                mgr_pillars += [{} for _ in range(3 - len(mgr_pillars))]
                        except (json.JSONDecodeError, TypeError):
                            mgr_pillars = [{}, {}, {}]

                        mgr_updated_pillars = []
                        for pi in range(3):
                            p = mgr_pillars[pi] if pi < len(mgr_pillars) else {}
                            with st.expander(f"PILLAR {pi + 1}"):
                                p_name = st.text_input("NAME", value=p.get('name', ''), key=f"mgr_mh_pillar_{pi}_name", max_chars=100)
                                p_tagline = st.text_input("TAGLINE", value=p.get('tagline', ''), key=f"mgr_mh_pillar_{pi}_tagline", max_chars=150)
                                p_headline = st.text_area("HEADLINE CLAIM", value=p.get('headline_claim', ''), key=f"mgr_mh_pillar_{pi}_headline", max_chars=500, height=70)
                                pp1 = st.text_input("Proof 1", value=p.get('proof_1', ''), key=f"mgr_mh_pillar_{pi}_pp1", max_chars=200)
                                pp2 = st.text_input("Proof 2", value=p.get('proof_2', ''), key=f"mgr_mh_pillar_{pi}_pp2", max_chars=200)
                                pp3 = st.text_input("Proof 3", value=p.get('proof_3', ''), key=f"mgr_mh_pillar_{pi}_pp3", max_chars=200)
                                mgr_updated_pillars.append({
                                    'name': p_name, 'tagline': p_tagline, 'headline_claim': p_headline,
                                    'proof_1': pp1, 'proof_2': pp2, 'proof_3': pp3
                                })

                        new_mh_pillars_json = json.dumps(mgr_updated_pillars)

                        st.markdown("---")
                        st.markdown('<span style="color:#ab8f59; font-weight:700; font-size:0.8rem; letter-spacing:0.05em;">FOUNDER POSITIONING STATEMENT</span>', unsafe_allow_html=True)
                        new_mh_founder = st.text_area("FOUNDER POSITIONING STATEMENT", inputs['mh_founder_positioning'], max_chars=1000, height=70, label_visibility="collapsed", key="mgr_mh_founder")
                        st.markdown('<span style="color:#ab8f59; font-weight:700; font-size:0.8rem; letter-spacing:0.05em;">POINT OF VIEW (POV) STATEMENT</span>', unsafe_allow_html=True)
                        new_mh_pov = st.text_area("POINT OF VIEW (POV) STATEMENT", inputs['mh_pov'], max_chars=1000, height=80, label_visibility="collapsed", key="mgr_mh_pov")
                        st.markdown('<span style="color:#ab8f59; font-weight:700; font-size:0.8rem; letter-spacing:0.05em;">COMPANY BOILERPLATE</span>', unsafe_allow_html=True)
                        new_mh_boilerplate = st.text_area("COMPANY BOILERPLATE", inputs['mh_boilerplate'], max_chars=1500, height=100, label_visibility="collapsed", key="mgr_mh_boilerplate")
                        if new_mh_boilerplate:
                            wc = len(new_mh_boilerplate.split())
                            sc = new_mh_boilerplate.count('.') + new_mh_boilerplate.count('!') + new_mh_boilerplate.count('?')
                            if wc > 80 or sc > 4:
                                st.warning(f"Boilerplate: {wc} words / ~{sc} sentences. Recommended: under 80 words, 4 sentences.")

                        st.markdown("---")
                        st.markdown('<span style="color:#ab8f59; font-weight:700; font-size:0.8rem; letter-spacing:0.05em;">MESSAGING GUARDRAILS</span>', unsafe_allow_html=True)
                        st.markdown('<span style="color:#5c6b61; font-size:0.75rem;">OFF-LIMITS TOPICS</span>', unsafe_allow_html=True)
                        new_mh_offlimits = st.text_area("OFF-LIMITS TOPICS", inputs['mh_offlimits'], max_chars=1000, height=70, label_visibility="collapsed", key="mgr_mh_offlimits")
                        st.markdown('<span style="color:#5c6b61; font-size:0.75rem;">CLAIMS REQUIRING PRE-APPROVAL</span>', unsafe_allow_html=True)
                        new_mh_preapproval = st.text_area("CLAIMS REQUIRING PRE-APPROVAL", inputs['mh_preapproval_claims'], max_chars=1000, height=70, label_visibility="collapsed", key="mgr_mh_preapproval")
                        st.markdown('<span style="color:#5c6b61; font-size:0.75rem;">TONE CONSTRAINTS</span>', unsafe_allow_html=True)
                        new_mh_tone_constraints = st.text_area("TONE CONSTRAINTS", inputs['mh_tone_constraints'], max_chars=1000, height=70, label_visibility="collapsed", key="mgr_mh_tone_constraints")

                    # 4. VISUAL IDENTITY (PALETTE)
                    with st.expander("4. VISUAL IDENTITY (PALETTE)"):
                        st.markdown("##### COLOR PALETTE")
                        st.caption("Define the hex codes for the automated Visual Audit.")

                        # PRIMARY COLORS
                        st.markdown("**PRIMARY COLORS**")
                        if not inputs['palette_primary']: inputs['palette_primary'] = []
                        for i, color in enumerate(inputs['palette_primary']):
                            c1, c2 = st.columns([4,1])
                            with c1:
                                new_color = st.color_picker(f"Primary {i+1}", color, key=f"mgr_p_{i}")
                                inputs['palette_primary'][i] = new_color
                            with c2:
                                if st.button("REMOVE", key=f"mgr_del_p_{i}", type="secondary"):
                                    inputs['palette_primary'].pop(i)
                                    st.rerun()
                        if st.button("ADD PRIMARY COLOR", key="mgr_add_p"):
                            inputs['palette_primary'].append("#000000")
                            st.rerun()

                        st.markdown("---")
                        
                        # SECONDARY COLORS
                        st.markdown("**SECONDARY COLORS**")
                        if not inputs['palette_secondary']: inputs['palette_secondary'] = []
                        for i, color in enumerate(inputs['palette_secondary']):
                            c1, c2 = st.columns([4,1])
                            with c1:
                                new_color = st.color_picker(f"Secondary {i+1}", color, key=f"mgr_s_{i}")
                                inputs['palette_secondary'][i] = new_color
                            with c2:
                                if st.button("REMOVE", key=f"mgr_del_s_{i}", type="secondary"):
                                    inputs['palette_secondary'].pop(i)
                                    st.rerun()
                        if st.button("ADD SECONDARY COLOR", key="mgr_add_s"):
                            inputs['palette_secondary'].append("#000000")
                            st.rerun()

                        st.markdown("---")

                        # ACCENT COLORS
                        st.markdown("**ACCENT COLORS**")
                        if not inputs['palette_accent']: inputs['palette_accent'] = []
                        for i, color in enumerate(inputs['palette_accent']):
                            c1, c2 = st.columns([4,1])
                            with c1:
                                new_color = st.color_picker(f"Accent {i+1}", color, key=f"mgr_a_{i}")
                                inputs['palette_accent'][i] = new_color
                            with c2:
                                if st.button("REMOVE", key=f"mgr_del_a_{i}", type="secondary"):
                                    inputs['palette_accent'].pop(i)
                                    st.rerun()
                        if st.button("ADD ACCENT COLOR", key="mgr_add_a"):
                            inputs['palette_accent'].append("#000000")
                            st.rerun()
                    
                    # --- CALIBRATION & ASSETS ---
                    st.markdown("### CALIBRATION LAB & ASSET LIBRARY")
                    st.info("Upload assets to train the engine. View and manage uploaded assets in the lists below.")
                    
                    cal_tab1, cal_tab2, cal_tab3 = st.tabs(["SOCIAL MEDIA", "VOICE & TONE", "VISUAL ID"])
                    
                    # --- 1. SOCIAL INJECTOR ---
                    with cal_tab1:
                        # UPLOAD SECTION
                        c1, c2 = st.columns(2)
                        with c1:
                            cal_platform = st.selectbox("PLATFORM", ["LinkedIn", "X (Twitter)", "Instagram"], key="cal_plat")
                            
                        with c2:
                            # --- TABS FOR CONSISTENCY (MATCHING VOICE TAB) ---
                            s_tab1, s_tab2 = st.tabs(["UPLOAD SCREENSHOT", "PASTE TEXT"])
                            
                            cal_img = None
                            raw_post_text = None
                            
                            with s_tab1:
                                s_key = f"social_up_mgr_{st.session_state.get('social_uploader_key', 0)}"
                                cal_img = st.file_uploader("UPLOAD IMAGE", type=["png", "jpg"], key=s_key)
                                
                            with s_tab2:
                                raw_post_text = st.text_area("PASTE POST COPY", height=100, key="soc_raw_text_mgr")
                        
                        if 'man_social_analysis' not in st.session_state: st.session_state['man_social_analysis'] = ""
                        
                        # LOGIC BRANCH: IMAGE vs TEXT
                        if cal_img and st.button(f"ANALYZE {cal_platform.upper()} POST (IMAGE)", type="primary", key="btn_cal_social_img"):
                            with st.spinner("REVERSE ENGINEERING..."):
                                img = Image.open(cal_img)
                                st.session_state['man_social_analysis'] = logic_engine.analyze_social_style(img)
                        elif raw_post_text and st.button(f"INGEST {cal_platform.upper()} POST (TEXT)", type="primary", key="btn_cal_social_txt"):
                             st.session_state['man_social_analysis'] = raw_post_text
                        
                        if st.session_state['man_social_analysis']:
                            st.markdown("#### REVIEW FINDINGS")
                            edit_social = st.text_area("EDIT ANALYSIS", value=st.session_state['man_social_analysis'], key="rev_social", height=150, max_chars=5000)
                            if st.button("CONFIRM & INJECT (SOCIAL)", type="primary", disabled=_ba_trial_readonly):
                                from datetime import datetime
                                timestamp = datetime.now().strftime("%Y-%m-%d")
                                
                                # Process Visual for Storage
                                vis_ref = ""
                                if cal_img:
                                    b64_img = process_image_for_storage(cal_img)
                                    if b64_img:
                                        vis_ref = f"\n[VISUAL_REF: {b64_img}]"

                                injection = f"\n\n[ASSET: {cal_platform.upper()} POST | DATE: {timestamp}]\n{edit_social}{vis_ref}\n----------------\n"
                                
                                inputs['social_dna'] += injection
                                
                                # UPDATE SCORE
                                profile_obj = update_calibration_score(profile_obj)
                                
                                db.save_profile(st.session_state['user_id'], target, profile_obj)
                                st.session_state['man_social_analysis'] = ""

                                # LOG TO DB
                                db.log_event(
                                    org_id=st.session_state.get('org_id', 'Unknown'),
                                    username=st.session_state.get('username', 'Unknown'),
                                    activity_type="ASSET INJECTION",
                                    asset_name=f"Social: {cal_platform}",
                                    score=profile_obj.get('calibration_score', 0),
                                    verdict="ADDED SOCIAL",
                                    metadata={"type": "social_dna", "content": edit_social[:50]+"..."}
                                )

                                # Analytics: sample uploaded + calibration change
                                _pa_u = st.session_state.get('username', '')
                                _pa_sid = st.session_state.get('_analytics_session_id')
                                _pa_org = st.session_state.get('org_id')
                                _new_score = profile_obj.get('calibration_score', 0)
                                _old_score = st.session_state.get('_last_cal_score', 0)
                                social_count = inputs.get('social_dna', '').count('[ASSET:')
                                db.track_event("sample_uploaded", _pa_u,
                                               metadata={"type": "social", "platform": cal_platform, "new_count": social_count},
                                               session_id=_pa_sid, org_id=_pa_org)
                                if _new_score != _old_score:
                                    db.track_event("calibration_change", _pa_u,
                                                   metadata={"old_score": _old_score, "new_score": _new_score, "trigger": "social_sample_added"},
                                                   session_id=_pa_sid, org_id=_pa_org)
                                    if _new_score >= 60 and _old_score < 60:
                                        db.check_milestone(_pa_u, "calibration_crossed_60", session_id=_pa_sid, org_id=_pa_org)
                                    if _new_score >= 90 and _old_score < 90:
                                        db.check_milestone(_pa_u, "calibration_crossed_90", session_id=_pa_sid, org_id=_pa_org)
                                st.session_state['_last_cal_score'] = _new_score

                                st.success(f"Asset Injected. Calibration Score updated to {profile_obj.get('calibration_score', 0)}%.")
                                st.rerun()
                        
                        # LIBRARY VIEW
                        st.divider()
                        st.markdown("#### ACTIVE ASSETS")
                        social_assets = parse_assets_from_text(inputs['social_dna'])
                        if social_assets:
                            for i, asset in enumerate(social_assets):
                                with st.container():
                                    st.markdown(f"<div class='asset-box'><div class='asset-header'>{asset['header']}</div></div>", unsafe_allow_html=True)
                                    c_img, c_txt, c_del = st.columns([1, 3, 1])
                                    with c_img:
                                        if asset['image']:
                                            st.image(asset['image'], caption="Asset Thumbnail")
                                        else:
                                            st.caption("No Image")
                                    with c_txt:
                                        with st.expander("View Analysis"):
                                            st.text(asset['content'])
                                    with c_del:
                                        if st.button("DELETE", key=f"del_soc_{i}", type="secondary"):
                                            inputs['social_dna'] = inputs['social_dna'].replace(asset['full_text'], "")
                                            profile_obj = update_calibration_score(profile_obj)
                                            db.save_profile(st.session_state['user_id'], target, profile_obj)

                                            # LOG DELETION
                                            db.log_event(
                                                org_id=st.session_state.get('org_id', 'Unknown'),
                                                username=st.session_state.get('username', 'Unknown'),
                                                activity_type="ASSET DELETED",
                                                asset_name=asset['header'],
                                                score=profile_obj.get('calibration_score', 0),
                                                verdict="REMOVED",
                                                metadata={"type": "social_dna"}
                                            )
                                            # Analytics: sample deleted
                                            db.track_event("sample_deleted", st.session_state.get('username', ''),
                                                           metadata={"type": "social", "new_count": inputs.get('social_dna', '').count('[ASSET:')},
                                                           session_id=st.session_state.get('_analytics_session_id'),
                                                           org_id=st.session_state.get('org_id'))
                                            st.rerun()
                        else:
                            st.caption("No social assets calibrated.")

                    # --- 2. VOICE INJECTOR (FORTIFICATION PROTOCOL) ---
                    with cal_tab2:
                        c1, c2 = st.columns([1, 1])
                        with c1:
                            # THE 5 CLUSTERS — descriptions + content type guidance from shared config
                            _cluster_roles = {
                                "Corporate Affairs": "STANDARDIZATION & RECORD",
                                "Crisis & Response": "DEFENSE & MITIGATION",
                                "Internal Leadership": "ALIGNMENT & MORALE",
                                "Thought Leadership": "INFLUENCE & AUTHORITY",
                                "Brand Marketing": "GROWTH & CONVERSION",
                            }
                            _cluster_intros = {
                                "Corporate Affairs": "Maintains objective accuracy and establishes the baseline narrative.",
                                "Crisis & Response": "Fortifies reputation during volatility. Prioritizes empathy and rapid stabilization.",
                                "Internal Leadership": "Strengthens cultural cohesion and transmits directives from the top down.",
                                "Thought Leadership": "Penetrates new markets via argumentation and distinct perspective.",
                                "Brand Marketing": "Drives action through persuasion and benefit-driven framing.",
                            }
                            VOICE_CLUSTERS = {}
                            for _vc_name in CT_CLUSTER_NAMES:
                                _vc_types = [v["label"] for v in CONTENT_TYPES.values() if v.get("cluster") == _vc_name]
                                _vc_type_list = ", ".join(_vc_types) if _vc_types else "various content"
                                VOICE_CLUSTERS[_vc_name] = {
                                    "role": _cluster_roles.get(_vc_name, ""),
                                    "desc": f"{_cluster_intros.get(_vc_name, '')} Upload samples such as: {_vc_type_list}."
                                }
                            
                            voice_type = st.selectbox("COMMUNICATION CLUSTER", list(VOICE_CLUSTERS.keys()), key="cal_type_voice")
                            
                            # THE EXPLAINER BLOCK (Dynamic)
                            info = VOICE_CLUSTERS[voice_type]
                            st.markdown(f"""
                                <div style="background-color: #1b2a2e; border-left: 3px solid #ab8f59; padding: 15px; margin-top: 5px; margin-bottom: 20px;">
                                    <strong style="color: #ab8f59; font-size: 0.75rem; letter-spacing: 1px; display: block; margin-bottom: 5px;">{info['role']}</strong>
                                    <span style="color: #d0d0d0; font-size: 0.85rem; line-height: 1.4;">{info['desc']}</span>
                                </div>
                            """, unsafe_allow_html=True)

                            # TUNERS (Metadata only, not separate buckets)
                            cc1, cc2 = st.columns(2)
                            with cc1:
                                voice_sender = st.text_input("SENDER (CONTEXT)", placeholder="e.g. CEO", key="cal_sender_voice")
                            with cc2:
                                voice_audience = st.text_input("AUDIENCE (TARGET)", placeholder="e.g. Investors", key="cal_audience_voice")
                        
                        with c2:
                            # --- VOICE TEXT PASTE (TABS) ---
                            v_tab1, v_tab2 = st.tabs(["UPLOAD FILE", "PASTE TEXT"])
                            
                            v_file = None
                            v_text_input = None
                            
                            with v_tab1:
                                # UPDATED FILE UPLOADER TO ACCEPT PDF AND DOCX
                                v_file = st.file_uploader("UPLOAD (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="cal_up_voice")
                                st.caption("Engine requires 3+ samples per cluster.")
                                
                            with v_tab2:
                                v_text_input = st.text_area("PASTE RAW CONTENT", height=200, placeholder="Paste article/email text here...", key="cal_paste_voice")
                        
                        if 'man_voice_analysis' not in st.session_state: st.session_state['man_voice_analysis'] = ""
                        
                        if st.button("INITIATE PROTOCOL ANALYSIS", type="primary", key="btn_cal_voice", disabled=_ba_trial_readonly):
                            # VALIDATION
                            valid_input = False
                            raw_txt = ""
                            source_name = "Manual Paste"
                            
                            if v_file:
                                valid_input = True
                                source_name = v_file.name
                                try:
                                    if v_file.type == "application/pdf":
                                        raw_txt = logic_engine.extract_text_from_pdf(v_file)
                                    elif v_file.name.endswith(".docx"):
                                        import docx
                                        doc = docx.Document(v_file)
                                        raw_txt = "\n".join([para.text for para in doc.paragraphs])
                                    else:
                                        raw_txt = str(v_file.read(), "utf-8")
                                except Exception as e:
                                    st.error(f"Read Error: {e}")
                                    valid_input = False
                                    
                            elif v_text_input:
                                valid_input = True
                                raw_txt = v_text_input
                            
                            if valid_input:
                                with st.spinner("DECONSTRUCTING RHETORICAL PATTERNS..."):
                                    try:
                                        prompt = f"""
                                        TASK: Extract the voice profile from this text.
                                        ROLE: Expert Linguist.
                                        CONTEXT: This belongs to the '{voice_type}' cluster.
                                        CONSTRAINTS: No chat. No emojis. Bullet points only.
                                        INPUT TEXT: {raw_txt[:10000]}
                                        OUTPUT FORMAT:
                                        - SYNTAX ARCHITECTURE: (e.g. Complex, Fragmented)
                                        - LEXICON TIER: (e.g. Academic, Slang, Corporate)
                                        - RHETORICAL MECHANICS: (e.g. Metaphors, Questions)
                                        - TONAL FREQUENCY: (e.g. Urgent, Calm, Witty)
                                        """
                                        # logic_engine handles the sanitization of 'prompt'
                                        st.session_state['man_voice_analysis'] = logic_engine.generate_brand_rules(prompt)
                                        st.session_state['temp_voice_source_name'] = source_name # Track source
                                    except Exception as e:
                                        st.error(f"Analysis Failed: {e}")
                            else:
                                st.warning("Please upload a file or paste text.")

                        if st.session_state['man_voice_analysis']:
                            st.markdown("#### ANALYSIS REVIEW")
                            edit_voice = st.text_area("EXTRACTED PATTERNS", value=st.session_state['man_voice_analysis'], key="rev_voice", height=150)
                            
                            if st.button("CONFIRM & FORTIFY ENGINE", type="primary", disabled=_ba_trial_readonly):
                                from datetime import datetime
                                timestamp = datetime.now().strftime("%Y-%m-%d")
                                source_ref = st.session_state.get('temp_voice_source_name', 'Unknown')
                                
                                # UPDATED HEADER WITH NEW TAXONOMY
                                header_meta = f"CLUSTER: {voice_type.upper()} | SENDER: {voice_sender.upper()} | AUDIENCE: {voice_audience.upper()}"
                                injection = f"\n\n[ASSET: {header_meta} | SOURCE: {source_ref} | DATE: {timestamp}]\n{edit_voice}\n----------------\n"
                                
                                inputs['voice_dna'] += injection
                                
                                # Update Score & DB
                                profile_obj = update_calibration_score(profile_obj)
                                db.save_profile(st.session_state['user_id'], target, profile_obj)
                                st.session_state['man_voice_analysis'] = ""

                                # Log
                                db.log_event(
                                    org_id=st.session_state.get('org_id', 'Unknown'),
                                    username=st.session_state.get('username', 'Unknown'),
                                    activity_type="ASSET INJECTION",
                                    asset_name=f"Voice: {voice_type}",
                                    score=profile_obj.get('calibration_score', 0),
                                    verdict="FORTIFIED",
                                    metadata={"cluster": voice_type}
                                )

                                # Analytics: sample uploaded + calibration change
                                _pa_u = st.session_state.get('username', '')
                                _pa_sid = st.session_state.get('_analytics_session_id')
                                _pa_org = st.session_state.get('org_id')
                                _new_score = profile_obj.get('calibration_score', 0)
                                _old_score = st.session_state.get('_last_cal_score', 0)
                                voice_count = inputs.get('voice_dna', '').count('[ASSET:')
                                db.track_event("sample_uploaded", _pa_u,
                                               metadata={"type": "voice", "cluster": voice_type, "new_count": voice_count},
                                               session_id=_pa_sid, org_id=_pa_org)
                                db.check_milestone(_pa_u, "first_voice_sample", session_id=_pa_sid, org_id=_pa_org)
                                if _new_score != _old_score:
                                    db.track_event("calibration_change", _pa_u,
                                                   metadata={"old_score": _old_score, "new_score": _new_score, "trigger": "voice_sample_added"},
                                                   session_id=_pa_sid, org_id=_pa_org)
                                    if _new_score >= 60 and _old_score < 60:
                                        db.check_milestone(_pa_u, "calibration_crossed_60", session_id=_pa_sid, org_id=_pa_org)
                                    if _new_score >= 90 and _old_score < 90:
                                        db.check_milestone(_pa_u, "calibration_crossed_90", session_id=_pa_sid, org_id=_pa_org)
                                st.session_state['_last_cal_score'] = _new_score

                                st.success(f"Cluster Fortified. Calibration Score: {profile_obj.get('calibration_score', 0)}%.")
                                st.rerun()

                        # LIBRARY VIEW
                        st.divider()
                        st.markdown("#### ACTIVE ASSETS")
                        voice_assets = parse_assets_from_text(inputs['voice_dna'])
                        if voice_assets:
                            for i, asset in enumerate(voice_assets):
                                with st.container():
                                    st.markdown(f"<div class='asset-box'><div class='asset-header'>{asset['header']}</div></div>", unsafe_allow_html=True)
                                    c_txt, c_del = st.columns([4,1])
                                    with c_txt:
                                        with st.expander("View Analysis Content"):
                                            st.text(asset['content'])
                                    with c_del:
                                        if st.button("DELETE", key=f"del_voc_{i}", type="secondary"):
                                            inputs['voice_dna'] = inputs['voice_dna'].replace(asset['full_text'], "")
                                            profile_obj = update_calibration_score(profile_obj)
                                            db.save_profile(st.session_state['user_id'], target, profile_obj)

                                            # LOG DELETION
                                            db.log_event(
                                                org_id=st.session_state.get('org_id', 'Unknown'),
                                                username=st.session_state.get('username', 'Unknown'),
                                                activity_type="ASSET DELETED",
                                                asset_name=asset['header'],
                                                score=profile_obj.get('calibration_score', 0),
                                                verdict="REMOVED",
                                                metadata={"type": "voice_dna"}
                                            )
                                            # Analytics: sample deleted
                                            db.track_event("sample_deleted", st.session_state.get('username', ''),
                                                           metadata={"type": "voice", "new_count": inputs.get('voice_dna', '').count('[ASSET:')},
                                                           session_id=st.session_state.get('_analytics_session_id'),
                                                           org_id=st.session_state.get('org_id'))
                                            st.rerun()
                        else:
                            st.caption("No voice assets calibrated.")

                    # --- 3. VISUAL INJECTOR ---
                    with cal_tab3:
                        c1, c2 = st.columns(2)
                        with c1:
                            vis_type = st.selectbox("ASSET TYPE", ["Logo", "Iconography", "Website Screenshot", "Marketing Flyer", "Typography Spec"], key="cal_type_vis")
                        with c2:
                            vis_file = st.file_uploader("UPLOAD VISUAL ASSET (IMG)", type=["png", "jpg"], key="cal_up_vis")
                        
                        if 'man_vis_analysis' not in st.session_state: st.session_state['man_vis_analysis'] = ""
                        
                        if vis_file and st.button("ANALYZE AESTHETIC", type="primary", key="btn_cal_vis", disabled=_ba_trial_readonly):
                            with st.spinner("ANALYZING DESIGN..."):
                                img = Image.open(vis_file)
                                st.session_state['man_vis_analysis'] = logic_engine.describe_logo(img)
                        
                        if st.session_state['man_vis_analysis']:
                            st.markdown("#### REVIEW FINDINGS")
                            edit_vis = st.text_area("EDIT ANALYSIS", value=st.session_state['man_vis_analysis'], key="rev_vis", height=150, max_chars=5000)
                            if st.button("CONFIRM & INJECT (VISUAL)", type="primary", disabled=_ba_trial_readonly):
                                from datetime import datetime
                                timestamp = datetime.now().strftime("%Y-%m-%d")
                                
                                # Process Visual for Storage
                                vis_ref = ""
                                if vis_file:
                                    b64_img = process_image_for_storage(vis_file)
                                    if b64_img:
                                        vis_ref = f"\n[VISUAL_REF: {b64_img}]"

                                injection = f"\n\n[ASSET: {vis_type.upper()} | SOURCE: {vis_file.name} | DATE: {timestamp}]\n{edit_vis}{vis_ref}\n----------------\n"
                                
                                inputs['visual_dna'] += injection
                                
                                # UPDATE SCORE
                                profile_obj = update_calibration_score(profile_obj)
                                
                                db.save_profile(st.session_state['user_id'], target, profile_obj)
                                st.session_state['man_vis_analysis'] = ""

                                # LOG TO DB
                                db.log_event(
                                    org_id=st.session_state.get('org_id', 'Unknown'),
                                    username=st.session_state.get('username', 'Unknown'),
                                    activity_type="ASSET INJECTION",
                                    asset_name=f"Visual: {vis_type}",
                                    score=profile_obj.get('calibration_score', 0),
                                    verdict="ADDED VISUAL",
                                    metadata={"type": "visual_dna", "content": edit_vis[:50]+"..."}
                                )

                                # Analytics: sample uploaded + calibration change
                                _pa_u = st.session_state.get('username', '')
                                _pa_sid = st.session_state.get('_analytics_session_id')
                                _pa_org = st.session_state.get('org_id')
                                _new_score = profile_obj.get('calibration_score', 0)
                                _old_score = st.session_state.get('_last_cal_score', 0)
                                visual_count = inputs.get('visual_dna', '').count('[ASSET:')
                                db.track_event("sample_uploaded", _pa_u,
                                               metadata={"type": "visual", "new_count": visual_count},
                                               session_id=_pa_sid, org_id=_pa_org)
                                if _new_score != _old_score:
                                    db.track_event("calibration_change", _pa_u,
                                                   metadata={"old_score": _old_score, "new_score": _new_score, "trigger": "visual_sample_added"},
                                                   session_id=_pa_sid, org_id=_pa_org)
                                    if _new_score >= 60 and _old_score < 60:
                                        db.check_milestone(_pa_u, "calibration_crossed_60", session_id=_pa_sid, org_id=_pa_org)
                                    if _new_score >= 90 and _old_score < 90:
                                        db.check_milestone(_pa_u, "calibration_crossed_90", session_id=_pa_sid, org_id=_pa_org)
                                st.session_state['_last_cal_score'] = _new_score

                                st.success(f"Asset Injected. Calibration Score updated to {profile_obj.get('calibration_score', 0)}%.")
                                st.rerun()

                        # LIBRARY VIEW
                        st.divider()
                        st.markdown("#### ACTIVE ASSETS")
                        vis_assets = parse_assets_from_text(inputs['visual_dna'])
                        if vis_assets:
                            for i, asset in enumerate(vis_assets):
                                with st.container():
                                    st.markdown(f"<div class='asset-box'><div class='asset-header'>{asset['header']}</div></div>", unsafe_allow_html=True)
                                    c_img, c_txt, c_del = st.columns([1, 3, 1])
                                    with c_img:
                                        if asset['image']:
                                            st.image(asset['image'], caption="Asset Thumbnail")
                                        else:
                                            st.caption("No Image")
                                    with c_txt:
                                        with st.expander("View Analysis"):
                                            st.text(asset['content'])
                                    with c_del:
                                        if st.button("DELETE", key=f"del_vis_{i}", type="secondary"):
                                            inputs['visual_dna'] = inputs['visual_dna'].replace(asset['full_text'], "")
                                            profile_obj = update_calibration_score(profile_obj)
                                            db.save_profile(st.session_state['user_id'], target, profile_obj)

                                            # LOG DELETION
                                            db.log_event(
                                                org_id=st.session_state.get('org_id', 'Unknown'),
                                                username=st.session_state.get('username', 'Unknown'),
                                                activity_type="ASSET DELETED",
                                                asset_name=asset['header'],
                                                score=profile_obj.get('calibration_score', 0),
                                                verdict="REMOVED",
                                                metadata={"type": "visual_dna"}
                                            )
                                            # Analytics: sample deleted
                                            db.track_event("sample_deleted", st.session_state.get('username', ''),
                                                           metadata={"type": "visual", "new_count": inputs.get('visual_dna', '').count('[ASSET:')},
                                                           session_id=st.session_state.get('_analytics_session_id'),
                                                           org_id=st.session_state.get('org_id'))
                                            st.rerun()
                        else:
                            st.caption("No visual assets calibrated.")

                    st.divider()

                    # --- MANUAL EDITORS (ADVANCED) ---
                    with st.expander("MANUAL TEXT EDITORS (READ-ONLY)"):
                        st.info("These fields display the raw data blocks. To edit this content, use the Asset Library tools above.")
                        edit_tab1, edit_tab2, edit_tab3 = st.tabs(["RAW SOCIAL", "RAW VOICE", "RAW VISUAL"])
                        with edit_tab1:
                            st.text_area("SOCIAL SAMPLES BLOB", inputs['social_dna'], height=200, disabled=True)
                        with edit_tab2:
                            st.text_area("VOICE SAMPLES BLOB", inputs['voice_dna'], height=200, disabled=True)
                        with edit_tab3:
                            st.text_area("VISUAL SAMPLES BLOB", inputs['visual_dna'], height=200, disabled=True)

                    if st.button("SAVE STRATEGY CHANGES", type="primary", disabled=_ba_trial_readonly):
                        # 1. Update Standard Inputs
                        profile_obj['inputs']['wiz_name'] = new_name
                        profile_obj['inputs']['wiz_archetype'] = new_arch
                        profile_obj['inputs']['wiz_mission'] = new_mission
                        profile_obj['inputs']['wiz_values'] = new_values
                        profile_obj['inputs']['wiz_tone'] = new_tone
                        profile_obj['inputs']['wiz_guardrails'] = new_guard
                        profile_obj['inputs']['mh_brand_promise'] = new_mh_brand_promise
                        profile_obj['inputs']['mh_pillars_json'] = new_mh_pillars_json
                        profile_obj['inputs']['mh_founder_positioning'] = new_mh_founder
                        profile_obj['inputs']['mh_pov'] = new_mh_pov
                        profile_obj['inputs']['mh_boilerplate'] = new_mh_boilerplate
                        profile_obj['inputs']['mh_offlimits'] = new_mh_offlimits
                        profile_obj['inputs']['mh_preapproval_claims'] = new_mh_preapproval
                        profile_obj['inputs']['mh_tone_constraints'] = new_mh_tone_constraints
                        
                        p_p = ", ".join(inputs['palette_primary'])
                        p_s = ", ".join(inputs['palette_secondary'])
                        p_a = ", ".join(inputs['palette_accent'])
                        
                        # 2. Update Score
                        profile_obj = update_calibration_score(profile_obj)
                        
                        # 3. Rebuild Final Text (The Full Brand Kit)
                        
                        def clean_dna_for_llm(text):
                            """Removes base64 images from text before sending to LLM context."""
                            if not text: return ""
                            lines = text.split('\n')
                            clean = [l for l in lines if not l.startswith("[VISUAL_REF:")]
                            return "\n".join(clean)

                        new_text = f"""
                        1. STRATEGY
                        - Brand: {new_name}
                        - Archetype: {new_arch}
                        - Mission: {new_mission}
                        - Values: {new_values}

                        2. VOICE
                        - Tone Keywords: {new_tone}

                        [VOICE SAMPLES & ASSETS]
                        {clean_dna_for_llm(inputs['voice_dna'])}

                        3. VISUALS
                        - Primary: {p_p}
                        - Secondary: {p_s}
                        - Accents: {p_a}

                        [VISUAL SAMPLES & ASSETS]
                        {clean_dna_for_llm(inputs['visual_dna'])}

                        4. GUARDRAILS
                        - {new_guard}
                        {build_mh_context(profile_obj['inputs'])}
                        5. SOCIAL SAMPLES (CALIBRATION DATA)
                        {clean_dna_for_llm(inputs['social_dna'])}
                        """
                        
                        profile_obj['final_text'] = new_text
                        st.session_state['profiles'][target] = profile_obj
                        
                        # 4. DB Commit
                        db.save_profile(st.session_state['user_id'], target, profile_obj)

                        # LOG STRATEGY UPDATE
                        db.log_event(
                            org_id=st.session_state.get('org_id', 'Unknown'),
                            username=st.session_state.get('username', 'Unknown'),
                            activity_type="STRATEGY UPDATE",
                            asset_name=target,
                            score=profile_obj.get('calibration_score', 0),
                            verdict="REFINED",
                            metadata={"name": new_name, "arch": new_arch}
                        )

                        # Analytics: strategy updated + calibration + message house milestone
                        _pa_u = st.session_state.get('username', '')
                        _pa_sid = st.session_state.get('_analytics_session_id')
                        _pa_org = st.session_state.get('org_id')
                        _new_score = profile_obj.get('calibration_score', 0)
                        _old_score = st.session_state.get('_last_cal_score', 0)
                        db.track_event("strategy_updated", _pa_u,
                                       metadata={"field": "strategy_save"},
                                       session_id=_pa_sid, org_id=_pa_org)
                        # Check message house milestone
                        _mh_check = [profile_obj['inputs'].get('mh_brand_promise'),
                                     profile_obj['inputs'].get('mh_pillars_json'),
                                     profile_obj['inputs'].get('mh_boilerplate')]
                        if any(_mh_check):
                            db.check_milestone(_pa_u, "message_house_started",
                                               session_id=_pa_sid, org_id=_pa_org)
                        if _new_score != _old_score:
                            db.track_event("calibration_change", _pa_u,
                                           metadata={"old_score": _old_score, "new_score": _new_score, "trigger": "strategy_updated"},
                                           session_id=_pa_sid, org_id=_pa_org)
                            if _new_score >= 60 and _old_score < 60:
                                db.check_milestone(_pa_u, "calibration_crossed_60", session_id=_pa_sid, org_id=_pa_org)
                            if _new_score >= 90 and _old_score < 90:
                                db.check_milestone(_pa_u, "calibration_crossed_90", session_id=_pa_sid, org_id=_pa_org)
                        st.session_state['_last_cal_score'] = _new_score

                        st.success(f"Strategy Saved. Calibration Score: {profile_obj.get('calibration_score', 0)}%")
                        st.rerun()

                else:
                    st.warning("This profile was created from a PDF/Raw Text. Structured editing is unavailable.")
                    new_raw = st.text_area("EDIT RAW TEXT", final_text_view, height=500, max_chars=20000)
                    if st.button("SAVE RAW CHANGES", disabled=_ba_trial_readonly):
                        st.session_state['profiles'][target] = new_raw
                        db.save_profile(st.session_state['user_id'], target, new_raw)

                        # LOG RAW EDIT
                        db.log_event(
                            org_id=st.session_state.get('org_id', 'Unknown'),
                            username=st.session_state.get('username', 'Unknown'),
                            activity_type="STRATEGY UPDATE",
                            asset_name=target,
                            score=0,
                            verdict="RAW EDIT",
                            metadata={"type": "raw_text_override"}
                        )
                        st.success("SAVED")

                if st.button("DELETE PROFILE"): 
                    del st.session_state['profiles'][target]
                    db.delete_profile(st.session_state['user_id'], target)

                    # LOG DELETION
                    db.log_event(
                        org_id=st.session_state.get('org_id', 'Unknown'),
                        username=st.session_state.get('username', 'Unknown'),
                        activity_type="PROFILE DELETED",
                        asset_name=target,
                        score=0,
                        verdict="DESTROYED",
                        metadata={}
                    )
                    st.rerun()
    
    # -----------------------------------------------------------
    # TAB 3: IMPORT BRAND FROM PDF (THE PDF INGESTOR)
    # -----------------------------------------------------------
    with main_tab3:
        st.markdown("### AUTO-FILL FROM GUIDELINES")
        st.caption("Upload a PDF to automatically populate the Brand Identity fields.")
        
        # The uploader needs the key match the callback
        st.file_uploader("UPLOAD BRAND GUIDE", type=["pdf"], key="arch_pdf_uploader")
        
        # The button simply triggers the callback
        st.button("EXTRACT & MAP TO BRAND", type="primary", on_click=extract_and_map_pdf, disabled=_ba_trial_readonly)
    
        # Display Messages based on the flags set in callback
        if st.session_state.get('extraction_success'):
            st.success("Extraction complete. Switch to the BUILD NEW BRAND tab to review.")
            # Clear flag so it doesn't stay forever
            st.session_state['extraction_success'] = False
        
        if st.session_state.get('extraction_error'):
            st.error(f"Extraction Error: {st.session_state['extraction_error']}")
            st.session_state['extraction_error'] = None
                
# ===================================================================
# TEAM MANAGEMENT MODULE 
# ===================================================================

if app_mode == "TEAM MANAGEMENT":
    st.title("TEAM MANAGEMENT")
    
    # Check permissions
    current_username = st.session_state.get('username', 'Unknown')
    current_email = st.session_state.get('email', '')
    is_admin = st.session_state.get('is_admin', False)
    
    # CASE INSENSITIVE CHECK for God Mode User
    is_god_mode = (current_username.lower() == "nick_admin")
    
    if not is_admin and not is_god_mode:
        st.error("ACCESS DENIED. This area is restricted to Organization Admins.")
        st.stop()
        
    current_org = st.session_state.get('org_id', 'Unknown')
    
    # Get subscription status
    user_status = db.get_user_status(current_username)
    
    # --- GOD MODE OVERRIDE ---
    if is_god_mode:
        user_status = "unlimited"
        max_seats = 99999
    else:
        # Standard Limits
        seat_limits = {
            "trial": 1,
            "solo": 1,
            "agency": 5,
            "enterprise": 20
        }
        max_seats = seat_limits.get(user_status, 1)
    
    st.markdown(f"**ORGANIZATION:** {current_org}")
    st.markdown(f"**SUBSCRIPTION TIER:** {user_status.upper()}")
    st.divider()
    
    # Get current team members
    users = db.get_users_by_org(current_org)
    current_seats = len(users) if users else 0
    
    # --- SEAT USAGE INDICATOR ---
    if is_god_mode:
         st.markdown(f"### SEAT USAGE: {current_seats} / ∞ (GOD MODE)")
    else:
         st.markdown(f"### SEAT USAGE: {current_seats} / {max_seats}")
    
    # Visual progress bar
    if is_god_mode or max_seats > 1000:
        usage_pct = 1 # Just show a sliver for unlimited
        bar_color = "#5c6b61" # Green
        display_text = "UNLIMITED ACCESS"
    else:
        usage_pct = (current_seats / max_seats) * 100 if max_seats > 0 else 0
        display_text = f"{current_seats} / {max_seats} SEATS"
        
        if usage_pct < 70:
            bar_color = "#5c6b61"  # Green
        elif usage_pct < 90:
            bar_color = "#eeba2b"  # Orange
        else:
            bar_color = "#bd0000"  # Red
    
    st.markdown(f"""
    <div style='background: rgba(27, 42, 46, 0.6); height: 30px; border: 1px solid #5c6b61; position: relative;'>
        <div style='background: {bar_color}; height: 100%; width: {usage_pct}%;'></div>
        <div style='position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                    color: #f5f5f0; font-weight: 700; font-size: 0.85rem;'>
            {display_text}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='margin-bottom: 30px;'></div>", unsafe_allow_html=True)
    
    # --- TWO COLUMN LAYOUT ---
    col_team, col_actions = st.columns([2.5, 1.5])
    
    # ========================================
    # LEFT: TEAM ROSTER
    # ========================================
    with col_team:
        st.markdown("### TEAM ROSTER")
        
        if users:
            import pandas as pd
            df = pd.DataFrame(users, columns=["USERNAME", "EMAIL", "IS_ADMIN", "CREATED_AT"])
            
            # Format role column
            df['ROLE'] = df['IS_ADMIN'].apply(lambda x: "ADMIN" if x else "MEMBER")
            df = df[["USERNAME", "EMAIL", "ROLE", "CREATED_AT"]]
            
            st.dataframe(df, hide_index=True, use_container_width=True)
            
            # --- ACTION BUTTONS FOR EACH USER ---
            st.markdown("### MANAGE MEMBERS")
            
            for idx, user in enumerate(users):
                username = user[0]
                email = user[1]
                is_user_admin = bool(user[2])
                
                # Skip current user (can't manage yourself)
                if username == current_username:
                    st.info(f"**{username}** (You) - Cannot manage your own account")
                    continue
                
                with st.expander(f"**{username}** ({email})"):
                    action_col1, action_col2, action_col3 = st.columns(3)
                    
                    # Promote/Demote
                    with action_col1:
                        if is_user_admin:
                            # Check if this is the last admin
                            admin_count = sum(1 for u in users if u[2])
                            if admin_count <= 1:
                                st.warning("Cannot demote last admin")
                            else:
                                if st.button(f"Demote to Member", key=f"demote_{idx}"):
                                    db.update_user_fields(username, is_admin=False)
                                    st.success(f"{username} demoted to Member")
                                    st.rerun()
                        else:
                            if st.button(f"Promote to Admin", key=f"promote_{idx}"):
                                db.update_user_fields(username, is_admin=True)
                                st.success(f"{username} promoted to Admin")
                                st.rerun()
                    
                    # Reset Password
                    with action_col2:
                        if st.button(f"Reset Password", key=f"reset_{idx}"):
                            st.session_state[f'reset_password_for_{username}'] = True
                        
                        if st.session_state.get(f'reset_password_for_{username}', False):
                            new_pass = st.text_input(f"New temp password for {username}", type="password", key=f"newpw_{idx}")
                            if st.button(f"Confirm Reset", key=f"confirm_reset_{idx}"):
                                if new_pass:
                                    db.reset_user_password(username, new_pass)
                                    st.success(f"Password reset for {username}")
                                    st.session_state[f'reset_password_for_{username}'] = False
                                    st.rerun()
                                else:
                                    st.warning("Enter new password")
                    
                    # Remove User
                    with action_col3:
                        if st.button(f"Remove User", key=f"remove_{idx}", type="secondary"):
                            st.session_state[f'confirm_remove_{username}'] = True
                        
                        if st.session_state.get(f'confirm_remove_{username}', False):
                            st.warning(f"Confirm removal of {username}?")
                            conf_col1, conf_col2 = st.columns(2)
                            with conf_col1:
                                if st.button("Yes, Remove", key=f"yes_remove_{idx}"):
                                    db.delete_user_full(username)
                                    st.success(f"{username} removed from organization")
                                    st.session_state[f'confirm_remove_{username}'] = False
                                    st.rerun()
                            with conf_col2:
                                if st.button("Cancel", key=f"cancel_remove_{idx}"):
                                    st.session_state[f'confirm_remove_{username}'] = False
                                    st.rerun()
        else:
            st.info("No team members found. Start by adding a user.")
    
    # ========================================
    # RIGHT: ADD NEW MEMBER
    # ========================================
    with col_actions:
        st.markdown("### ADD TEAM MEMBER")
        
        # Check if seats available
        if current_seats >= max_seats:
            st.error("SEAT LIMIT REACHED")
            st.markdown(f"Your {user_status.upper()} tier allows {max_seats} seat(s).")
            st.markdown("Upgrade your subscription to add more team members.")
        else:
            if is_god_mode:
                 st.info(f"UNLIMITED seats available")
            else:
                 seats_remaining = max_seats - current_seats
                 st.info(f"{seats_remaining} seat(s) available")
            
            with st.form("add_team_member"):
                new_user = st.text_input("USERNAME", max_chars=64)
                new_email = st.text_input("EMAIL", max_chars=120)
                new_pass = st.text_input("TEMP PASSWORD", type="password", max_chars=64)
                make_admin = st.checkbox("Grant Admin Access")
                submitted = st.form_submit_button("CREATE SEAT", use_container_width=True)
                
                if submitted:
                    if new_user and new_pass and new_email:
                        # Validate email format (basic)
                        if "@" not in new_email or "." not in new_email:
                            st.error("Invalid email format")
                        else:
                            # CREATE USER LINKED TO CURRENT ORG
                            if db.create_user(new_user, new_email, new_pass, org_id=current_org, is_admin=make_admin):
                                role = "Admin" if make_admin else "Member"
                                st.success(f"✓ {new_user} added as {role}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("Failed: Username exists OR seat limit reached")
                    else:
                        st.warning("All fields required")
        
        st.markdown("---")
        st.markdown("### SUBSCRIPTION INFO")
        tier_info = {
            "trial": "1 seat, limited features",
            "solo": "1 seat, full platform",
            "agency": "5 seats, team features",
            "enterprise": "20 seats, premium support",
            "unlimited": "Unlimited seats, God Mode"
        }
        st.caption(f"**{user_status.upper()}:** {tier_info.get(user_status, 'Contact support')}")
        
        if st.button("Manage Subscription", use_container_width=True):
            st.session_state['app_mode'] = "SUBSCRIPTION"
            st.rerun()

# ===================================================================
# END OF TEAM MANAGEMENT MODULE
# ===================================================================

# ===================================================================
# SUBSCRIPTION MANAGEMENT PAGE
# ===================================================================

elif app_mode == "SUBSCRIPTION":
    st.markdown("<h1 style='color:#ab8f59;'>SUBSCRIPTION</h1>", unsafe_allow_html=True)
    _sub_user = st.session_state.get('username', '')
    _sub_tier = st.session_state.get('tier', {})
    _sub_tier_key = _sub_tier.get('_tier_key', 'solo')
    _sub_status = _sub_tier.get('_subscription_status', 'inactive')
    _sub_is_trial = _sub_tier.get('_is_trial', False)
    _sub_trial_days = _sub_tier.get('_trial_days_remaining', 0)
    _sub_email = ''
    _sub_user_data = db.get_user_full(_sub_user)
    if _sub_user_data:
        _sub_email = _sub_user_data.get('email', '')

    # Current plan display
    if _sub_is_trial:
        st.markdown(f"""
            <div style="background:rgba(171,143,89,0.08); border:1px solid #ab8f59; padding:20px;
                        border-radius:4px; margin-bottom:20px;">
                <div style="font-weight:800; color:#24363b; font-size:1.1rem; letter-spacing:0.05em;">FREE TRIAL</div>
                <div style="color:#3d3d3d; margin-top:8px; font-size:0.9rem;">{_sub_trial_days} days remaining</div>
                <div style="color:#5c6b61; margin-top:4px; font-size:0.8rem;">
                    Full access to all modules with the sample brand. Subscribe to use your own brands.
                </div>
            </div>
        """, unsafe_allow_html=True)
    elif _sub_status == 'active':
        _sub_display = _sub_tier.get('display_name', 'Solo')
        _sub_price = _sub_tier.get('price_monthly_usd', 0)
        st.markdown(f"""
            <div style="background:rgba(36,54,59,0.05); border:1px solid #24363b; padding:20px;
                        border-radius:4px; margin-bottom:20px;">
                <div style="font-weight:800; color:#24363b; font-size:1.1rem; letter-spacing:0.05em;">{_sub_display.upper()} PLAN</div>
                <div style="color:#3d3d3d; margin-top:8px; font-size:0.9rem;">${_sub_price}/month</div>
                <div style="color:#5c6b61; margin-top:4px; font-size:0.8rem;">Status: Active</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="background:#f5f5f0; border:1px solid #ab8f59; padding:20px;
                        border-radius:4px; margin-bottom:20px;">
                <div style="font-weight:800; color:#24363b; font-size:1.1rem; letter-spacing:0.05em;">NO ACTIVE SUBSCRIPTION</div>
                <div style="color:#3d3d3d; margin-top:8px; font-size:0.85rem;">
                    Your brand data is safe. Subscribe to resume full access.
                </div>
            </div>
        """, unsafe_allow_html=True)

    # Usage info
    _sub_usage = st.session_state.get('usage', {})
    if _sub_usage.get('limit', 0) > 0:
        _used = _sub_usage.get('used', 0)
        _limit = _sub_usage.get('limit', 0)
        _pct = _sub_usage.get('percentage', 0)
        st.markdown(f"**Usage this month:** {_used} / {_limit} actions ({_pct:.0f}%)")
        st.progress(min(_pct / 100, 1.0))
    st.markdown("---")

    # Plan comparison / subscribe buttons
    st.markdown("### CHOOSE YOUR PLAN")
    from tier_config import TIER_CONFIG
    _plan_cols = st.columns(3)
    for idx, (tk, tc) in enumerate([("solo", TIER_CONFIG["solo"]), ("agency", TIER_CONFIG["agency"]), ("enterprise", TIER_CONFIG["enterprise"])]):
        with _plan_cols[idx]:
            _is_current = (tk == _sub_tier_key and _sub_status == 'active')
            _border = "#ab8f59" if _is_current else "#c0c0c0"
            _badge = " (CURRENT)" if _is_current else ""
            st.markdown(f"""
                <div style="font-family:'Montserrat',sans-serif; border:2px solid {_border}; padding:20px; border-radius:4px; text-align:center; min-height:280px; background-color:#f5f5f0;">
                    <div style="font-weight:800; color:#24363b; font-size:1rem; letter-spacing:0.05em;">{tc['display_name'].upper()}{_badge}</div>
                    <div style="font-size:1.3rem; font-weight:700; color:#24363b; margin:12px 0;">${tc['price_monthly_usd']}<span style="font-size:0.8rem; color:#5c6b61;">/mo</span></div>
                    <div style="text-align:left; font-size:0.8rem; color:#3d3d3d; line-height:1.8;">
                        {'Unlimited' if tc['max_brands'] == -1 else tc['max_brands']} brands<br>
                        {tc['max_seats']} seat{'s' if tc['max_seats'] > 1 else ''}<br>
                        {tc['monthly_ai_actions']} AI actions/mo
                    </div>
                </div>
            """, unsafe_allow_html=True)
            if not _is_current and not _is_super_admin():
                _checkout_url = sub_manager.get_checkout_url(tk, _sub_user, _sub_email)
                if _checkout_url:
                    st.markdown(f"""
                        <div style="text-align:center; margin-top:12px;">
                            <a href="{_checkout_url}" target="_blank" style="
                                display:inline-block; background-color:#ab8f59; color:#1b2a2e;
                                padding:10px 24px; text-decoration:none; font-weight:700;
                                font-size:0.8rem; letter-spacing:0.08em; text-transform:uppercase;
                            ">SUBSCRIBE</a>
                        </div>
                    """, unsafe_allow_html=True)

    # Manage existing subscription
    if _sub_status == 'active' and not _sub_is_trial and _sub_tier_key not in ('super_admin', 'retainer'):
        st.markdown("---")
        st.markdown("### MANAGE SUBSCRIPTION")
        _portal_url = sub_manager.get_customer_portal_url(_sub_user)
        if _portal_url:
            st.markdown(f"""
                <a href="{_portal_url}" target="_blank" style="
                    display:inline-block; background-color:#24363b; color:#f5f5f0;
                    padding:10px 24px; text-decoration:none; font-weight:700;
                    font-size:0.8rem; letter-spacing:0.08em; text-transform:uppercase;
                ">MANAGE BILLING</a>
            """, unsafe_allow_html=True)
            st.caption("Update payment method, view invoices, or cancel your subscription.")
        else:
            st.caption("Contact support@castellanpr.com to manage your subscription.")

    # Manual sync option
    st.markdown("---")
    if st.button("SYNC SUBSCRIPTION STATUS"):
        import time as _sync_t
        st.session_state.pop('_tier_resolved_at', None)
        _new_tier = sub_manager.resolve_user_tier(_sub_user)
        st.session_state['tier'] = _new_tier
        st.session_state['subscription_status'] = _new_tier.get('_subscription_status', 'inactive')
        st.session_state['status'] = st.session_state['subscription_status']
        st.session_state['_tier_resolved_at'] = _sync_t.time()
        st.session_state['usage'] = sub_manager.check_usage_limit(_sub_user)
        st.success("Subscription status synced.")
        _sync_t.sleep(1.5)
        st.rerun()


# ===================================================================
# FULL ACTIVITY LOG MODULE
# ===================================================================

elif app_mode == "ACTIVITY LOG":
    st.title("ACTIVITY LOG")
    
    current_org = st.session_state.get('org_id')
    username = st.session_state.get('username')
    is_admin = st.session_state.get('is_admin', False)
    
    st.markdown(f"**ORGANIZATION:** {current_org}")
    if is_admin:
        st.caption("Admin view: Showing all organization activity")
    else:
        st.caption("User view: Showing your activity only")
    
    st.divider()
    
    # --- FILTERS ---
    filter_col1, filter_col2, filter_col3 = st.columns(3)
    
    with filter_col1:
        limit = st.selectbox("ENTRIES TO SHOW", [20, 50, 100, 200], index=0)
    
    with filter_col2:
        activity_types = ["ALL", "VISUAL AUDIT", "COPY EDIT", "CONTENT GENERATION", 
                         "STRATEGY UPDATE", "PROFILE DELETED", "ASSET INJECTION"]
        filter_type = st.selectbox("ACTIVITY TYPE", activity_types)
    
    with filter_col3:
        if is_admin:
            # Get all users in org for filter
            users = db.get_users_by_org(current_org)
            user_list = ["ALL"] + [u[0] for u in users] if users else ["ALL"]
            filter_user = st.selectbox("USER", user_list)
        else:
            filter_user = username
    
    # --- FETCH LOGS ---
    try:
        logs = db.get_org_logs(current_org, limit=limit)
        
        # Apply filters
        if not is_admin:
            # Non-admins only see their own
            logs = [log for log in logs if log.get('username') == username]
        elif filter_user != "ALL":
            # Admin filtered by specific user
            logs = [log for log in logs if log.get('username') == filter_user]
        
        if filter_type != "ALL":
            logs = [log for log in logs if log.get('activity_type') == filter_type]
        
        if logs:
            st.markdown(f"**SHOWING {len(logs)} ENTRIES**")
            st.markdown("---")

            # Build HTML table (selectable text, brand-styled)
            _rows_html = ""
            for i, log in enumerate(logs):
                asset_raw = log.get('asset_name', '')
                asset_display = (asset_raw[:30] + "...") if len(asset_raw) > 30 else asset_raw
                _rows_html += (
                    f"<tr>"
                    f"<td>{log.get('timestamp', '')}</td>"
                    f"<td>{log.get('username', '')}</td>"
                    f"<td>{log.get('activity_type', '')}</td>"
                    f"<td>{asset_display}</td>"
                    f"<td>{log.get('score', '-')}</td>"
                    f"<td>{log.get('verdict', '')}</td>"
                    f"</tr>"
                )

            st.markdown(f"""
            <div style="overflow-x: auto; max-height: 500px; overflow-y: auto; border: 1px solid #5c6b61; border-radius: 2px;">
            <table class="activity-log-table">
                <thead><tr>
                    <th>TIME</th><th>USER</th><th>ACTIVITY</th>
                    <th>ASSET</th><th>SCORE</th><th>VERDICT</th>
                </tr></thead>
                <tbody>{_rows_html}</tbody>
            </table>
            </div>
            """, unsafe_allow_html=True)

            # --- DETAIL VIEW (selectbox-driven) ---
            st.markdown("---")
            st.markdown("### ENTRY DETAILS")

            detail_options = [
                f"{i+1}. {log.get('activity_type', '')} — {log.get('asset_name', '')[:40]}"
                for i, log in enumerate(logs)
            ]
            selected_idx = st.selectbox(
                "SELECT ENTRY", range(len(detail_options)),
                format_func=lambda i: detail_options[i],
                key="activity_log_detail_select"
            )

            selected_log = logs[selected_idx]
            _activity = selected_log.get('activity_type', '')

            # -- Header row --
            st.markdown(f"""
            <div style="display:flex; justify-content:space-between; align-items:center;
                        padding:12px 16px; background:rgba(27,42,46,0.6);
                        border-left:3px solid #ab8f59; margin-bottom:16px;">
                <span style="font-weight:700; color:#ab8f59; letter-spacing:0.05em;">{_activity}</span>
                <span style="color:#5c6b61; font-size:0.8rem;">{selected_log.get('timestamp', '')} &middot; {selected_log.get('username', '')}</span>
            </div>
            """, unsafe_allow_html=True)

            # -- Parse metadata --
            try:
                metadata = json.loads(selected_log.get('metadata_json', '{}'))
            except:
                metadata = {}

            _asset = selected_log.get('asset_name', '')
            _score = selected_log.get('score', '-')
            _verdict = selected_log.get('verdict', '')

            # -- Render per activity type --
            if _activity == "VISUAL AUDIT":
                _scores = metadata.get('scores', {})
                _summary = metadata.get('summary', '')
                st.markdown(f"**Asset:** {_asset}")
                sc1, sc2, sc3, sc4 = st.columns(4)
                with sc1: st.metric("OVERALL", _score)
                with sc2: st.metric("COLOR", _scores.get('color', '-'))
                with sc3: st.metric("VISUAL", _scores.get('visual', '-'))
                with sc4: st.metric("COPY", _scores.get('copy', '-'))
                st.markdown(f"**Verdict:** {_verdict}")
                if _summary:
                    st.markdown(f"**Summary:** {_summary}")

            elif _activity == "COPY EDIT":
                st.markdown(f"**Asset:** {_asset} &nbsp;|&nbsp; **Score:** {_score} &nbsp;|&nbsp; **Verdict:** {_verdict}")
                _draft = metadata.get('draft', '')
                _rewrite = metadata.get('rewrite', '')
                _rationale = metadata.get('rationale', '')
                if _draft:
                    with st.expander("ORIGINAL DRAFT", expanded=False):
                        st.text(_draft[:2000])
                if _rewrite:
                    with st.expander("REWRITTEN OUTPUT", expanded=True):
                        st.markdown(_rewrite[:2000])
                if _rationale:
                    with st.expander("RATIONALE", expanded=False):
                        st.markdown(_rationale[:2000])

            elif _activity in ("GENERATOR", "CONTENT GENERATION"):
                _topic = metadata.get('topic', '')
                _key_points = metadata.get('key_points', '')
                _draft = metadata.get('draft', '')
                _rationale = metadata.get('rationale', '')
                st.markdown(f"**Topic:** {_topic}")
                if _key_points:
                    st.markdown(f"**Key Points:** {_key_points}")
                if _draft:
                    with st.expander("GENERATED CONTENT", expanded=True):
                        st.markdown(_draft[:3000])
                if _rationale:
                    with st.expander("RATIONALE", expanded=False):
                        st.markdown(_rationale[:2000])

            elif _activity in ("SOCIAL GEN", "SOCIAL GENERATION"):
                _platform = metadata.get('platform', '')
                _goal = metadata.get('goal', '')
                _topic = metadata.get('topic', '')
                _options = metadata.get('options', [])
                st.markdown(f"**Platform:** {_platform} &nbsp;|&nbsp; **Goal:** {_goal}")
                if _topic:
                    st.markdown(f"**Topic:** {_topic}")
                if _options:
                    for j, opt in enumerate(_options):
                        with st.expander(f"OPTION {j+1}", expanded=(j == 0)):
                            if isinstance(opt, dict):
                                st.markdown(opt.get('content', opt.get('text', str(opt))))
                            else:
                                st.markdown(str(opt))

            elif _activity == "STRATEGY UPDATE":
                _name = metadata.get('name', '')
                _arch = metadata.get('arch', '')
                _stype = metadata.get('type', '')
                st.markdown(f"**Asset:** {_asset} &nbsp;|&nbsp; **Verdict:** {_verdict}")
                if _name:
                    st.markdown(f"**Profile:** {_name}")
                if _stype:
                    st.markdown(f"**Type:** {_stype}")
                if _arch:
                    with st.expander("UPDATED CONTENT", expanded=False):
                        st.text(_arch[:2000])

            elif _activity in ("ASSET INJECTION", "ASSET DELETED"):
                _dtype = metadata.get('type', '')
                _content = metadata.get('content', '')
                st.markdown(f"**Asset:** {_asset} &nbsp;|&nbsp; **Type:** {_dtype} &nbsp;|&nbsp; **Verdict:** {_verdict}")
                if _content:
                    st.markdown(f"**Preview:** {_content}")

            elif _activity in ("PROFILE CREATED", "PROFILE DELETED"):
                _method = metadata.get('method', '')
                st.markdown(f"**Asset:** {_asset} &nbsp;|&nbsp; **Verdict:** {_verdict}")
                if _method:
                    st.markdown(f"**Method:** {_method}")

            else:
                # Fallback: show structured metadata
                st.markdown(f"**Asset:** {_asset} &nbsp;|&nbsp; **Score:** {_score} &nbsp;|&nbsp; **Verdict:** {_verdict}")
                if metadata:
                    with st.expander("RAW METADATA", expanded=True):
                        st.json(metadata)
        
        else:
            st.warning("No activity logs found matching your filters")
    
    except Exception as e:
        st.error(f"Error loading activity logs: {e}")
    
    # --- EXPORT OPTION (Future Enhancement) ---
    st.markdown("---")
    if st.button("EXPORT TO CSV"):
        st.info("Export functionality: Coming in next update")

# ===================================================================
# END OF ACTIVITY LOG MODULE
# ===================================================================

# --- ADMIN DASHBOARD (GOD MODE) ---
if st.session_state.get("authenticated") and st.session_state.get("is_admin"):
    st.markdown("---")
    with st.expander("GOD MODE: SYSTEM OVERVIEW"):
        # Custom CSS for the Admin Panel to match the Theme
        st.markdown("""
        <style>
            /* Style the Metrics */
            div[data-testid="stMetricValue"] {
                color: #ab8f59 !important;
                -webkit-text-fill-color: #ab8f59 !important;
                font-family: 'Montserrat', 'Helvetica Neue', Arial, sans-serif !important;
            }
            div[data-testid="stMetricLabel"] {
                color: #5c6b61 !important;
                -webkit-text-fill-color: #5c6b61 !important;
            }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("<h3 style='color: #ab8f59; letter-spacing: 0.1em;'>GLOBAL SYSTEM STATUS</h3>", unsafe_allow_html=True)
        
        # 1. METRICS ROW
        _gs_conn = db._get_connection()
        try:
            user_count = db._fetchone_val(db._execute_plain(_gs_conn, "SELECT COUNT(*) FROM users"), 0)
            org_count = db._fetchone_val(db._execute_plain(_gs_conn, "SELECT COUNT(DISTINCT org_id) FROM users"), 0)
            log_count = db._fetchone_val(db._execute_plain(_gs_conn, "SELECT COUNT(*) FROM activity_log"), 0)

            _gs_users_raw = db._execute_plain(
                _gs_conn, "SELECT username, email, org_id, is_admin, created_at FROM users").fetchall()
            _gs_users = [db._dict_row(r) for r in _gs_users_raw]

            _gs_logs_raw = db._execute_plain(
                _gs_conn, "SELECT timestamp, org_id, username, activity_type, asset_name, verdict, metadata_json FROM activity_log ORDER BY id DESC LIMIT 100").fetchall()
            _gs_logs = [db._dict_row(r) for r in _gs_logs_raw]
        finally:
            _gs_conn.close()

        # Global Counts
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("TOTAL USERS", user_count)
        with m2: st.metric("ACTIVE ORGANIZATIONS", org_count)
        with m3: st.metric("TOTAL ACTIONS LOGGED", log_count)

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. TABS FOR DATA
        tab_users, tab_logs = st.tabs(["GLOBAL USER DATABASE", "GLOBAL AUDIT LOGS"])

        import pandas as pd

        with tab_users:
            if _gs_users:
                _u_rows = ""
                for row in _gs_users:
                    role = "ADMIN" if row['is_admin'] else "USER"
                    _u_rows += f"<tr><td>{row['username']}</td><td>{row['email']}</td><td>{row['org_id']}</td><td>{role}</td><td>{row['created_at']}</td></tr>"
                st.markdown(f"""
                <div style="overflow-x:auto; max-height:400px; overflow-y:auto; border:1px solid #5c6b61;">
                <table class="activity-log-table">
                    <thead><tr><th>USERNAME</th><th>EMAIL</th><th>ORG_ID</th><th>ROLE</th><th>CREATED_AT</th></tr></thead>
                    <tbody>{_u_rows}</tbody>
                </table></div>
                """, unsafe_allow_html=True)
            else:
                st.info("No users found.")

        with tab_logs:
            if _gs_logs:
                _l_rows = ""
                for row in _gs_logs:
                    _l_rows += f"<tr><td>{row['timestamp']}</td><td>{row['org_id']}</td><td>{row['username']}</td><td>{row['activity_type']}</td><td>{row['verdict']}</td></tr>"
                st.markdown(f"""
                <div style="overflow-x:auto; max-height:400px; overflow-y:auto; border:1px solid #5c6b61;">
                <table class="activity-log-table">
                    <thead><tr><th>TIME</th><th>ORG</th><th>USER</th><th>ACTION</th><th>VERDICT</th></tr></thead>
                    <tbody>{_l_rows}</tbody>
                </table></div>
                """, unsafe_allow_html=True)

                # Detail View (The Inspector)
                st.markdown("<h5 style='color: #ab8f59; margin-top: 20px;'>DEEP INSPECTOR</h5>", unsafe_allow_html=True)
                _log_options = [
                    f"{i+1}. {row['activity_type']} — {row['username']} ({str(row['timestamp'])[:16]})"
                    for i, row in enumerate(_gs_logs)
                ]
                _sel_idx = st.selectbox(
                    "SELECT ENTRY", range(len(_log_options)),
                    format_func=lambda i: _log_options[i],
                    key="godmode_log_detail_select"
                )
                _sel_row = _gs_logs[_sel_idx]
                c_meta, c_raw = st.columns(2)
                with c_meta:
                    st.caption("ACTION METADATA")
                    st.write(f"**Org:** {_sel_row['org_id']}")
                    st.write(f"**User:** {_sel_row['username']}")
                    st.write(f"**Asset:** {_sel_row['asset_name']}")
                with c_raw:
                    st.caption("PAYLOAD (JSON)")
                    try:
                        st.json(_sel_row['metadata_json'])
                    except:
                        st.code(_sel_row['metadata_json'])
            else:
                st.info("No global logs generated yet.")

# --- FOOTER ---
st.markdown("""<div class="footer">POWERED BY CASTELLAN PR</div>""", unsafe_allow_html=True)







































