import streamlit as st
from PIL import Image
import os
import re
import json
from logic import SignetLogic

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

# Initialize Logic
logic = SignetLogic()

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
    
    /* Fix Dropdown Menu Items */
    ul[data-baseweb="menu"] li {
        color: #FFFFFF !important;
        background-color: var(--c-teal-dark) !important;
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

# --- SESSION STATE ---
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'check_count' not in st.session_state: st.session_state['check_count'] = 0

# NAV STATE
if 'nav_selection' not in st.session_state: st.session_state['nav_selection'] = "DASHBOARD"

# WIZARD STATE LISTS
if 'wiz_samples_list' not in st.session_state: st.session_state['wiz_samples_list'] = []
if 'wiz_social_list' not in st.session_state: st.session_state['wiz_social_list'] = [] 
if 'wiz_logo_list' not in st.session_state: st.session_state['wiz_logo_list'] = []     
if 'dashboard_upload_open' not in st.session_state: st.session_state['dashboard_upload_open'] = False 

# DYNAMIC KEYS FOR UPLOADERS
if 'file_uploader_key' not in st.session_state: st.session_state['file_uploader_key'] = 0 
if 'social_uploader_key' not in st.session_state: st.session_state['social_uploader_key'] = 1000
if 'logo_uploader_key' not in st.session_state: st.session_state['logo_uploader_key'] = 2000

if 'profiles' not in st.session_state:
    st.session_state['profiles'] = {}

MAX_CHECKS = 50

ARCHETYPES = [
    "The Ruler", "The Creator", "The Sage", "The Innocent", 
    "The Outlaw", "The Magician", "The Hero", "The Lover", 
    "The Jester", "The Everyman", "The Caregiver", "The Explorer"
]

# --- HELPER FUNCTIONS ---
def nav_to(page_name):
    st.session_state['nav_selection'] = page_name

def calculate_calibration_score(profile_data):
    score = 0
    missing = []
    if "STRATEGY" in profile_data: score += 10
    if "VOICE" in profile_data: score += 10
    if "VISUALS" in profile_data: score += 10
    if "LOGO RULES" in profile_data: score += 10
    if "TYPOGRAPHY" in profile_data: score += 10
    if "Style Signature" in profile_data: score += 25
    else: missing.append("Voice Samples")
    if "SOCIAL MEDIA" in profile_data: score += 25
    else: missing.append("Social Screenshots")
    return score, missing

# --- PERSISTENCE FUNCTIONS ---
DRAFT_FILE = "signet_draft.json"

def save_wizard_draft():
    """Saves current wizard state variables to a local JSON."""
    data = {
        "wiz_name": st.session_state.get("wiz_name", ""),
        "wiz_archetype": st.session_state.get("wiz_archetype", ""),
        "wiz_tone": st.session_state.get("wiz_tone", ""),
        "wiz_mission": st.session_state.get("wiz_mission", ""),
        "wiz_values": st.session_state.get("wiz_values", ""),
        "wiz_guardrails": st.session_state.get("wiz_guardrails", ""),
        "wiz_samples_list": st.session_state.get("wiz_samples_list", [])
    }
    with open(DRAFT_FILE, "w") as f:
        json.dump(data, f)
    st.toast("Draft Saved Locally", icon="💾")

def load_wizard_draft():
    """Loads wizard state variables from local JSON."""
    if os.path.exists(DRAFT_FILE):
        with open(DRAFT_FILE, "r") as f:
            data = json.load(f)
            st.session_state["wiz_name"] = data.get("wiz_name", "")
            st.session_state["wiz_archetype"] = data.get("wiz_archetype", None)
            st.session_state["wiz_tone"] = data.get("wiz_tone", "")
            st.session_state["wiz_mission"] = data.get("wiz_mission", "")
            st.session_state["wiz_values"] = data.get("wiz_values", "")
            st.session_state["wiz_guardrails"] = data.get("wiz_guardrails", "")
            st.session_state["wiz_samples_list"] = data.get("wiz_samples_list", [])
        st.toast("Draft Loaded", icon="📂")
        st.rerun()
    else:
        st.error("No draft file found.")

# --- EXPORT TO HTML FUNCTION (NEW) ---
def convert_to_html_brand_card(brand_name, content):
    """
    Converts the raw markdown/text profile into a styled HTML Brand Card.
    This solves the "asterisks are ugly" problem without needing a PDF library.
    """
    # 1. Simple Markdown cleanup regex
    # Convert **Text** to <b>Text</b>
    html_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    # Convert * Bullet points to cleaner HTML bullets if strictly formatted, 
    # but for safety we will just preserve newlines and use bullets visually.
    
    # 2. Inject CSS for the "Castellan" Look
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: 'Helvetica Neue', Arial, sans-serif; background-color: #f5f5f0; color: #24363b; padding: 40px; line-height: 1.6; }}
            .brand-card {{ max-width: 800px; margin: 0 auto; background: white; padding: 50px; border: 1px solid #ab8f59; box-shadow: 0 10px 30px rgba(0,0,0,0.1); }}
            h1 {{ color: #24363b; text-transform: uppercase; border-bottom: 2px solid #ab8f59; padding-bottom: 10px; margin-bottom: 30px; letter-spacing: 0.1em; }}
            h2 {{ color: #ab8f59; font-size: 1.2rem; margin-top: 30px; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 0.05em; }}
            strong {{ color: #1b2a2e; }}
            .footer {{ margin-top: 50px; font-size: 0.8rem; color: #ab8f59; text-align: center; border-top: 1px solid #eee; padding-top: 20px; }}
            pre {{ white-space: pre-wrap; font-family: inherit; margin: 0; }}
        </style>
    </head>
    <body>
        <div class="brand-card">
            <h1>{brand_name} / BRAND PROFILE</h1>
            <pre>{html_content}</pre>
            <div class="footer">GENER
