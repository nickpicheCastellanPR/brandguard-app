import streamlit as st
from PIL import Image
import os
import re
import json
import sqlite3
import time # Added for Session Expiry
from logic import SignetLogic
import db_manager as db
import subscription_manager as sub_manager
import html

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
        font-family: 'Helvetica Neue', sans-serif !important;
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
        font-family: 'Helvetica Neue', sans-serif;
        font-weight: 800 !important;
        text-transform: uppercase;
        color: var(--c-cream) !important;
        padding-bottom: 15px;
        border-bottom: 1px solid var(--c-gold-muted);
        letter-spacing: 0.05em;
    }
    
    h2, h3 { color: var(--c-gold-muted) !important; text-transform: uppercase; font-weight: 700; }

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

    /* 6. BUTTONS (GLOBAL) */
    .stButton button {
        background-color: transparent !important;
        border: 1px solid var(--c-gold-muted) !important;
        color: var(--c-gold-muted) !important;
        border-radius: 0px !important;
        font-weight: 700 !important;
        text-transform: uppercase;
        letter-spacing: 0.15em;
        transition: all 0.2s;
        padding: 0.6rem 1.2rem;
    }
    .stButton button:hover {
        background-color: var(--c-gold-muted) !important;
        color: var(--c-teal-deep) !important;
        box-shadow: 0 0 15px rgba(171, 143, 89, 0.4);
        transform: translateY(-1px);
    }
    button[kind="primary"] {
        background: var(--c-gold-muted) !important;
        color: var(--c-teal-deep) !important;
        border: none !important;
    }
    
    /* Red delete button override */
    button[kind="secondary"] {
        border-color: #ff5f56 !important;
        color: #ff5f56 !important;
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
    
    /* CLEANUP */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
</style>
""", unsafe_allow_html=True)

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

init_wizard_state()

if 'profiles' not in st.session_state: st.session_state['profiles'] = {}
if 'nav_selection' not in st.session_state: st.session_state['nav_selection'] = "DASHBOARD"

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
    Advanced 'Cluster Density' Scoring.
    Total = 100.
    - Strategy: 20
    - Visuals: 15
    - Social: 15
    - Voice Clusters: 50 (10 pts per fortified cluster)
    """
    score = 0
    breakdown = []
    
    # CASE A: STRUCTURED DATA
    if isinstance(profile_data, dict) and 'inputs' in profile_data:
        inputs = profile_data['inputs']
        
        # 1. STRATEGY (20 PTS)
        strat_score = 0
        if inputs.get('wiz_mission'): strat_score += 5
        if inputs.get('wiz_values'): strat_score += 5
        if inputs.get('wiz_guardrails'): strat_score += 5
        if inputs.get('wiz_archetype'): strat_score += 5
        score += strat_score

        # 2. VISUALS (15 PTS)
        vis_score = 0
        if inputs.get('palette_primary'): vis_score += 5
        # Count Visual Assets
        v_blob = inputs.get('visual_dna', '')
        if "[ASSET:" in v_blob: vis_score += 10
        score += vis_score

        # 3. SOCIAL (15 PTS)
        soc_score = 0
        s_blob = inputs.get('social_dna', '')
        s_count = s_blob.count("[ASSET:")
        if s_count >= 3: soc_score = 15
        elif s_count >= 1: soc_score = 5
        score += soc_score

        # 4. VOICE CLUSTERS (50 PTS - The Heavy Lifting)
        # We define the 5 specific keys we are looking for
        voice_blob = inputs.get('voice_dna', '')
        clusters = {
            "Corporate": "Corporate Affairs",
            "Crisis": "Crisis & Response",
            "Internal": "Internal Leadership",
            "Thought": "Thought Leadership",
            "Marketing": "Brand Marketing"
        }
        
        cluster_health = {}
        voice_score = 0
        
        for key, full_name in clusters.items():
            # Count occurrences of specific cluster headers
            count = voice_blob.upper().count(f"CLUSTER: {full_name.upper()}")
            
            if count >= 3:
                points = 10
                status = "FORTIFIED"
                icon = "✅"
            elif count >= 1:
                points = 3
                status = "UNSTABLE"
                icon = "⚠️"
            else:
                points = 0
                status = "EMPTY"
                icon = "❌"
            
            voice_score += points
            cluster_health[key] = {"count": count, "status": status, "icon": icon}
        
        score += voice_score

    # CASE B: LEGACY/PDF (Fallback)
    else:
        # Simple length check for unstructured data
        text_data = str(profile_data.get('final_text', '') if isinstance(profile_data, dict) else profile_data)
        score = min(len(text_data) // 50, 100) # 5000 chars = 100%
        cluster_health = {}

    # FINAL STATUS LABEL
    score = min(score, 100)
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
        "clusters": cluster_health
    }
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
    
    # --- TIER 1: HIGH RISK (Crisis, Press Release) ---
    # Strategy: Start at 0. Trust must be earned. Safety is paramount.
    if content_type in ["Crisis Statement", "Press Release"]:
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
        if content_type == "Crisis Statement" and ("crisis" in final_text or "statement" in final_text):
            score += 10
            assets_found.append("Crisis History")
        elif content_type == "Press Release" and ("press" in final_text or "release" in final_text):
            score += 10
            assets_found.append("Press History")
            
        # HARD CAP: If Guardrails are missing, cannot exceed 50%.
        if not inputs.get('wiz_guardrails'):
            score = min(score, 50)

    # --- TIER 2: STRATEGIC INTERNAL (Memo, Email) ---
    # Strategy: Start at 20. Needs Authority and Tone.
    elif content_type in ["Executive Memo", "Internal Email"]:
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
            body {{ font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; background-color: #f5f5f0; color: #24363b; padding: 40px; line-height: 1.6; }}
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
            <div class="subtitle">Brand Governance Profile</div>
            <div class="content">{content}</div>
            <div class="footer">GENERATED BY SIGNET // INTELLIGENT BRAND GOVERNANCE</div>
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

# --- LOGIN / AUTH SCREEN (HERO LAYOUT V3 - FIXED) ---
if not st.session_state['authenticated']:
    # 1. GLOBAL STYLES + LOGIN CARD CSS
    st.markdown("""<style>
        .stApp { 
            background-color: #f5f5f0 !important; 
            background-image: linear-gradient(rgba(36, 54, 59, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(36, 54, 59, 0.05) 1px, transparent 1px), radial-gradient(circle at 0% 0%, rgba(92, 107, 97, 0.5) 0%, rgba(92, 107, 97, 0.1) 40%, transparent 70%), radial-gradient(circle at 100% 100%, rgba(36, 54, 59, 0.4) 0%, rgba(36, 54, 59, 0.1) 40%, transparent 70%); 
            background-size: 40px 40px, 40px 40px, 100% 100%, 100% 100%; 
        } 
        section[data-testid="stSidebar"] { display: none; } 
        .stTextInput input { 
            background-color: #ffffff !important; 
            color: #24363b !important; 
            border: 1px solid #c0c0c0 !important; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.05); 
            -webkit-text-fill-color: #24363b !important; 
        } 
        .stTextInput input:focus { border-color: #24363b !important; }
        
        /* FIX: TARGET THE RIGHT COLUMN TO CREATE THE CARD LOOK WITHOUT HTML WRAPPERS */
        div[data-testid="column"]:nth-of-type(2) > div[data-testid="stVerticalBlock"] {
            background-color: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.08);
            border-top: 5px solid #24363b;
        }
        
        /* Base Geometric Bullet Style */
        .geo-bullet {
            display: inline-block;
            width: 12px; height: 12px;
            background-color: #ab8f59; /* Brand Gold */
            margin-right: 14px;
            vertical-align: middle;
            box-shadow: 0 0 0 2px #24363b; /* Subtle Teal Border */
            position: relative; top: -2px; 
        }
        .geo-circle  { border-radius: 50%; }
        .geo-diamond { transform: rotate(45deg); border-radius: 1px; }
        .geo-square  { border-radius: 2px; }
    </style>""", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    # 2. BALANCED COLUMNS
    c1, c2 = st.columns([1, 1], gap="large")
    
    # --- LEFT COLUMN: THE PITCH ---
    with c1:
        if os.path.exists("Signet_Logo_Color.png"):
            st.image("Signet_Logo_Color.png", width=180)
        else:
            st.markdown("<div style='font-size: 3rem; color: #24363b; font-weight: 800; letter-spacing: 0.15em;'>SIGNET</div>", unsafe_allow_html=True)
            
        st.markdown("""
            <div style='margin-top: 20px; color: #24363b;'>
                <h1 style='border: none; padding: 0; font-size: 2.5rem; line-height: 1.2; margin-bottom: 20px;'>
                    Protect your brand's <br><span style='color: #ab8f59;'>integrity at scale.</span>
                </h1>
                <p style='font-size: 1.1rem; line-height: 1.6; color: #5c6b61; font-family: sans-serif;'>
                    Signet is the intelligent governance engine that ensures every piece of content—from emails to social posts—aligns perfectly with your brand identity.
                </p>
                <ul style='list-style: none; padding: 0; margin-top: 30px; font-family: sans-serif; color: #3d3d3d; font-size: 1.05rem;'>
                    <li style='margin-bottom: 18px;'>
                        <span class="geo-bullet geo-circle"></span><strong>Strategic Alignment:</strong> Calibrate AI to your specific archetype.
                    </li>
                    <li style='margin-bottom: 18px;'>
                        <span class="geo-bullet geo-diamond"></span><strong>Visual Compliance:</strong> Audit assets against hex codes and logo rules.
                    </li>
                    <li style='margin-bottom: 18px;'>
                        <span class="geo-bullet geo-square"></span><strong>Perfect Copy:</strong> Rewrite drafts to match your executive voice.
                    </li>
                </ul>
            </div>
        """, unsafe_allow_html=True)

# --- RIGHT COLUMN: THE LOGIN ---
    with c2:
        st.markdown("<h4 style='text-align: center; color: #ab8f59; margin-bottom: 20px; letter-spacing: 2px;'>ACCESS TERMINAL</h4>", unsafe_allow_html=True)
        
        # --- NEW: SELF-SEALING ADMIN SETUP ---
        if db.get_user_count() == 0:
            st.warning("⚠️ SYSTEM RESET: CREATE ADMIN ACCOUNT")
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
                    
                    # 3. SYNC SUBSCRIPTION STATUS
                    user_email = user_data.get('email', '')
                    status = sub_manager.sync_user_status(user_data['username'], user_email)
                    st.session_state['status'] = status
                    
                    # 4. LOAD PROFILES & RERUN
                    st.session_state['profiles'] = db.get_profiles(user_data['username'])
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
        
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
                    st.success(f"Account created! You are the Admin of {r_org}. Please log in.")
                else:
                    st.error("Username already taken.")

    st.markdown("<br><div style='text-align: center; color: #ab8f59; font-size: 0.7rem; letter-spacing: 0.2em;'>CASTELLAN PR</div>", unsafe_allow_html=True)
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
            border: none !important;
            font-weight: 800 !important;
        }
        button[kind="primary"] p {
            color: #1b2a2e !important;
        }
        button[kind="primary"]:hover {
            background-color: #f0c05a !important;
            color: #1b2a2e !important;
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
        </style>
    """, unsafe_allow_html=True)

    # 1. BRANDING
    if os.path.exists("Signet_Logo_Color.png"):
        st.image("Signet_Logo_Color.png", use_container_width=True) 
    else:
        st.markdown('<div style="font-size: 2rem; color: #24363b; font-weight: 900; letter-spacing: 0.1em; text-align: center; margin-bottom: 20px;">SIGNET</div>', unsafe_allow_html=True)
    
    st.markdown('<div style="margin-bottom: 20px;"></div>', unsafe_allow_html=True)

    # 2. USER & STATUS BADGE
    raw_user = st.session_state.get('username', 'User').upper()
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
                
                st.markdown("---")
                
                # 2. System Capabilities (Instructional)
                st.markdown("<span style='color:#24363b; font-weight:800; font-size:0.75rem;'>SYSTEM CAPABILITIES:</span>", unsafe_allow_html=True)
                if score < 40:
                    st.markdown("<span style='color:#24363b; font-size:0.75rem;'>⚠️ **UNSAFE:** Engine relies on generic training. High risk of generic output.</span>", unsafe_allow_html=True)
                elif score < 90:
                    st.markdown("<span style='color:#24363b; font-size:0.75rem;'>⚠️ **PARTIAL:** Safe for fortified clusters (green) only. Verify output carefully.</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:#24363b; font-size:0.75rem;'>✅ **OPERATIONAL:** Engine is fully fortified across all domains.</span>", unsafe_allow_html=True)
                
                st.markdown("<div style='margin-bottom:8px'></div>", unsafe_allow_html=True)

                # 3. Next Step (Actionable)
                st.markdown("<span style='color:#24363b; font-weight:800; font-size:0.75rem;'>NEXT OBJECTIVE:</span>", unsafe_allow_html=True)
                # Find the first weak cluster
                weakest = next((k for k, v in cal_data['clusters'].items() if v['count'] < 3), None)
                if weakest:
                    needed = 3 - cal_data['clusters'][weakest]['count']
                    st.markdown(f"<span style='color:#24363b; font-size:0.75rem;'>Upload {needed} more **{weakest}** samples to fortify this cluster.</span>", unsafe_allow_html=True)
                else:
                    st.markdown("<span style='color:#24363b; font-size:0.75rem;'>System fully calibrated.</span>", unsafe_allow_html=True)

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
    st.button("BRAND MANAGER", width="stretch", on_click=set_page, args=("BRAND MANAGER",))
    st.button("TEAM MANAGEMENT", width="stretch", on_click=set_page, args=("TEAM MANAGEMENT",))
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

    if st.button("LOGOUT", width="stretch"):
        st.session_state['authenticated'] = False
        st.session_state['username'] = None
        st.session_state['profiles'] = {}
        st.rerun()

# --- BRIDGE VARIABLES ---
app_mode = st.session_state.get('app_mode', 'DASHBOARD')
active_profile = st.session_state.get('active_profile_name')
        
def show_paywall():
    """Renders the Castellan Agency Tier Paywall."""
    st.markdown("""
        <style>
            .paywall-card {
                background-color: #1b2a2e;
                border: 1px solid #ab8f59;
                padding: 40px;
                text-align: center;
                border-radius: 4px;
                margin-top: 50px;
                box-shadow: 0 20px 50px rgba(0,0,0,0.5);
            }
            .paywall-icon { font-size: 3rem; margin-bottom: 20px; display: block; }
            .paywall-title { 
                color: #f5f5f0; font-family: 'Helvetica Neue', sans-serif; 
                font-weight: 800; text-transform: uppercase; letter-spacing: 0.1em;
                font-size: 1.5rem; margin-bottom: 10px;
            }
            .paywall-desc { color: #5c6b61; margin-bottom: 30px; font-size: 1rem; line-height: 1.6; }
            .paywall-price { color: #ab8f59; font-size: 1.2rem; font-weight: 700; margin-bottom: 30px; }
        </style>
        <div class="paywall-card">
            <span class="paywall-icon">🔒</span>
            <div class="paywall-title">Agency Tier Restricted</div>
            <div class="paywall-desc">
                This capability requires high-fidelity engine processing.<br>
                Upgrade to the Agency Tier to unlock full narrative governance.
            </div>
            <div class="paywall-price"></div>
            <a href="https://castellanpr.lemonsqueezy.com" target="_blank">
                <button style="
                    background-color: #ab8f59; color: #1b2a2e; border: none; 
                    padding: 12px 30px; font-weight: 800; letter-spacing: 0.1em; 
                    cursor: pointer; text-transform: uppercase;">
                    Initialize Subscription
                </button>
            </a>
        </div>
    """, unsafe_allow_html=True)
    st.stop() # CRITICAL: This halts the app so users can't see the tool below.
    
# --- MODULES ---

# 1. DASHBOARD
if app_mode == "DASHBOARD":
    
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
                BRAND GOVERNANCE BEGINS HERE
            </h2>
            <p style='font-size: 1.1rem; line-height: 1.6; margin-bottom: 40px; max-width: 700px; margin-left: auto; margin-right: auto;'>
                Signet measures signal degradation across your brand's publishing perimeter. 
                To begin, build a Brand Profile containing your authoritative signal.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("BUILD BRAND PROFILE", use_container_width=True, type="primary"):
                st.session_state['app_mode'] = "BRAND ARCHITECT"
                st.rerun()
        
        st.markdown("""
        <div style='max-width: 600px; margin: 40px auto 0 auto; padding: 20px; border-left: 3px solid #5c6b61;'>
            <p style='margin-bottom: 10px; font-weight: 600; color: #ab8f59;'>A Brand Profile contains:</p>
            <ul style='line-height: 1.8;'>
                <li>Voice DNA (3-5 gold-standard text assets)</li>
                <li>Visual Standards (color palette, logo specifications)</li>
                <li>Strategic Foundation (mission, values, guardrails)</li>
            </ul>
            <p style='margin-top: 20px; color: #5c6b61;'>
                Once calibrated, governance modules become operational.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.stop()  # Don't show the rest of dashboard
    
    # --- RETURNING USER STATE (1+ PROFILES) ---
    st.title("COMMAND CENTER")
    
    # Profile selector (auto-select if only one profile)
    if len(profiles) == 1:
        selected_profile = list(profiles.keys())[0]
        st.info(f"Using profile: **{selected_profile}**")
        st.session_state['active_profile_name'] = selected_profile
    else:
        selected_profile = st.selectbox(
            "SELECT BRAND PROFILE",
            list(profiles.keys()),
            index=list(profiles.keys()).index(active_profile_name) if active_profile_name in profiles else 0
        )
        st.session_state['active_profile_name'] = selected_profile
    
    current_profile = profiles[selected_profile]
    
    # Calculate calibration data
    cal_data = calculate_calibration_score(current_profile)
    
    # --- THREE-COLUMN LAYOUT ---
    col_left, col_center, col_right = st.columns([1.2, 1.5, 1.3])
    
    # ========================================
    # LEFT COLUMN: PROFILE STATUS
    # ========================================
    with col_left:
        st.markdown("### PROFILE STATUS")
        
        # Calibration Score Display
        score = cal_data.get('score', 0)
        status_label = cal_data.get('status_label', 'UNKNOWN')
        
        # Color coding (using approved colors)
        if score < 40:
            color = "#bd0000"  # Red
        elif score < 80:
            color = "#eeba2b"  # Orange
        else:
            color = "#5c6b61"  # Green
        
        st.markdown(f"""
        <div style='background: rgba(27, 42, 46, 0.6); padding: 20px; border-left: 4px solid {color}; margin-bottom: 20px;'>
            <div style='font-size: 0.9rem; color: #ab8f59; margin-bottom: 5px;'>CALIBRATION</div>
            <div style='font-size: 2rem; font-weight: 800; color: {color};'>{score}%</div>
            <div style='font-size: 0.85rem; color: #5c6b61; margin-top: 5px;'>{status_label}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Cluster Status
        cluster_health = cal_data.get('clusters', {})
        
        if cluster_health:
            st.markdown("**VOICE CLUSTER STATUS:**")
            
            cluster_display_names = {
                "Corporate": "Corporate Affairs",
                "Crisis": "Crisis & Response",
                "Internal": "Internal Leadership",
                "Thought": "Thought Leadership",
                "Marketing": "Brand Marketing"
            }
            
            for key, full_name in cluster_display_names.items():
                if key in cluster_health:
                    data = cluster_health[key]
                    count = data.get('count', 0)
                    icon = data.get('icon', '❌')
                    
                    st.markdown(f"{icon} {full_name} ({count} assets)")
        
        # Engine Readiness Summary
        st.markdown("---")
        st.markdown("**ENGINE READINESS:**")
        
        fortified_clusters = [
            cluster_display_names.get(key, key) 
            for key, data in cluster_health.items() 
            if data.get('count', 0) >= 3
        ]
        
        if fortified_clusters:
            st.markdown("Calibrated for content generation and copy review in:")
            for cluster in fortified_clusters:
                st.markdown(f"• {cluster}")
        else:
            st.warning("Engine requires 3+ assets per cluster for reliable output.")
        
        # Show next fortification target
        unstable_clusters = [
            (key, data) 
            for key, data in cluster_health.items() 
            if data.get('count', 0) > 0 and data.get('count', 0) < 3
        ]
        
        if unstable_clusters:
            key, data = unstable_clusters[0]
            needed = 3 - data.get('count', 0)
            cluster_name = cluster_display_names.get(key, key)
            st.info(f"⚠️ Add {needed} more {cluster_name} asset{'s' if needed > 1 else ''} to fortify this cluster.")
    
    # ========================================
    # CENTER COLUMN: GOVERNANCE MODULES
    # ========================================
    with col_center:
        st.markdown("### GOVERNANCE MODULES")
        
        module_descriptions = {
            "VISUAL COMPLIANCE": "Audit images against palette standards",
            "COPY EDITOR": "Enforce voice across written content",
            "CONTENT GENERATOR": "Generate brand-calibrated copy",
            "SOCIAL MEDIA ASSISTANT": "Cross-channel consistency analysis"
        }
        
        for module_name, description in module_descriptions.items():
            if st.button(module_name, use_container_width=True):
                st.session_state['app_mode'] = module_name
                st.rerun()
            st.caption(description)
            st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)
    
    # ========================================
    # RIGHT COLUMN: RECENT OPERATIONS
    # ========================================
    with col_right:
        st.markdown("### RECENT OPERATIONS")
        
        # Fetch activity logs
        try:
            logs = db.get_org_logs(org_id, limit=10)
            
            # Filter for non-admins (show only their activity)
            if not is_admin:
                logs = [log for log in logs if log.get('username') == username]
            
            if logs:
                for log in logs:
                    timestamp = log.get('timestamp', '')
                    activity = log.get('activity_type', 'UNKNOWN')
                    verdict = log.get('verdict', '')
                    score = log.get('score', 0)
                    asset = log.get('asset_name', '')
                    
                    # Format display based on activity type
                    if 'VISUAL' in activity:
                        detail = f"PASS ({score}%)" if score > 60 else f"FAIL ({score}%)"
                    elif 'EDIT' in activity or 'COPY' in activity:
                        detail = verdict
                    elif 'GENERATION' in activity or 'CONTENT' in activity:
                        metadata = json.loads(log.get('metadata_json', '{}'))
                        word_count = metadata.get('word_count', 'N/A')
                        detail = f"{word_count} words" if isinstance(word_count, int) else verdict
                    else:
                        detail = verdict
                    
                    st.markdown(f"""
                    <div style='background: rgba(27, 42, 46, 0.4); padding: 10px; margin-bottom: 8px; border-left: 2px solid #5c6b61;'>
                        <div style='font-size: 0.75rem; color: #ab8f59;'>{timestamp} │ {activity}</div>
                        <div style='font-size: 0.85rem; margin-top: 4px;'>└─ {detail}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.info("No recent activity logged.")
        
        except Exception as e:
            st.error(f"Error loading activity log: {e}")
        
        # View full log button
        if st.button("VIEW FULL LOG", use_container_width=True):
            # Manually force the navigation state
            st.session_state.app_mode = "ACTIVITY LOG" 
            st.rerun()

            
# 2. VISUAL COMPLIANCE (The 5-Pillar Scorecard)
elif app_mode == "VISUAL COMPLIANCE":
    st.title("VISUAL COMPLIANCE AUDIT")
    
    # --- CSS INJECTION ---
    st.markdown("""
        <style>
        div.stButton > button[kind="primary"] {
            background-color: #ab8f59 !important;
            color: #1b2a2e !important;
            border: none !important;
            font-weight: 800 !important;
            letter-spacing: 1px !important;
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
    
    # --- AGENCY TIER CHECK ---
    is_admin = st.session_state.get('is_admin', False)
    sub_status = st.session_state.get('status', 'trial').lower()
    
    if not is_admin and sub_status != 'active':
        show_paywall()
    
    # --- HELPER: ASSET LIBRARY RETRIEVAL (UPDATED) ---
    def get_all_visual_assets(profile_data):
        """Parses Visual DNA AND Social DNA to find ALL saved images."""
        inputs = profile_data.get('inputs', {})
        assets = {}
        
        # WE NOW SCAN BOTH VISUAL AND SOCIAL DNA
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
    if not active_profile_name:
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
                uploaded_file = st.file_uploader("Upload the draft to check", type=['png', 'jpg', 'jpeg'])
                if uploaded_file:
                    image = Image.open(uploaded_file)
                    st.image(image, caption="Candidate", use_container_width=True)
            
            with c2:
                st.markdown("### 2. CONTEXT & STANDARDS")
                asset_type = st.selectbox("What are we auditing?", [
                    "Social Media Post",
                    "Website/Landing Page",
                    "Email Header/Banner",
                    "Print/Flyer",
                    "Presentation Slide"
                ])
                
                # Retrieve All Assets (Updated Function)
                all_assets = get_all_visual_assets(profile_data)
                
                # Determine Smart Defaults based on Asset Type
                default_selections = []
                # 1. Always look for Logo
                for name in all_assets.keys():
                    if "LOGO" in name.upper(): default_selections.append(name)
                
                # 2. Look for Context Matches
                keyword_map = {
                    "Social Media Post": "SOCIAL",
                    "Website/Landing Page": "WEB",
                    "Email Header/Banner": "EMAIL",
                    "Print/Flyer": "PRINT",
                    "Presentation Slide": "SLIDE"
                }
                key = keyword_map.get(asset_type, "")
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
                        st.image(collage, caption="Active Reference Sheet (The 'Gold Standard')", use_container_width=True)
                    else:
                        st.info("No visual references selected. Auditing based on Text Rules only.")
                else:
                    st.warning("⚠️ No visual assets found in Brand Manager.")
                    st.caption("The engine will rely on your Color Palette and Tone rules. Upload assets in 'Social Media' or 'Visual ID' to enable comparison.")
                    selected_asset_names = []

            st.divider()

            if st.button("RUN COMPLIANCE CHECK", type="primary", use_container_width=True):
                if uploaded_file:
                    with st.spinner("ANALYZING PIXELS & CALCULATING COMPLIANCE..."):
                        
                        inputs = profile_data.get('inputs', {})
                        
                        # 1. PREPARE VISUAL REFERENCE (COLLAGE)
                        reference_image_obj = None
                        if selected_asset_names:
                            imgs = [all_assets[n] for n in selected_asset_names]
                            reference_image_obj = create_reference_collage(imgs)
                        
                        # 2. BUILD TEXT DNA (THE FALLBACK KING)
                        def clean_dna(text):
                            if not text: return ""
                            return "\n".join([l for l in text.split('\n') if not l.startswith("[VISUAL_REF:")])

                        visual_dna_clean = clean_dna(inputs.get('visual_dna', ''))
                        
                        visual_context = f"""
                        CORE IDENTITY (THE LAW):
                        - Primary Palette (Hex): {', '.join(inputs.get('palette_primary', []))}
                        - Typography/Style Rules: {visual_dna_clean}
                        - Brand Voice: {inputs.get('wiz_tone', 'N/A')}
                        - Core Values: {inputs.get('wiz_values', 'N/A')}
                        
                        CONTEXT:
                        - Asset Type: {asset_type}
                        
                        GUARDRAILS (DO NOT VIOLATE):
                        {inputs.get('wiz_guardrails', '')}
                        """
                        
                        try:
                            # Pass the Collage as the single reference image
                            result = logic_engine.run_visual_audit(image, visual_context, reference_image=reference_image_obj)
                            
                            # Save State
                            st.session_state['active_audit_result'] = result
                            st.session_state['active_audit_image'] = image
                            
                            # LOG TO DB (GOD MODE)
                            db.log_event(
                                org_id=st.session_state.get('org_id', 'Unknown'),
                                username=st.session_state.get('username', 'Unknown'),
                                activity_type="VISUAL AUDIT",
                                asset_name=uploaded_file.name,
                                score=result.get('score', 0),
                                verdict=result.get('verdict', 'N/A'),
                                metadata=result
                            )
                            
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"System Error: {e}")
                else:
                    st.warning("Please upload an image.")

        # --- RESULTS DISPLAY (If State Exists) ---
        if st.session_state.get('active_audit_result'):
            result = st.session_state['active_audit_result']
            
            # Score Header
            score = result.get('score', 0)
            bd = result.get('breakdown', {})
            score_color = "#ff4b4b" 
            if score > 60: score_color = "#ffa421"
            if score > 85: score_color = "#09ab3b"
            
            c1, c2 = st.columns([1, 2])
            with c1:
                st.markdown(f"""
                    <div style="background-color: #1b2a2e; border: 1px solid {score_color}; padding: 30px; border-radius: 4px; text-align: center; height: 100%;">
                        <h2 style="color: {score_color}; margin: 0; font-size: 3.5rem; font-weight: 800; letter-spacing: -2px;">{score}</h2>
                        <p style="color: #5c6b61; margin: 0; letter-spacing: 2px; font-weight: 700; text-transform: uppercase; font-size: 0.8rem;">{result.get('verdict', 'ANALYZED')}</p>
                    </div>
                """, unsafe_allow_html=True)
            
            with c2:
                def render_bar(label, val, weight_txt):
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
                
                render_bar("COLOR FIDELITY", bd.get('color', {}).get('score', 0), "(25%)")
                render_bar("IDENTITY INTEGRITY", bd.get('identity', {}).get('score', 0), "(25%)")
                render_bar("TONE & COPY", bd.get('tone', {}).get('score', 0), "(20%)")
                render_bar("TYPOGRAPHY", bd.get('typography', {}).get('score', 0), "(15%)")
                render_bar("VISUAL AESTHETIC", bd.get('vibe', {}).get('score', 0), "(15%)") # RENAMED

            st.divider()
            
            col_crit, col_warn, col_win = st.columns(3)
            st.markdown("""
            <style>
                .geo-bullet-red { display: inline-block; width: 8px; height: 8px; background-color: #ff4b4b; margin-right: 8px; transform: rotate(45deg); }
                .geo-bullet-orange { display: inline-block; width: 8px; height: 8px; background-color: #ffa421; margin-right: 8px; border-radius: 50%; }
                .geo-bullet-green { display: inline-block; width: 8px; height: 8px; background-color: #09ab3b; margin-right: 8px; }
                .audit-item { font-size: 0.85rem; color: #f5f5f0; margin-bottom: 12px; border-left: 2px solid #3d3d3d; padding-left: 12px; line-height: 1.4; }
            </style>
            """, unsafe_allow_html=True)
            
            with col_crit:
                st.markdown("<h5 style='color:#ff4b4b; letter-spacing:1px;'>VIOLATIONS</h5>", unsafe_allow_html=True)
                if result.get('critical_fixes'):
                    for fix in result['critical_fixes']:
                        st.markdown(f"<div class='audit-item' style='border-left-color: #ff4b4b;'><div class='geo-bullet-red'></div>{fix}</div>", unsafe_allow_html=True)
                else:
                    st.caption("No critical errors.")

            with col_warn:
                st.markdown("<h5 style='color:#ffa421; letter-spacing:1px;'>REFINEMENTS</h5>", unsafe_allow_html=True)
                if result.get('minor_fixes'):
                    for fix in result['minor_fixes']:
                        st.markdown(f"<div class='audit-item' style='border-left-color: #ffa421;'><div class='geo-bullet-orange'></div>{fix}</div>", unsafe_allow_html=True)
                else:
                    st.caption("No refinements needed.")

            with col_win:
                st.markdown("<h5 style='color:#09ab3b; letter-spacing:1px;'>SUCCESS</h5>", unsafe_allow_html=True)
                if result.get('brand_wins'):
                    for win in result['brand_wins']:
                        st.markdown(f"<div class='audit-item' style='border-left-color: #09ab3b;'><div class='geo-bullet-green'></div>{win}</div>", unsafe_allow_html=True)
                else:
                    st.caption("No specific wins.")
            
            with st.expander("VIEW SCORING LOGIC (TRANSPARENCY REPORT)"):
                r_color = bd.get('color', {}).get('reason', 'No data.')
                r_id = bd.get('identity', {}).get('reason', 'No data.')
                r_tone = bd.get('tone', {}).get('reason', 'No data.')
                r_typo = bd.get('typography', {}).get('reason', 'No data.')
                r_vibe = bd.get('vibe', {}).get('reason', 'No data.')
                
                st.markdown(f"""
                **1. COLOR ANALYSIS:** {r_color}  
                **2. IDENTITY:** {r_id}  
                **3. TONE & COPY:** {r_tone}
                **4. TYPOGRAPHY:** {r_typo}  
                **5. VISUAL AESTHETIC:** {r_vibe}
                """)
    
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
            with st.form("add_team_member"):
                new_user = st.text_input("USERNAME", max_chars=64)
                new_email = st.text_input("EMAIL", max_chars=120)
                new_pass = st.text_input("TEMP PASSWORD", type="password", max_chars=64)
                submitted = st.form_submit_button("CREATE SEAT")
                
                if submitted:
                    if new_user and new_pass:
                        # CREATE USER LINKED TO CURRENT ORG
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
    
    # --- CSS INJECTION ---
    st.markdown("""
        <style>
        div.stButton > button[kind="primary"] {
            background-color: #ab8f59 !important;
            color: #1b2a2e !important;
            border: none !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
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

    # --- AGENCY TIER CHECK ---
    is_admin = st.session_state.get('is_admin', False)
    sub_status = st.session_state.get('status', 'trial').lower()
    if not is_admin and sub_status != 'active':
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
                # Trigger: Changing this updates the Confidence Meter
                content_type = st.selectbox("CONTENT TYPE", [
                    "Internal Email", 
                    "Press Release", 
                    "Blog Post", 
                    "Executive Memo", 
                    "Crisis Statement",       
                    "Speech / Script",        
                    "Social Campaign"   
                ])
            with cc2: 
                # Persisted Sender
                st.text_input("SENDER / VOICE", placeholder="e.g. CEO", key="ce_sender", max_chars=100)
            with cc3: 
                # Persisted Audience
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
            
            if st.button("REWRITE AND ALIGN", type="primary", use_container_width=True):
                # Access via state key
                if st.session_state['ce_draft']:
                    with st.spinner("CALIBRATING TONE & SYNTAX..."):
                        
                        # --- SMART CONTEXT BUILDING ---
                        inputs = profile_data.get('inputs', {})
                        
                        # 1. Clean Base64 noise (Safety)
                        def clean_dna(text):
                            if not text: return ""
                            return "\n".join([l for l in text.split('\n') if not l.startswith("[VISUAL_REF:")])

                        voice_dna = clean_dna(inputs.get('voice_dna', ''))
                        
                        # 2. Build the "Voice Prompt"
                        prof_text = f"""
                        STRATEGY:
                        - Mission: {inputs.get('wiz_mission', '')}
                        - Tone Keywords: {inputs.get('wiz_tone', '')}
                        
                        VOICE DNA (LINGUISTIC RULES & SAMPLES):
                        {voice_dna}
                        
                        CRITICAL GUARDRAILS (DO NOT VIOLATE):
                        {inputs.get('wiz_guardrails', '')}
                        """
                        
                        # 3. Engineered Prompt
                        prompt_wrapper = f"""
                        CONTEXT: 
                        - Type: {content_type}
                        - Sender: {st.session_state['ce_sender']}
                        - Audience: {st.session_state['ce_audience']}
                        - Intensity: {edit_intensity}
                        
                        TASK: Rewrite the draft below to match the Brand Rules.
                        
                        STEP 1: RATIONALE
                        Analyze the draft against the brand voice. Explain 3 key changes you are making and why.
                        
                        STEP 2: REWRITE
                        Provide the rewritten text. Ensure all GUARDRAILS are strictly followed.
                        
                        OUTPUT FORMAT:
                        RATIONALE:
                        [Your explanation]
                        REWRITE:
                        [The new text]
                        
                        DRAFT CONTENT (DATA ONLY): 
                        --- BEGIN USER TEXT ---
                        {st.session_state['ce_draft']}
                        --- END USER TEXT ---
                        """
                        
                        # Call Logic
                        try:
                            # Use Safe Generate Wrapper
                            full_response = logic_engine.run_copy_editor(prompt_wrapper, prof_text)
                            
                            # Parse Split (Heuristic)
                            if "REWRITE:" in full_response:
                                parts = full_response.split("REWRITE:")
                                rationale = parts[0].replace("RATIONALE:", "").strip()
                                rewrite = parts[1].strip()
                            else:
                                rationale = "Automated alignment to brand voice."
                                rewrite = full_response
                            
                            # Update State
                            st.session_state['ce_result'] = rewrite
                            st.session_state['ce_rationale'] = rationale
                            
                            # LOG TO DB (GOD MODE)
                            # This writes to the shared Agency Timeline
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
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("Please enter text to rewrite.")

        # --- OUTPUT SECTION (Stateful) ---
        if st.session_state['ce_result']:
            st.divider()
            
            # Rationale Box
            if st.session_state['ce_rationale']:
                st.markdown(f"""
                    <div class="rationale-box">
                        <strong>STRATEGIC RATIONALE:</strong><br>
                        {st.session_state['ce_rationale']}
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
                    
# 4. CONTENT GENERATOR (Stateful, Calibrated, Structured)
elif app_mode == "CONTENT GENERATOR":
    st.title("CONTENT GENERATOR")
    
    # --- CSS INJECTION ---
    st.markdown("""
        <style>
        div.stButton > button[kind="primary"] {
            background-color: #ab8f59 !important;
            color: #1b2a2e !important;
            border: none !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
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

    # --- AGENCY TIER CHECK ---
    is_admin = st.session_state.get('is_admin', False)
    sub_status = st.session_state.get('status', 'trial').lower()
    if not is_admin and sub_status != 'active':
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
        # We count how many times this specific format appears in the DNA
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
                # Trigger for Dynamic Calibration
                content_type = st.selectbox("FORMAT", [
                    "Press Release", "Internal Email", "Executive Memo", "Blog Post", 
                    "Crisis Statement", "Speech / Script", "Social Campaign"
                ])
            with cc2:
                length = st.select_slider("TARGET LENGTH", options=["Brief", "Standard", "Deep Dive"])
            
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
            
            if st.button("GENERATE DRAFT", type="primary", use_container_width=True):
                # Access via state keys
                if st.session_state['cg_topic'] and st.session_state['cg_key_points']:
                    with st.spinner("ARCHITECTING CONTENT..."):
                        
                        # --- SMART CONTEXT BUILDING ---
                        inputs = profile_data.get('inputs', {})
                        
                        # 1. Clean Base64 noise (Safety)
                        def clean_dna(text):
                            if not text: return ""
                            return "\n".join([l for l in text.split('\n') if not l.startswith("[VISUAL_REF:")])

                        voice_dna = clean_dna(inputs.get('voice_dna', ''))
                        
                        # 2. Build the "Targeted Prompt"
                        prof_text = f"""
                        STRATEGY:
                        - Mission: {inputs.get('wiz_mission', '')}
                        - Tone Keywords: {inputs.get('wiz_tone', '')}
                        
                        VOICE DNA (LINGUISTIC RULES & SAMPLES):
                        {voice_dna}
                        
                        CRITICAL GUARDRAILS (DO NOT VIOLATE):
                        {inputs.get('wiz_guardrails', '')}
                        """
                        
                        # Engineered Prompt (Constraint-Based)
                        prompt_wrapper = f"""
                        CONTEXT:
                        - Type: {content_type}
                        - Length: {length}
                        - Sender: {sender}
                        - Audience: {audience}
                        
                        CORE TASK: Write a {content_type} about "{st.session_state['cg_topic']}".
                        
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
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("Topic and Key Points are required.")

        # --- 3. OUTPUT DISPLAY ---
        if st.session_state['cg_result']:
            st.divider()
            
            if st.session_state['cg_rationale']:
                st.markdown(f"""
                    <div class="rationale-box">
                        <strong>GENERATION STRATEGY:</strong><br>
                        {st.session_state['cg_rationale']}
                    </div>
                """, unsafe_allow_html=True)
            
            st.subheader("FINAL DRAFT")
            st.text_area("Copy to Clipboard", value=st.session_state['cg_result'], height=500)
                
# 5. SOCIAL MEDIA ASSISTANT (Platform-Aware, Goal-Oriented, Trend-Aware)
elif app_mode == "SOCIAL MEDIA ASSISTANT":
    st.title("SOCIAL MEDIA ASSISTANT")
    
    # --- CSS INJECTION ---
    st.markdown("""
        <style>
        div.stButton > button[kind="primary"] {
            background-color: #ab8f59 !important;
            color: #1b2a2e !important;
            border: none !important;
            font-weight: 800 !important;
            text-transform: uppercase !important;
            letter-spacing: 1px !important;
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

    # --- AGENCY TIER CHECK ---
    is_admin = st.session_state.get('is_admin', False)
    sub_status = st.session_state.get('status', 'trial').lower()
    if not is_admin and sub_status != 'active':
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
        if 'sm_goal' not in st.session_state: st.session_state['sm_goal'] = "Reach (Awareness)"
        if 'sm_results' not in st.session_state: st.session_state['sm_results'] = None
        
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
            
            if st.button("GENERATE OPTIONS", type="primary", use_container_width=True):
                # Check using session state
                if st.session_state['sm_topic']:
                    with st.spinner("SCANNING TRENDS & DRAFTING..."):
                        
                        # --- SMART CONTEXT BUILDING ---
                        inputs = profile_data.get('inputs', {})
                        
                        # 1. Clean Base64 noise
                        def clean_dna(text):
                            if not text: return ""
                            return "\n".join([l for l in text.split('\n') if not l.startswith("[VISUAL_REF:")])

                        social_dna = clean_dna(inputs.get('social_dna', ''))
                        
                        # 2. Build the "Social Prompt"
                        prof_text = f"""
                        STRATEGY:
                        - Mission: {inputs.get('wiz_mission', '')}
                        - Tone Keywords: {inputs.get('wiz_tone', '')}
                        
                        SOCIAL MEDIA DNA (SUCCESSFUL PATTERNS):
                        {social_dna}
                        
                        CRITICAL GUARDRAILS (DO NOT VIOLATE):
                        {inputs.get('wiz_guardrails', '')}
                        """
                        
                        # 3. Image Analysis (if present)
                        image_desc = "No image provided."
                        if uploaded_image:
                            img = Image.open(uploaded_image)
                            image_desc = logic_engine.analyze_social_post(img)
                        
                        # 4. Engineered Prompt (Trend-Aware)
                        prompt = (
                            f"ROLE: Expert Social Media Manager for the brand defined below.\n"
                            f"PLATFORM: {st.session_state['sm_platform']} (Adhere strictly to character limits and cultural norms).\n"
                            f"GOAL: {st.session_state['sm_goal']}\n"
                            f"TOPIC: \"\"\"{st.session_state['sm_topic']}\"\"\"\n"
                            f"IMAGE CONTEXT: {image_desc}\n\n"
                            
                            "STEP 0: TREND CHECK (CRITICAL)\n"
                            f"Using Google Search, identify 3 currently trending hashtags or conversation topics related to '{st.session_state['sm_topic']}' on {st.session_state['sm_platform']}. "
                            "If relevant, integrate these into the posts to maximize visibility.\n\n"
                            
                            "TASK: Generate 3 distinct post options.\n\n"
                            
                            "OPTION 1: THE STORYTELLER\n"
                            "- Focus: Narrative, emotive, connects topic to brand values.\n"
                            "- Structure: Long-form (if platform allows), spacing for readability.\n\n"
                            
                            "OPTION 2: THE PROVOCATEUR\n"
                            "- Focus: Pattern interrupt, hot take, or question.\n"
                            "- Structure: Short, punchy, designed to stop the scroll.\n\n"
                            
                            "OPTION 3: THE VALUE-ADD\n"
                            "- Focus: Educational, utility, 'Save this post'.\n"
                            "- Structure: Bullet points or actionable advice.\n\n"
                            
                            "OUTPUT FORMAT:\n"
                            "Strictly separate options with '|||'.\n"
                            "Example: Option 1 Content ||| Option 2 Content ||| Option 3 Content\n"
                            "IMPORTANT: Append the 'Trending Hashtags' you found to the bottom of the best-suited option."
                        )
                        
                        try:
                            # We use the content generator method as a wrapper (it uses the Search Model)
                            response = logic_engine.run_content_generator("Social Post", st.session_state['sm_platform'], prompt, prof_text)
                            
                            # Parse
                            options = response.split("|||")
                            # Fallback if split fails
                            if len(options) < 3: options = [response, "Option 2 Generation Failed", "Option 3 Generation Failed"]
                            
                            st.session_state['sm_results'] = options
                            
                            # LOG TO DB (GOD MODE)
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
                                    "options": options
                                }
                            )
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    st.warning("Please enter a topic.")

        # --- OUTPUT DISPLAY ---
        if st.session_state['sm_results']:
            st.divider()
            st.subheader("CAMPAIGN OPTIONS")
            
            t1, t2, t3 = st.tabs(["THE STORYTELLER", "THE PROVOCATEUR", "THE VALUE-ADD"])
            
            with t1:
                st.text_area("Narrative Focus", value=st.session_state['sm_results'][0].strip(), height=400)
            with t2:
                st.text_area("Engagement Focus", value=st.session_state['sm_results'][1].strip(), height=400)
            with t3:
                st.text_area("Utility Focus", value=st.session_state['sm_results'][2].strip(), height=400)
                
# 6. BRAND ARCHITECT
elif app_mode == "BRAND ARCHITECT":
    st.title("BRAND ARCHITECT")
    
    # --- CSS INJECTION FOR VISIBILITY ---
    st.markdown("""
        <style>
        div.stButton > button[kind="primary"] {
            background-color: #ab8f59 !important;
            color: #1b2a2e !important;
            border: none !important;
            font-weight: 800 !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #f0c05a !important;
            color: #1b2a2e !important;
        }
        div.stButton > button[kind="primary"] p {
            color: #1b2a2e !important;
        }
        </style>
    """, unsafe_allow_html=True)

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
            
    # PERSISTENCE HANDLED AUTOMATICALLY UPON GENERATION NOW
    st.info("Profiles are automatically saved to your account upon generation.")
    
    tab1, tab2 = st.tabs(["WIZARD", "PDF EXTRACT"])
    with tab1:
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
            
        with st.expander("2. VOICE & CALIBRATION"):
            st.caption("Upload existing content to train the engine on your voice.")
            st.selectbox("CONTENT TYPE", ["Internal Email", "Executive Memo", "Press Release", "Article/Blog", "Social Post", "Website Copy", "Other"], key="wiz_sample_type")
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

        with st.expander("3. SOCIAL MEDIA (GOLD STANDARD)"):
            st.caption("Upload 'Representative' posts that capture your ideal look & feel.")
            
            c1, c2 = st.columns([1, 2])
            with c1:
                s_plat = st.selectbox("PLATFORM", ["LinkedIn", "Instagram", "X (Twitter)"], key="wiz_social_platform")
            with c2:
                s_key = f"social_up_{st.session_state['social_uploader_key']}"
                s_file = st.file_uploader("UPLOAD SCREENSHOT", type=["png", "jpg"], key=s_key)
            
            # --- NEW: STATEFUL ANALYSIS PREVIEW ---
            if 'temp_social_analysis' not in st.session_state: st.session_state['temp_social_analysis'] = ""
            
            if s_file and st.button("ANALYZE POST"):
                with st.spinner("REVERSE ENGINEERING STRATEGY..."):
                    img = Image.open(s_file)
                    # Use the NEW Strict Method (Visual Vibe -> Aesthetic)
                    st.session_state['temp_social_analysis'] = logic_engine.analyze_social_style(img)
            
            # --- THE FEEDBACK LOOP ---
            if st.session_state['temp_social_analysis']:
                st.markdown("#### 🧬 AI FINDINGS (REVIEW & EDIT)")
                st.caption("Edit the analysis below to ensure it matches your brand standards.")
                
                edited_analysis = st.text_area(
                    "SOCIAL DNA", 
                    value=st.session_state['temp_social_analysis'], 
                    height=200,
                    key="social_edit_box",
                    max_chars=5000
                )
                
                if st.button("CONFIRM & ADD TO DNA", type="primary"):
                    entry = {
                        "file": s_file,
                        "platform": s_plat,
                        "analysis": edited_analysis # Save the EDITED version
                    }
                    st.session_state['wiz_social_list'].append(entry)
                    st.session_state['temp_social_analysis'] = "" # Reset
                    st.session_state['social_uploader_key'] += 1 # Reset Uploader
                    st.success("Added to Social DNA Buffer")
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

        if st.button("GENERATE SYSTEM", type="primary"):
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
                        3. VISUALS: Palette: {palette_str}. Logo: {logo_summary}. Social DNA: {social_summary}
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
                                "social_dna": social_summary # PERSIST THE DNA
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
                            metadata={"method": "Wizard Generator"}
                        )

                        st.session_state['wiz_samples_list'] = []
                        st.session_state['wiz_social_list'] = []
                        st.session_state['wiz_logo_list'] = []
                        st.success("CALIBRATED & SAVED TO DATABASE")
                        st.rerun()
                    except Exception as e:
                        if "ResourceExhausted" in str(e): st.error("⚠️ AI QUOTA EXCEEDED: Please wait 60 seconds.")
                        else: st.error(f"Error: {e}")

    with tab2:
        st.markdown("### AUTO-FILL FROM GUIDELINES")
        st.caption("Upload a PDF to automatically populate the Wizard fields.")
        
        # The uploader needs the key match the callback
        st.file_uploader("UPLOAD BRAND GUIDE", type=["pdf"], key="arch_pdf_uploader")
        
        # The button simply triggers the callback
        st.button("EXTRACT & MAP TO WIZARD", type="primary", on_click=extract_and_map_pdf)
    
        # Display Messages based on the flags set in callback
        if st.session_state.get('extraction_success'):
            st.success("✅ Extraction Complete! Switch to the 'WIZARD' tab to review.")
            # Clear flag so it doesn't stay forever
            st.session_state['extraction_success'] = False
        
        if st.session_state.get('extraction_error'):
            st.error(f"Extraction Error: {st.session_state['extraction_error']}")
            st.session_state['extraction_error'] = None

# 7. BRAND MANAGER
elif app_mode == "BRAND MANAGER":
    st.title("BRAND MANAGER")
    
    # --- CSS INJECTION ---
    st.markdown("""
        <style>
        div.stButton > button[kind="primary"] {
            background-color: #ab8f59 !important;
            color: #1b2a2e !important;
            border: none !important;
            font-weight: 800 !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #f0c05a !important;
            color: #1b2a2e !important;
        }
        div.stButton > button[kind="primary"] p {
            color: #1b2a2e !important;
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

    # --- HELPERS ---
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
        """Splits the DNA text block into manageable assets based on headers."""
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
        
        # 2. DNA Layers (60%) - The Asset Layer
        has_social = len(inputs.get('social_dna', '')) > 20 or "[ASSET:" in inputs.get('social_dna', '')
        has_voice = len(inputs.get('voice_dna', '')) > 20 or "[ASSET:" in inputs.get('voice_dna', '')
        has_visual = len(inputs.get('visual_dna', '')) > 20 or "[ASSET:" in inputs.get('visual_dna', '')

        if has_social: score += 20
        if has_voice: score += 20
        if has_visual: score += 20
        
        profile_obj['calibration_score'] = min(score, 100)
        return profile_obj

    if st.session_state['profiles']:
        p_keys = list(st.session_state['profiles'].keys())
        default_ix = 0
        if st.session_state.get('active_profile_name') in p_keys:
            default_ix = p_keys.index(st.session_state['active_profile_name'])
        target = st.selectbox("PROFILE", p_keys, index=default_ix)
        profile_obj = st.session_state['profiles'][target]
        
        is_structured = isinstance(profile_obj, dict) and "inputs" in profile_obj
        final_text_view = profile_obj['final_text'] if is_structured else profile_obj
        
        # --- VIEW MODES ---
        view_tab1, view_tab2 = st.tabs(["EDITOR", "LIVE PROFILE PREVIEW"])
        
        with view_tab2:
            st.markdown("### CURRENT BRAND KIT")
            st.caption("This is the exact data the AI uses to generate content.")
            st.text_area("READ-ONLY VIEW", value=final_text_view, height=600, disabled=True)
            
            html_data = convert_to_html_brand_card(target, final_text_view)
            st.download_button(label="DOWNLOAD HTML REPORT", data=html_data, file_name=f"{target.replace(' ', '_')}_BrandKit.html", mime="text/html")

        with view_tab1:
            st.divider()
            
            if is_structured:
                inputs = profile_obj['inputs']
                
                # --- SAFETY INIT ---
                # Ensure all required keys exist to prevent errors
                for key in ['social_dna', 'voice_dna', 'visual_dna']:
                    if key not in inputs: inputs[key] = ""
                for key in ['palette_primary', 'palette_secondary', 'palette_accent']:
                    if key not in inputs: inputs[key] = []
                
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

                # 4. VISUAL IDENTITY (PALETTE) - NEW SECTION ADDED HERE
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
                        cal_img = st.file_uploader("UPLOAD POST SCREENSHOT", type=["png", "jpg"], key="cal_up_social")
                    
                    if 'man_social_analysis' not in st.session_state: st.session_state['man_social_analysis'] = ""
                    
                    if cal_img and st.button(f"ANALYZE {cal_platform.upper()} POST", type="primary", key="btn_cal_social"):
                        with st.spinner("REVERSE ENGINEERING..."):
                            img = Image.open(cal_img)
                            st.session_state['man_social_analysis'] = logic_engine.analyze_social_style(img)
                    
                    if st.session_state['man_social_analysis']:
                        st.markdown("#### REVIEW FINDINGS")
                        edit_social = st.text_area("EDIT ANALYSIS", value=st.session_state['man_social_analysis'], key="rev_social", height=150, max_chars=5000)
                        if st.button("CONFIRM & INJECT (SOCIAL)", type="primary"):
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
                                        st.rerun()
                    else:
                        st.caption("No social assets calibrated.")

                # --- 2. VOICE INJECTOR (FORTIFICATION PROTOCOL) ---
                with cal_tab2:
                    c1, c2 = st.columns([1, 1])
                    with c1:
                        # THE 5 CLUSTERS
                        VOICE_CLUSTERS = {
                            "Corporate Affairs": {
                                "role": "STANDARDIZATION & RECORD",
                                "desc": "Upload Press Releases and Fact Sheets. Maintains objective accuracy and establishes the baseline narrative."
                            },
                            "Crisis & Response": {
                                "role": "DEFENSE & MITIGATION",
                                "desc": "Upload Holding Statements and Apologies. Fortifies reputation during volatility. Prioritizes empathy and rapid stabilization."
                            },
                            "Internal Leadership": {
                                "role": "ALIGNMENT & MORALE",
                                "desc": "Upload Memos and All-Hands updates. Strengthens cultural cohesion and transmits directives from the top down."
                            },
                            "Thought Leadership": {
                                "role": "INFLUENCE & AUTHORITY",
                                "desc": "Upload Op-Eds and Speeches. Penetrates new markets via argumentation and distinct perspective."
                            },
                            "Brand Marketing": {
                                "role": "GROWTH & CONVERSION",
                                "desc": "Upload Newsletters and Copy. Drives action through persuasion and benefit-driven framing."
                            }
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
                        v_file = st.file_uploader("UPLOAD SOURCE MATERIAL (PDF/DOCX/TXT)", type=["pdf", "docx", "txt"], key="cal_up_voice")
                        st.caption("Engine requires 3+ samples per cluster for high fidelity.")
                    
                    if 'man_voice_analysis' not in st.session_state: st.session_state['man_voice_analysis'] = ""
                    
                    if v_file and st.button("INITIATE PROTOCOL ANALYSIS", type="primary", key="btn_cal_voice"):
                        with st.spinner("DECONSTRUCTING RHETORICAL PATTERNS..."):
                            try:
                                raw_txt = ""
                                if v_file.type == "application/pdf":
                                    raw_txt = logic_engine.extract_text_from_pdf(v_file)
                                elif v_file.name.endswith(".docx"):
                                    # PYTHON-DOCX HANDLER
                                    import docx
                                    doc = docx.Document(v_file)
                                    raw_txt = "\n".join([para.text for para in doc.paragraphs])
                                else:
                                    raw_txt = str(v_file.read(), "utf-8")
                                
                                prompt = f"""
                                TASK: Extract the 'Voice DNA' from this text.
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
                                st.session_state['man_voice_analysis'] = logic_engine.generate_brand_rules(prompt)
                            except Exception as e:
                                st.error(f"Analysis Failed: {e}")

                    if st.session_state['man_voice_analysis']:
                        st.markdown("#### ANALYSIS REVIEW")
                        edit_voice = st.text_area("EXTRACTED PATTERNS", value=st.session_state['man_voice_analysis'], key="rev_voice", height=150)
                        
                        if st.button("CONFIRM & FORTIFY ENGINE", type="primary"):
                            from datetime import datetime
                            timestamp = datetime.now().strftime("%Y-%m-%d")
                            
                            # UPDATED HEADER WITH NEW TAXONOMY
                            header_meta = f"CLUSTER: {voice_type.upper()} | SENDER: {voice_sender.upper()} | AUDIENCE: {voice_audience.upper()}"
                            injection = f"\n\n[ASSET: {header_meta} | SOURCE: {v_file.name} | DATE: {timestamp}]\n{edit_voice}\n----------------\n"
                            
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
                    
                    if vis_file and st.button("ANALYZE AESTHETIC", type="primary", key="btn_cal_vis"):
                        with st.spinner("ANALYZING DESIGN..."):
                            img = Image.open(vis_file)
                            st.session_state['man_vis_analysis'] = logic_engine.describe_logo(img)
                    
                    if st.session_state['man_vis_analysis']:
                        st.markdown("#### REVIEW FINDINGS")
                        edit_vis = st.text_area("EDIT ANALYSIS", value=st.session_state['man_vis_analysis'], key="rev_vis", height=150, max_chars=5000)
                        if st.button("CONFIRM & INJECT (VISUAL)", type="primary"):
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
                                        st.rerun()
                    else:
                        st.caption("No visual assets calibrated.")

                st.divider()

                # --- MANUAL EDITORS (ADVANCED) ---
                with st.expander("MANUAL TEXT EDITORS (ADVANCED USERS)"):
                    st.warning("Editing these raw fields directly may break the Asset Library headers above.")
                    edit_tab1, edit_tab2, edit_tab3 = st.tabs(["RAW SOCIAL", "RAW VOICE", "RAW VISUAL"])
                    with edit_tab1:
                        inputs['social_dna'] = st.text_area("SOCIAL DNA BLOB", inputs['social_dna'], height=200, max_chars=10000)
                    with edit_tab2:
                        inputs['voice_dna'] = st.text_area("VOICE DNA BLOB", inputs['voice_dna'], height=200, max_chars=10000)
                    with edit_tab3:
                        inputs['visual_dna'] = st.text_area("VISUAL DNA BLOB", inputs['visual_dna'], height=200, max_chars=10000)

                if st.button("SAVE STRATEGY CHANGES", type="primary"):
                    # 1. Update Standard Inputs
                    profile_obj['inputs']['wiz_name'] = new_name
                    profile_obj['inputs']['wiz_archetype'] = new_arch
                    profile_obj['inputs']['wiz_mission'] = new_mission
                    profile_obj['inputs']['wiz_values'] = new_values
                    profile_obj['inputs']['wiz_tone'] = new_tone
                    profile_obj['inputs']['wiz_guardrails'] = new_guard
                    
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
                    
                    [VOICE DNA & ASSETS]
                    {clean_dna_for_llm(inputs['voice_dna'])}
                    
                    3. VISUALS
                    - Primary: {p_p}
                    - Secondary: {p_s}
                    - Accents: {p_a}
                    
                    [VISUAL DNA & ASSETS]
                    {clean_dna_for_llm(inputs['visual_dna'])}
                    
                    4. GUARDRAILS
                    - {new_guard}
                    
                    5. SOCIAL DNA (CALIBRATION DATA)
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
                    
                    st.success(f"Strategy Saved. Calibration Score: {profile_obj.get('calibration_score', 0)}%")
                    st.rerun()

            else:
                st.warning("This profile was created from a PDF/Raw Text. Structured editing is unavailable.")
                new_raw = st.text_area("EDIT RAW TEXT", final_text_view, height=500, max_chars=20000)
                if st.button("SAVE RAW CHANGES"):
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
                
# ===================================================================
# TEAM MANAGEMENT MODULE - COMPLETE REPLACEMENT
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
                                    conn = sqlite3.connect(db.DB_NAME)
                                    conn.execute("UPDATE users SET is_admin = 0 WHERE username = ?", (username,))
                                    conn.commit()
                                    conn.close()
                                    st.success(f"{username} demoted to Member")
                                    st.rerun()
                        else:
                            if st.button(f"Promote to Admin", key=f"promote_{idx}"):
                                conn = sqlite3.connect(db.DB_NAME)
                                conn.execute("UPDATE users SET is_admin = 1 WHERE username = ?", (username,))
                                conn.commit()
                                conn.close()
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
                                    from argon2 import PasswordHasher
                                    ph = PasswordHasher()
                                    hashed = ph.hash(new_pass)
                                    conn = sqlite3.connect(db.DB_NAME)
                                    conn.execute("UPDATE users SET password_hash = ? WHERE username = ?", (hashed, username))
                                    conn.commit()
                                    conn.close()
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
                            st.warning(f"⚠️ Confirm removal of {username}?")
                            conf_col1, conf_col2 = st.columns(2)
                            with conf_col1:
                                if st.button("Yes, Remove", key=f"yes_remove_{idx}"):
                                    # Delete user
                                    conn = sqlite3.connect(db.DB_NAME)
                                    conn.execute("DELETE FROM users WHERE username = ?", (username,))
                                    conn.commit()
                                    conn.close()
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
            st.error(f"⚠️ SEAT LIMIT REACHED")
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
        
        if st.button("Upgrade Subscription", use_container_width=True):
            st.info("Contact sales@castellanpr.com to upgrade")

# ===================================================================
# END OF TEAM MANAGEMENT MODULE
# ===================================================================

# ===================================================================
# FULL ACTIVITY LOG MODULE - NEW MODULE
# Add this AFTER the Team Management section in app.py
# Also add navigation button: st.button("ACTIVITY LOG", ...)
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
            
            # Display as table
            import pandas as pd
            
            # Prepare data for table
            table_data = []
            for log in logs:
                table_data.append({
                    "TIME": log.get('timestamp', ''),
                    "USER": log.get('username', ''),
                    "ACTIVITY": log.get('activity_type', ''),
                    "ASSET": log.get('asset_name', '')[:30] + "..." if len(log.get('asset_name', '')) > 30 else log.get('asset_name', ''),
                    "SCORE": log.get('score', '-'),
                    "VERDICT": log.get('verdict', '')
                })
            
            df = pd.DataFrame(table_data)
            
            # Interactive table with row selection
            selection = st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )
            
            # --- DETAIL VIEW ---
            st.markdown("---")
            st.markdown("### ENTRY DETAILS")
            
            if selection and len(selection.selection.rows) > 0:
                row_idx = selection.selection.rows[0]
                selected_log = logs[row_idx]
                
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    st.markdown("**METADATA**")
                    st.write(f"**Org:** {selected_log.get('org_id')}")
                    st.write(f"**User:** {selected_log.get('username')}")
                    st.write(f"**Time:** {selected_log.get('timestamp')}")
                    st.write(f"**Activity:** {selected_log.get('activity_type')}")
                    st.write(f"**Asset:** {selected_log.get('asset_name')}")
                    st.write(f"**Score:** {selected_log.get('score')}")
                    st.write(f"**Verdict:** {selected_log.get('verdict')}")
                
                with detail_col2:
                    st.markdown("**FULL PAYLOAD (JSON)**")
                    try:
                        metadata = json.loads(selected_log.get('metadata_json', '{}'))
                        st.json(metadata)
                    except:
                        st.code(selected_log.get('metadata_json', '{}'))
            else:
                st.info("Select a row above to view full details")
        
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
            /* Force Tables to look like Data Terminals */
            div[data-testid="stDataFrame"] div[class*="stDataFrame"] {
                background-color: #1b2a2e !important;
                border: 1px solid #5c6b61;
            }
            div[data-testid="stDataFrame"] table {
                color: #f5f5f0 !important;
                font-family: 'Courier New', monospace !important;
                font-size: 0.85rem !important;
            }
            div[data-testid="stDataFrame"] th {
                background-color: #24363b !important;
                color: #ab8f59 !important;
                border-bottom: 1px solid #ab8f59 !important;
                text-transform: uppercase;
                letter-spacing: 0.1em;
            }
            div[data-testid="stDataFrame"] td {
                border-bottom: 1px solid #3d3d3d !important;
            }
            /* Style the Metrics */
            div[data-testid="stMetricValue"] {
                color: #ab8f59 !important;
                font-family: 'Helvetica Neue', sans-serif !important;
            }
            div[data-testid="stMetricLabel"] {
                color: #5c6b61 !important;
            }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("<h3 style='color: #ab8f59; letter-spacing: 0.1em;'>GLOBAL SYSTEM STATUS</h3>", unsafe_allow_html=True)
        
        # 1. METRICS ROW
        conn = sqlite3.connect(db.DB_NAME)
        
        # Global Counts
        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        org_count = conn.execute("SELECT COUNT(DISTINCT org_id) FROM users").fetchone()[0]
        log_count = conn.execute("SELECT COUNT(*) FROM activity_log").fetchone()[0]
        
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("TOTAL USERS", user_count)
        with m2: st.metric("ACTIVE ORGANIZATIONS", org_count)
        with m3: st.metric("TOTAL ACTIONS LOGGED", log_count)
        
        st.markdown("<br>", unsafe_allow_html=True)

        # 2. TABS FOR DATA
        tab_users, tab_logs = st.tabs(["GLOBAL USER DATABASE", "GLOBAL AUDIT LOGS"])
        
        import pandas as pd

        with tab_users:
            users_raw = conn.execute("SELECT username, email, org_id, is_admin, created_at FROM users").fetchall()
            if users_raw:
                df_users = pd.DataFrame(users_raw, columns=["USERNAME", "EMAIL", "ORG_ID", "ROLE", "CREATED_AT"])
                df_users['ROLE'] = df_users['ROLE'].apply(lambda x: "ADMIN" if x else "USER")
                st.dataframe(df_users, width="stretch", hide_index=True, use_container_width=True)
            else:
                st.info("No users found.")

        with tab_logs:
            # Fetch last 100 logs globally
            logs_raw = conn.execute("SELECT timestamp, org_id, username, activity_type, asset_name, verdict, metadata_json FROM activity_log ORDER BY id DESC LIMIT 100").fetchall()
            
            if logs_raw:
                df_logs = pd.DataFrame(logs_raw, columns=["TIME", "ORG", "USER", "ACTION", "ASSET", "VERDICT", "META"])
                
                # Filter for readability
                display_cols = ["TIME", "ORG", "USER", "ACTION", "VERDICT"]
                
                selection = st.dataframe(
                    df_logs[display_cols], 
                    width="stretch", 
                    hide_index=True,
                    on_select="rerun", 
                    selection_mode="single-row",
                    use_container_width=True
                )
                
                # Detail View (The Inspector)
                st.markdown("<h5 style='color: #ab8f59; margin-top: 20px;'>DEEP INSPECTOR</h5>", unsafe_allow_html=True)
                if selection and len(selection.selection.rows) > 0:
                    row_idx = selection.selection.rows[0]
                    selected_log = df_logs.iloc[row_idx]
                    
                    c_meta, c_raw = st.columns(2)
                    with c_meta:
                        st.caption("ACTION METADATA")
                        st.write(f"**Org:** {selected_log['ORG']}")
                        st.write(f"**User:** {selected_log['USER']}")
                        st.write(f"**Asset:** {selected_log['ASSET']}")
                    
                    with c_raw:
                        st.caption("PAYLOAD (JSON)")
                        st.json(selected_log["META"])
                    
                else:
                    st.caption("Select a log entry above to audit the specific JSON payload.")
            else:
                st.info("No global logs generated yet.")
        
        conn.close()

# --- FOOTER ---
st.markdown("""<div class="footer">POWERED BY CASTELLAN PR</div>""", unsafe_allow_html=True)



























