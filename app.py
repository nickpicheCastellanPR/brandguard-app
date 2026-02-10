import streamlit as st
from PIL import Image
import os
import re
import json
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

# Initialize Logic & Database
# --- SAFE LOGIC INITIALIZATION ---
import logic # Ensure this is imported
try:
    # Try to start the engine
    logic_engine = logic.SignetLogic()
except Exception as e:
    # If it fails, STOP everything and show the error.
    st.error(f"🚨 CRITICAL STARTUP ERROR: {e}")
    st.code(f"Details: {type(e).__name__}", language="text")
    st.stop()
if 'db_init' not in st.session_state:
    db.init_db()
    st.session_state['db_init'] = True

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

# --- SESSION STATE & AUTH ---
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if 'user_id' not in st.session_state: st.session_state['user_id'] = None
if 'username' not in st.session_state: st.session_state['username'] = None

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
    score = 0
    missing = []
    
    # CASE A: STRUCTURED DATA (Created via Wizard)
    # We check what the USER actually entered, ignoring AI filler text.
    if isinstance(profile_data, dict) and 'inputs' in profile_data:
        inputs = profile_data['inputs']
        
        # 1. STRATEGY (40 pts)
        # Name & Archetype are required to exist, so we give small points for them
        if inputs.get('wiz_mission'): score += 15
        else: missing.append("Mission Statement")
            
        if inputs.get('wiz_values'): score += 15
        else: missing.append("Core Values")
        
        if inputs.get('wiz_guardrails'): score += 10
        else: missing.append("Guardrails")

        # 2. VOICE (30 pts)
        # We check the wizard sample list length if available, otherwise check input text length
        # (Session state might be cleared, so we check the 'wiz_tone' and text content implied)
        if inputs.get('wiz_tone'): score += 10
        else: missing.append("Tone Keywords")
        
        # We need to detect if samples were actually added. 
        # Since 'inputs' stores raw strings, we check if the AI text contains the "Analysis:" marker 
        # which implies samples were processed.
        final_text = profile_data.get('final_text', '')
        if "Analysis: TYPE:" in final_text or "Analysis: File" in final_text:
            score += 20
        else:
             missing.append("Writing Samples")

        # 3. VISUALS (30 pts)
        # Check if palettes are not default
        p_prim = inputs.get('palette_primary', [])
        if p_prim and p_prim != ["#24363b"]: score += 10
        
        if "Logo Variant" in final_text: score += 10
        if "Platform:" in final_text and "Analysis:" in final_text: score += 10

    # CASE B: UNSTRUCTURED (Uploaded PDF)
    # We fall back to text parsing
    else:
        text_data = str(profile_data.get('final_text', '') if isinstance(profile_data, dict) else profile_data)
        
        # Simple keywords aren't enough, check for length
        if len(text_data) > 1000: score += 50 # Volume check
        if "STRATEGY" in text_data: score += 10
        if "VOICE" in text_data: score += 10
        if "VISUALS" in text_data: score += 10
        if "social" in text_data.lower(): score += 20

    # STATUS LOGIC
    if score < 40:
        status_label = "Foundation"
        color = "#3d3d3d" 
        msg = "⚠️ <b>Low Data.</b> Add Mission, Values, and Samples to train the engine."
    elif score < 80:
        status_label = "Developing"
        color = "#ab8f59" 
        msg = "💡 <b>Refinement:</b> Engine needs more Writing Samples to capture nuance."
    else:
        status_label = "Calibrated"
        color = "#4E8065" 
        msg = "✅ <b>Ready:</b> Signet is calibrated to your brand voice."

    return {
        "score": min(score, 100), # Cap at 100
        "status_label": status_label,
        "color": color,
        "message": msg
    }

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
        # This checks if the DB is empty. If so, it lets you create the Admin.
        if db.get_user_count() == 0:
            st.warning("⚠️ SYSTEM RESET: CREATE ADMIN ACCOUNT")
            with st.form("setup_admin_hero"):
                new_admin_user = st.text_input("Admin Username")
                new_admin_pass = st.text_input("Admin Password", type="password")
                new_admin_email = st.text_input("Admin Email")
                if st.form_submit_button("Initialize System"):
                    if new_admin_user and new_admin_pass:
                        db.create_user(new_admin_user, new_admin_email, new_admin_pass, is_admin=True)
                        st.success("Admin Created! Please Log In.")
                        st.rerun()
            st.divider()
        # -------------------------------------

        login_tab, reg_tab = st.tabs(["LOGIN", "REGISTER"])
        
        with login_tab:
            l_user = st.text_input("USERNAME", key="l_user")
            l_pass = st.text_input("PASSWORD", type="password", key="l_pass")
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("ENTER", type="primary", use_container_width=True):
                # 1. CHECK CREDENTIALS
                user_data = db.check_login(l_user, l_pass) 
                
                if user_data:
                    # 2. SET SESSION STATE
                    st.session_state['authenticated'] = True
                    st.session_state['user_id'] = user_data['username'] 
                    st.session_state['username'] = user_data['username']
                    st.session_state['is_admin'] = user_data['is_admin']
                    
                    # 3. SYNC SUBSCRIPTION STATUS (The Bouncer Check)
                    user_email = user_data.get('email', '')
                    # This checks Lemon Squeezy and updates the DB
                    status = sub_manager.sync_user_status(user_data['username'], user_email)
                    st.session_state['status'] = status
                    
                    # 4. LOAD PROFILES & RERUN
                    st.session_state['profiles'] = db.get_profiles(user_data['username'])
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
        
        with reg_tab:
            r_user = st.text_input("CHOOSE USERNAME", key="r_user")
            r_pass = st.text_input("CHOOSE PASSWORD", type="password", key="r_pass")
            r_email = st.text_input("EMAIL", key="r_email") 
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("CREATE ACCOUNT", use_container_width=True):
                if db.create_user(r_user, r_email, r_pass):
                    st.success("Account created! Please log in.")
                else:
                    st.error("Username already taken.")

    st.markdown("<br><div style='text-align: center; color: #ab8f59; font-size: 0.7rem; letter-spacing: 0.2em;'>CASTELLAN PR INTERNAL TOOL</div>", unsafe_allow_html=True)
    st.stop()
    
# --- SIDEBAR ---
with st.sidebar:
    # 1. BRANDING
    if os.path.exists("Signet_Logo_Color.png"):
        st.image("Signet_Logo_Color.png", use_container_width=True)
    else:
        st.markdown('<div style="font-size: 2rem; color: #24363b; font-weight: 900; letter-spacing: 0.1em; text-align: center; margin-bottom: 20px;">SIGNET</div>', unsafe_allow_html=True)
    
    st.divider()

    # --- USER & STATUS BADGE (SECURE & POLISHED) ---
    # 1. Sanitize: Prevent XSS attacks from usernames
    raw_user = st.session_state.get('username', 'User').upper()
    user_tag = html.escape(raw_user) 
    
    status_tag = st.session_state.get('status', 'trial').upper()
    
    st.caption(f"OPERATIVE: {user_tag}")
    
    # 2. BADGE FIX (Double-Layer Color Enforcement)
    # We use a container DIV for the box, and a SPAN for the text to force the color.
    if status_tag == "ACTIVE":
        st.markdown(
            """
            <div style='background-color: #ab8f59; border: 1px solid #1b2a2e; padding: 6px 12px; border-radius: 4px; display: inline-block; margin-bottom: 10px;'>
                <span style='color: #1b2a2e !important; font-size: 0.75rem; font-weight: 800; letter-spacing: 1px; -webkit-text-fill-color: #1b2a2e;'>AGENCY TIER</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    else:
        # High Contrast: Cream Text on Dark Gray Box
        # Added '-webkit-text-fill-color' to override stubborn browser defaults
        st.markdown(
            """
            <div style='background-color: #3d3d3d; border: 1px solid #5c6b61; padding: 6px 12px; border-radius: 4px; display: inline-block; margin-bottom: 10px;'>
                <span style='color: #f5f5f0 !important; font-size: 0.75rem; font-weight: 800; letter-spacing: 1px; -webkit-text-fill-color: #f5f5f0;'>TRIAL LICENSE</span>
            </div>
            """, 
            unsafe_allow_html=True
        )
    
    # 3. ACTIVE PROFILE CALIBRATION
    profile_names = list(st.session_state.get('profiles', {}).keys())
    
    if profile_names:
        # Check if active_profile is in session state, default to first if not
        default_ix = 0
        if 'active_profile_name' in st.session_state and st.session_state['active_profile_name'] in profile_names:
             default_ix = profile_names.index(st.session_state['active_profile_name'])

        active_profile = st.selectbox("ACTIVE PROFILE", profile_names, index=default_ix)
        st.session_state['active_profile_name'] = active_profile # Persist selection
        
        current_rules = st.session_state['profiles'][active_profile]
        
        metrics = calculate_calibration_score(current_rules)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # CONFIDENCE METER
        st.markdown(f"""
            <style>
                .sb-container {{ margin-bottom: 10px; }}
                .sb-label {{ font-size: 0.7rem; font-weight: 700; color: #5c6b61; letter-spacing: 1px; margin-bottom: 4px; display: block; }}
                .sb-track {{ width: 100%; height: 6px; background: #dcdcd9; border-radius: 999px; overflow: hidden; margin-bottom: 6px; }}
                .sb-fill {{ height: 100%; width: {metrics['score']}%; background: {metrics['color']}; border-radius: 999px; transition: width 0.8s ease; }}
                .sb-status {{ font-size: 0.75rem; font-weight: 800; color: {metrics['color']}; }}
            </style>
            <div class="sb-container">
                <span class="sb-label">ENGINE CONFIDENCE</span>
                <div class="sb-track">
                    <div class="sb-fill"></div>
                </div>
                <div class="sb-status">
                     {metrics['status_label'].upper()} ({metrics['score']}%)
                </div>
            </div>
        """, unsafe_allow_html=True)
    else:
        active_profile = None
        current_rules = ""
        st.markdown("<div style='text-align:center; color:#5c6b61; font-size:0.8rem; margin-bottom:20px; font-weight:700;'>NO PROFILE LOADED</div>", unsafe_allow_html=True)

    st.divider()
    
    # 4. NAVIGATION
    # Standard Module List
    nav_options = ["DASHBOARD", "BRAND ARCHITECT", "VISUAL COMPLIANCE", "COPY EDITOR", "CONTENT GENERATOR", "SOCIAL MEDIA ASSISTANT"]
    
    # Add Admin Console only for Admins
    if st.session_state.get('is_admin', False):
        nav_options.append("ADMIN CONSOLE")
        
    # Sync navigation with session state (Safe Fallback)
    current_mode = st.session_state.get('app_mode', 'DASHBOARD')
    if current_mode not in nav_options: 
        current_mode = "DASHBOARD"

    app_mode = st.radio("MODULES", nav_options, index=nav_options.index(current_mode), label_visibility="collapsed", key="nav_selection")
    
    # Update App Mode if changed
    if app_mode != st.session_state.get('app_mode'):
        st.session_state['app_mode'] = app_mode
        st.rerun()
    
    st.divider()
    
    # 5. TRUST FOOTER
    st.markdown("""
        <div style='font-size: 0.7rem; color: #5c6b61; margin-top: 10px; margin-bottom: 20px;'>
            <strong>SECURE INSTANCE</strong><br>
            Data isolated to Castellan PR.<br>
            End-to-End Encrypted.
        </div>
    """, unsafe_allow_html=True)

    if st.button("LOGOUT", use_container_width=True):
        st.session_state['authenticated'] = False
        st.session_state['username'] = None
        st.session_state['profiles'] = {}
        st.rerun()

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
    st.title("BRAND COMMAND CENTER")
    
    # --- TRIAL STATUS BANNER ---
    # Only shows if user is NOT active. Doesn't block access, just reminds them.
    if st.session_state.get('status') != 'active':
        st.markdown("""
            <div style='background-color: #1b2a2e; padding: 15px; border-radius: 4px; margin-bottom: 25px; border: 1px solid #3d3d3d; border-left: 5px solid #ab8f59;'>
                <strong style='color: #ab8f59; letter-spacing: 1px;'>⚠️ TRIAL MODE ACTIVE</strong><br>
                <span style='color: #a0a0a0; font-size: 0.9rem;'>
                    You are operating on a restricted license. High-fidelity generation modules (Copy Editor, Visual Audit) are locked.<br>
                    <a href="https://castellanpr.lemonsqueezy.com" target="_blank" style="color: #f5f5f0; text-decoration: underline; font-weight: bold;">Initialize Agency Subscription to unlock.</a>
                </span>
            </div>
        """, unsafe_allow_html=True)
    # ---------------------------

    # 1. Determine if the user is "New" (Has no profiles yet)
    has_profiles = bool(st.session_state.get('profiles'))
    
    # 2. Render the Expander (Clean Title, No Emoji)
    with st.expander("QUICK START GUIDE: OPERATIONAL WORKFLOW", expanded=not has_profiles):
        st.markdown("""
        <div style='font-family: sans-serif; color: #f5f5f0; font-size: 0.95rem; line-height: 1.6;'>
            <p><strong>Signet</strong> acts as your brand's digital gatekeeper. Here is the workflow:</p>
            <ol style='margin-left: 20px;'>
                <li style='margin-bottom: 10px;'>
                    <strong style='color: #ab8f59;'>INITIALIZE:</strong> Create a Brand Profile using the 
                    <em>Wizard</em> (for new brands) or <em>Upload Guide</em> (for existing PDFs).
                </li>
                <li style='margin-bottom: 10px;'>
                    <strong style='color: #ab8f59;'>CALIBRATE:</strong> The engine scores your profile confidence. 
                    <em>Note:</em> You can generate content immediately, but adding more samples increases the precision of the engine's audits and copy generation.
                </li>
                <li style='margin-bottom: 10px;'>
                    <strong style='color: #ab8f59;'>EXECUTE:</strong> Once a profile is active, use the sidebar modules:
                    <ul>
                        <li><strong>Copy Editor:</strong> Paste a draft to rewrite it in your executive voice.</li>
                        <li><strong>Visual Compliance:</strong> Upload an image to check hex codes against your palette.</li>
                        <li><strong>Content Generator:</strong> Create new content from scratch.</li>
                        <li><strong>Social Media Assistant:</strong> Generate platform-specific captions and hashtags.</li>
                    </ul>
                </li>
            </ol>
        </div>
        """, unsafe_allow_html=True)   

    # --- STYLE FOR ACTION BUTTONS ---
    st.markdown("""<style>
        div[data-testid*="Column"] .stButton button {
            background: linear-gradient(135deg, #1b2a2e 0%, #111 100%) !important; border: 1px solid #3a4b50 !important; height: 250px !important; width: 100% !important; display: flex !important; flex-direction: column !important; align-items: center !important; justify-content: center !important; color: #f5f5f0 !important; border-radius: 0px !important; box-shadow: none !important; padding-top: 50px !important; position: relative !important; white-space: pre-wrap !important;
        }
        div[data-testid*="Column"] .stButton button:hover { transform: translateY(-5px) !important; border-color: #ab8f59 !important; box-shadow: 0 10px 30px rgba(0,0,0,0.4) !important; color: #ab8f59 !important; }
        div[data-testid*="Column"] .stButton button p { font-size: 1rem !important; font-weight: 700 !important; letter-spacing: 0.1em; }
        div[data-testid*="Column"]:nth-of-type(1) .stButton button::before { content: ''; position: absolute; top: 40px; width: 40px; height: 40px; border: 2px solid #ab8f59; box-shadow: 5px 5px 0px #5c6b61; }
        div[data-testid*="Column"]:nth-of-type(2) .stButton button::before { content: ''; position: absolute; top: 40px; width: 30px; height: 40px; border: 2px solid #ab8f59; background: linear-gradient(to bottom, transparent 20%, #ab8f59 20%, #ab8f59 25%, transparent 25%, transparent 40%, #ab8f59 40%, #ab8f59 45%, transparent 45%); }
        div[data-testid*="Column"]:nth-of-type(3) .stButton button::before { content: ''; position: absolute; top: 40px; width: 40px; height: 40px; border: 2px solid #ab8f59; border-radius: 50%; background: radial-gradient(circle, #5c6b61 20%, transparent 21%); }
    </style>""", unsafe_allow_html=True)

    # --- ACTION BUTTONS ---
    c1, c2, c3 = st.columns(3)
    with c1: st.button("\nCREATE PROFILE\nArchitect a new brand identity", on_click=nav_to, args=("BRAND ARCHITECT",))
    with c2: 
        if st.button("\nUPLOAD GUIDE\nIngest existing PDF rules"):
            st.session_state['dashboard_upload_open'] = True
            st.rerun()
    with c3:
        if st.button("\nLOAD DEMO\nLoad Castellan sample data"):
             demo_data = {
                 "final_text": "1. STRATEGY: Mission: Architecting Strategic Narratives... Archetype: The Ruler.\n2. VOICE: Professional...",
                 "inputs": {
                     "wiz_name": "Castellan PR", "wiz_archetype": "The Ruler", "wiz_tone": "Professional, Direct",
                     "wiz_mission": "Architecting narratives.", "wiz_values": "Precision, Power.",
                     "wiz_guardrails": "No fluff.", "palette_primary": ["#24363b"], "palette_secondary": ["#ab8f59"], "palette_accent": ["#f5f5f0"]
                 }
             }
             st.session_state['profiles']["Castellan PR (Demo)"] = demo_data
             db.save_profile(st.session_state['user_id'], "Castellan PR (Demo)", demo_data)
             st.rerun()

    # --- UPLOAD SECTION (Conditional) ---
    if st.session_state['dashboard_upload_open']:
        with st.container():
            st.markdown("""<div class="dashboard-card" style="border-left: 4px solid #f5f5f0;"><h3 style="color: #f5f5f0;">UPLOAD BRAND GUIDE (PDF)</h3><p style="color: #a0a0a0;">The engine will extract Strategy, Voice, and Visual rules automatically.</p></div>""", unsafe_allow_html=True)
            dash_pdf = st.file_uploader("SELECT PDF", type=["pdf"], key="dash_pdf_uploader")
            col_sub, col_can = st.columns([1, 1])
            with col_sub:
                if dash_pdf and st.button("PROCESS & INGEST", type="primary"):
                    with st.spinner("ANALYZING PDF STRUCTURE..."):
                        try:
                            # 1. Extract Text
                            raw_text = logic.extract_text_from_pdf(dash_pdf)
                            
                            # 2. Get Structured Data (The New Function)
                            extracted_data = logic.generate_brand_rules_from_pdf(raw_text)
                            
                            # 3. Create the Profile Object (Matching the Wizard Structure)
                            # map the AI's JSON directly to 'inputs' dictionary
                            new_profile = {
                                "inputs": {
                                    "wiz_name": extracted_data.get("wiz_name", "New Brand"),
                                    "wiz_archetype": extracted_data.get("wiz_archetype", "The Sage"),
                                    "wiz_tone": extracted_data.get("wiz_tone", "Professional"),
                                    "wiz_mission": extracted_data.get("wiz_mission", ""),
                                    "wiz_values": extracted_data.get("wiz_values", ""),
                                    "wiz_guardrails": extracted_data.get("wiz_guardrails", ""),
                                    "palette_primary": extracted_data.get("palette_primary", ["#24363b"]),
                                    "palette_secondary": extracted_data.get("palette_secondary", ["#ab8f59"]),
                                    "palette_accent": ["#f5f5f0"] # Default
                                },
                                # generate the "Master Rules" text for the engine to read
                                "final_text": f"1. STRATEGY\nMission: {extracted_data.get('wiz_mission')}\nValues: {extracted_data.get('wiz_values')}\n\n2. VOICE\nTone: {extracted_data.get('wiz_tone')}\nSample: {extracted_data.get('writing_sample')}"
                            }
                            
                            # 4. Save
                            profile_name = f"{extracted_data.get('wiz_name')} (PDF)"
                            db.save_profile(st.session_state['user_id'], profile_name, new_profile)
                            st.session_state['profiles'][profile_name] = new_profile
                            
                            st.success(f"SUCCESS: {profile_name} ingested.")
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"Error: {e}")
            with col_can:
                if st.button("CANCEL"):
                    st.session_state['dashboard_upload_open'] = False
                    st.rerun()
        st.divider()

    # --- THE LIBRARY GRID (ALWAYS VISIBLE) ---
    st.divider()
    st.markdown("### BRAND SIGNAL LIBRARY")
    
    profiles = db.get_profiles(st.session_state['user_id'])
    
    if not profiles:
        st.info("No active signals found. Initialize a profile above.")
    else:
        # Sort keys to ensure consistent order
        profile_names = sorted(list(profiles.keys()))
        
# Grid Logic
        for i in range(0, len(profile_names), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(profile_names):
                    raw_p_name = profile_names[i+j]
                    
                    # 🛡️ SECURITY: Sanitize the name for display to prevent HTML injection
                    p_name = html.escape(raw_p_name)
                    
                    # Use raw name for database lookup
                    p_data = profiles[raw_p_name] 
                    
                    with cols[j]:
                        with st.container():
                            # START CARD
                            st.markdown(f"<div class='dashboard-card'>", unsafe_allow_html=True)
                            
                            # HEADER (Now Safe)
                            st.markdown(f"#### {p_name}")
                            
                            # METER
                            metrics = calculate_calibration_score(p_data)
                            st.markdown(f"""
                                <style>
                                    .metric-container {{ font-family: 'Source Sans Pro', sans-serif; margin-bottom: 15px; }}
                                    .metric-header {{ display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 4px; }}
                                    .metric-label {{ font-size: 0.7rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; color: #5c6b61; }}
                                    .metric-value {{ font-size: 0.85rem; font-weight: 800; color: {metrics['color']}; }}
                                    .progress-track {{ width: 100%; height: 5px; background-color: #dcdcd9; border-radius: 999px; overflow: hidden; }}
                                    .progress-fill {{ height: 100%; width: {metrics['score']}%; background-color: {metrics['color']}; border-radius: 999px; transition: width 0.8s ease; }}
                                    .metric-hint {{ font-size: 0.75rem; color: #5c6b61; margin-top: 6px; font-style: italic; opacity: 0.9; min-height: 2.4em; }}
                                </style>
                                <div class="metric-container">
                                    <div class="metric-header">
                                        <span class="metric-label">{metrics['status_label']}</span>
                                        <span class="metric-value">{metrics['score']}%</span>
                                    </div>
                                    <div class="progress-track">
                                        <div class="progress-fill"></div>
                                    </div>
                                    <div class="metric-hint">{metrics['message']}</div>
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # ACTION BUTTON (Uses raw_p_name for logic key)
                            st.button("ACTIVATE SIGNAL", 
                                      key=f"open_{raw_p_name}", 
                                      on_click=activate_profile, 
                                      args=(raw_p_name,), 
                                      use_container_width=True)

                            st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<br><div style='background-color: rgba(36, 54, 59, 0.5); border-top: 1px solid #3a4b50; padding: 20px; text-align: center; border-radius: 4px;'><h3 style='color: #ab8f59; margin-bottom: 10px; font-size: 1rem; letter-spacing: 0.1em;'>INTELLIGENT BRAND GOVERNANCE</h3><p style='color: #a0a0a0; font-family: sans-serif; font-size: 0.9rem; line-height: 1.6; max-width: 800px; margin: 0 auto;'>Signet is a proprietary engine...</p></div>", unsafe_allow_html=True)
# 2. VISUAL COMPLIANCE
elif app_mode == "VISUAL COMPLIANCE":
    st.title("VISUAL COMPLIANCE AUDIT")

    # --- AGENCY TIER CHECK ---
    if st.session_state.get('status') != 'active':
        show_paywall()
    # -------------------------
    
    if not active_profile: st.warning("NO PROFILE SELECTED.")
    else:
        uploaded_file = st.file_uploader("UPLOAD ASSET", type=["jpg", "png"])
        if uploaded_file and st.button("RUN AUDIT", type="primary"):
            with st.spinner("ANALYZING PIXELS..."):
                prof_text = current_rules['final_text'] if isinstance(current_rules, dict) else current_rules
                result = logic.run_visual_audit(Image.open(uploaded_file), prof_text)
                st.markdown(result)

# 3. COPY EDITOR
elif app_mode == "COPY EDITOR":
    st.title("COPY EDITOR")
    
    # --- AGENCY TIER CHECK ---
    # Security Gate: Ensure only active subscribers can access this feature
    if st.session_state.get('status', 'trial').lower() != 'active':
        show_paywall()
    # -------------------------
    
    if not active_profile: 
        st.warning("NO PROFILE SELECTED.")
    else:
        c1, c2 = st.columns([2, 1])
        
        with c1: 
            text_input = st.text_area("DRAFT TEXT", height=300, placeholder="PASTE DRAFT COPY HERE...")
            
            # Context Inputs
            cc1, cc2, cc3 = st.columns(3)
            with cc1: 
                content_type = st.selectbox("CONTENT TYPE", ["Internal Email", "Press Release", "Blog Post", "Executive Memo", "Website Copy"])
            with cc2: 
                sender = st.text_input("SENDER / VOICE", placeholder="e.g. CEO, Support Team")
            with cc3: 
                audience = st.text_input("TARGET AUDIENCE", placeholder="e.g. Investors, Employees")
                
        with c2: 
            # Profile Card (Safe to use html here as active_profile is internal, but escaping is good practice)
            safe_profile_name = html.escape(active_profile)
            st.markdown(f"""<div class="dashboard-card"><h4>TARGET VOICE</h4><h3>{safe_profile_name}</h3></div>""", unsafe_allow_html=True)
        
        if st.button("ANALYZE & REWRITE", type="primary"):
            if text_input:
                with st.spinner("REWRITING..."):
                    # Prepare Data
                    prof_text = current_rules['final_text'] if isinstance(current_rules, dict) else current_rules
                    context_wrapper = f"CONTEXT: Type: {content_type}, Sender: {sender}, Audience: {audience}\nDRAFT CONTENT: {text_input}"
                    
                    # AI Processing
                    result = logic.run_copy_editor(context_wrapper, prof_text)
                    
                    st.divider()
                    st.subheader("REWRITTEN DRAFT")
                    
                    # 🛡️ SECURITY FIX: 
                    # We remove 'unsafe_allow_html=True'.
                    # This renders Markdown (Bold, Italic, Lists) but ESCAPES any <script> tags.
                    st.markdown(result)
                    
                    # Helper for copying
                    st.text_area("COPYABLE VERSION", value=result, height=300)
            else:
                st.warning("Please enter text to rewrite.")

# 4. CONTENT GENERATOR
elif app_mode == "CONTENT GENERATOR":
    st.title("CONTENT GENERATOR")

    # --- AGENCY TIER CHECK ---
    if st.session_state.get('status') != 'active':
        show_paywall()
    # -------------------------
    
    c1, c2 = st.columns(2)
    with c1: format_type = st.selectbox("TYPE", ["Press Release", "Email", "LinkedIn Post", "Article"])
    with c2: topic = st.text_input("TOPIC")
    audience = st.text_input("TARGET AUDIENCE", placeholder="e.g. Investors, Gen Z, Current Customers")
    key_points = st.text_area("KEY POINTS", height=150, placeholder="- Key point 1\n- Key point 2")
    if st.button("GENERATE DRAFT", type="primary"):
        with st.spinner("DRAFTING..."):
            prof_text = current_rules['final_text'] if isinstance(current_rules, dict) else current_rules
            full_prompt_topic = f"{topic} (Audience: {audience})"
            result = logic.run_content_generator(full_prompt_topic, format_type, key_points, prof_text)
            st.markdown(result)

# 5. SOCIAL MEDIA ASSISTANT
elif app_mode == "SOCIAL MEDIA ASSISTANT":
    st.title("SOCIAL MEDIA ASSISTANT")

    # --- AGENCY TIER CHECK ---
    if st.session_state.get('status') != 'active':
        show_paywall()
    # -------------------------
    
    if not active_profile: st.warning("NO PROFILE SELECTED.")
    else:
        c1, c2 = st.columns([1, 1])
        with c1:
            platform = st.selectbox("PLATFORM", ["LinkedIn", "Instagram", "X (Twitter)", "TikTok", "Facebook"])
            topic_social = st.text_area("TOPIC / CAPTION INTENT", height=100, placeholder="What is this post about?")
        with c2:
            social_img = st.file_uploader("UPLOAD VISUAL (Optional)", type=["jpg", "png"])
            
        if st.button("GENERATE POST", type="primary"):
            with st.spinner("ANALYZING & DRAFTING..."):
                prof_text = current_rules['final_text'] if isinstance(current_rules, dict) else current_rules
                img_context = ""
                if social_img:
                    desc = logic.analyze_social_post(Image.open(social_img))
                    img_context = f"IMAGE CONTEXT: The post includes an image described as: {desc}"
                
                social_prompt = f"""
                TASK: Write a social media post for {platform}.
                TOPIC: {topic_social}
                {img_context}
                INSTRUCTIONS:
                1. Apply the 'Social Media' rules from the Brand Profile.
                2. Use the 'High Performing Posts' in the profile as a benchmark for tone/length.
                3. Adhere to platform best practices for {platform} (hashtags, emoji usage, length).
                4. Provide a 'Rationale' section explaining why you chose this angle.
                """
                result = logic.run_content_generator(social_prompt, f"{platform} Post", "See prompt", prof_text)
                st.markdown(result)

# 6. BRAND ARCHITECT
elif app_mode == "BRAND ARCHITECT":
    st.title("BRAND ARCHITECT")
    def extract_and_map_pdf():
        # This runs BEFORE the page redraws
        uploaded_file = st.session_state.get('arch_pdf_uploader')
        if uploaded_file:
            try:
                raw_text = logic_engine.extract_text_from_pdf(uploaded_file)
                data = logic_engine.generate_brand_rules_from_pdf(raw_text)
                
                # Update Session State safely
                st.session_state['wiz_name'] = data.get('wiz_name', '')
                st.session_state['wiz_tone'] = data.get('wiz_tone', '')
                st.session_state['wiz_mission'] = data.get('wiz_mission', '')
                st.session_state['wiz_values'] = data.get('wiz_values', '')
                st.session_state['wiz_guardrails'] = data.get('wiz_guardrails', '')
                
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
            st.text_input("BRAND NAME", key="wiz_name")
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
            # Dynamic Info Card (Appears below the columns)
            if selected_arch:
                info = ARCHETYPE_INFO[selected_arch]
                st.markdown(f"""
                    <div style="background-color: rgba(36, 54, 59, 0.05); border-left: 3px solid #ab8f59; padding: 15px; margin-top: 10px; margin-bottom: 20px; border-radius: 0 4px 4px 0;">
                        <strong style="color: #24363b; display: block; margin-bottom: 4px;">THE VIBE:</strong>
                        <span style="color: #5c6b61; font-size: 0.9rem;">{info['desc']}</span>
                        <div style="margin-top: 8px; font-size: 0.8rem; color: #888;">
                            <em>Real World Examples: {info['examples']}</em>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            with c2: st.text_input("TONE KEYWORDS", placeholder="e.g. Witty, Professional, Bold", key="wiz_tone")
            st.text_area("MISSION STATEMENT", key="wiz_mission")
            st.text_area("CORE VALUES", placeholder="e.g. Transparency, Innovation, Community", key="wiz_values")
            st.text_area("BRAND GUARDRAILS (DO'S & DON'TS)", placeholder="e.g. Don't use emojis.", key="wiz_guardrails")
            
        with st.expander("2. VOICE & CALIBRATION"):
            st.caption("Upload existing content to train the engine on your voice.")
            st.selectbox("CONTENT TYPE", ["Internal Email", "Executive Memo", "Press Release", "Article/Blog", "Social Post", "Website Copy", "Other"], key="wiz_sample_type")
            v_tab1, v_tab2 = st.tabs(["PASTE TEXT", "UPLOAD FILE"])
            with v_tab1: st.text_area("PASTE TEXT HERE", key="wiz_temp_text", height=150)
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

        with st.expander("3. SOCIAL MEDIA"):
            st.caption("Upload screenshots of high-performing posts.")
            st.selectbox("PLATFORM", ["LinkedIn", "Instagram", "X (Twitter)", "Facebook", "Other"], key="wiz_social_platform")
            s_key = f"social_up_{st.session_state['social_uploader_key']}"
            st.file_uploader("UPLOAD SCREENSHOT", type=["png", "jpg"], key=s_key)
            st.button("ADD SOCIAL SAMPLE", on_click=add_social_callback)
            if st.session_state['wiz_social_list']:
                st.divider()
                st.markdown(f"**SOCIAL BUFFER: {len(st.session_state['wiz_social_list'])} IMAGES**")
                for i, item in enumerate(st.session_state['wiz_social_list']):
                    c1, c2 = st.columns([4,1])
                    with c1: st.caption(f"> {item['platform']} - {item['file'].name}")
                    with c2: 
                        if st.button("REMOVE", key=f"del_social_{i}", type="secondary"):
                            st.session_state['wiz_social_list'].pop(i)
                            st.rerun()
            
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
                        logo_desc_list = [f"Logo Variant ({item['file'].name}): {logic.describe_logo(Image.open(item['file']))}" for item in st.session_state['wiz_logo_list']]
                        logo_summary = "\n".join(logo_desc_list) if logo_desc_list else "None provided."
                        social_desc_list = [f"Platform: {item['platform']}. Analysis: {logic.analyze_social_post(Image.open(item['file']))}" for item in st.session_state['wiz_social_list']]
                        social_summary = "\n".join(social_desc_list) if social_desc_list else "None provided."
                        all_samples = "\n---\n".join(st.session_state['wiz_samples_list'])
                        
                        prompt = f"""
                        SYSTEM INSTRUCTION: Generate a comprehensive brand profile strictly following the numbered format below.
                        1. STRATEGY: Brand: {st.session_state.wiz_name}. Archetype: {st.session_state.wiz_archetype}. Mission: {st.session_state.wiz_mission}. Values: {st.session_state.wiz_values}
                        2. VOICE: Tone: {st.session_state.wiz_tone}. Analysis: {all_samples}
                        3. VISUALS: Palette: {palette_str}. Logo: {logo_summary}. Social: {social_summary}
                        4. GUARDRAILS: {st.session_state.wiz_guardrails}
                        """
                        
                        final_text_out = logic.generate_brand_rules(prompt)
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
                                "palette_accent": st.session_state['palette_accent']
                            }
                        }
                        
                        profile_name = f"{st.session_state.wiz_name} (Gen)"
                        st.session_state['profiles'][profile_name] = profile_data
                        
                        # SAVE TO DB
                        db.save_profile(st.session_state['user_id'], profile_name, profile_data)
                        
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
    if st.session_state['profiles']:
        p_keys = list(st.session_state['profiles'].keys())
        default_ix = 0
        if st.session_state.get('active_profile') in p_keys:
            default_ix = p_keys.index(st.session_state['active_profile'])
        target = st.selectbox("PROFILE", p_keys, index=default_ix)
        profile_obj = st.session_state['profiles'][target]
        
        is_structured = isinstance(profile_obj, dict) and "inputs" in profile_obj
        final_text_view = profile_obj['final_text'] if is_structured else profile_obj
        
        html_data = convert_to_html_brand_card(target, final_text_view)
        st.download_button(label="📄 DOWNLOAD BRAND KIT (HTML)", data=html_data, file_name=f"{target.replace(' ', '_')}_BrandKit.html", mime="text/html", use_container_width=True)
        
        st.divider()
        
        if is_structured:
            inputs = profile_obj['inputs']
            
            with st.expander("1. STRATEGY", expanded=True):
                new_name = st.text_input("BRAND NAME", inputs['wiz_name'])
                idx = ARCHETYPES.index(inputs['wiz_archetype']) if inputs['wiz_archetype'] in ARCHETYPES else 0
                def format_archetype_edit(option):
                    if option in ARCHETYPE_INFO:
                        return f"{option} | {ARCHETYPE_INFO[option]['tagline']}"
                    return option

                idx = ARCHETYPES.index(inputs['wiz_archetype']) if inputs['wiz_archetype'] in ARCHETYPES else 0
            
                new_arch = st.selectbox(
                    "ARCHETYPE", 
                    ARCHETYPES, 
                    index=idx,
                    format_func=format_archetype_edit
                )
                # Info Card for Editor
                if new_arch:
                    info = ARCHETYPE_INFO[new_arch]
                    st.markdown(f"""
                        <div style="background-color: rgba(36, 54, 59, 0.05); border-left: 3px solid #ab8f59; padding: 10px; margin-top: 5px; margin-bottom: 15px;">
                            <span style="color: #5c6b61; font-size: 0.85rem;">{info['desc']}</span>
                        </div>
                    """, unsafe_allow_html=True)
                new_mission = st.text_area("MISSION", inputs['wiz_mission'])
                new_values = st.text_area("VALUES", inputs['wiz_values'])
            
            with st.expander("2. VOICE"):
                new_tone = st.text_input("TONE KEYWORDS", inputs['wiz_tone'])
            
            with st.expander("3. GUARDRAILS"):
                new_guard = st.text_area("DO'S & DON'TS", inputs['wiz_guardrails'])
            
            if st.button("SAVE CHANGES & REGENERATE PROFILE"):
                profile_obj['inputs']['wiz_name'] = new_name
                profile_obj['inputs']['wiz_archetype'] = new_arch
                profile_obj['inputs']['wiz_mission'] = new_mission
                profile_obj['inputs']['wiz_values'] = new_values
                profile_obj['inputs']['wiz_tone'] = new_tone
                profile_obj['inputs']['wiz_guardrails'] = new_guard
                
                p_p = ", ".join(inputs['palette_primary'])
                p_s = ", ".join(inputs['palette_secondary'])
                
                new_text = f"""
                1. STRATEGY
                - Brand: {new_name}
                - Archetype: {new_arch}
                - Mission: {new_mission}
                - Values: {new_values}
                
                2. VOICE
                - Tone Keywords: {new_tone}
                
                3. VISUALS
                - Primary: {p_p}
                - Secondary: {p_s}
                
                4. GUARDRAILS
                - {new_guard}
                """
                profile_obj['final_text'] = new_text
                st.session_state['profiles'][target] = profile_obj
                
                # UPDATE DB
                db.save_profile(st.session_state['user_id'], target, profile_obj)
                
                st.success("UPDATED & REBUILT")
                st.rerun()

        else:
            st.warning("This profile was created from a PDF/Raw Text. Structured editing is unavailable.")
            new_raw = st.text_area("EDIT RAW TEXT", final_text_view, height=500)
            if st.button("SAVE RAW CHANGES"):
                st.session_state['profiles'][target] = new_raw
                db.save_profile(st.session_state['user_id'], target, new_raw)
                st.success("SAVED")

        if st.button("DELETE PROFILE"): 
            del st.session_state['profiles'][target]
            db.delete_profile(st.session_state['user_id'], target)
            st.rerun()
# --- ADMIN DASHBOARD (CASTELLAN STYLED) ---
if st.session_state.get("authenticated") and st.session_state.get("is_admin"):
    st.markdown("---")
    with st.expander("Show Admin Dashboard 🛡️"):
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

        st.markdown("<h3 style='color: #ab8f59; letter-spacing: 0.1em;'>SYSTEM OVERVIEW</h3>", unsafe_allow_html=True)
        
        # 1. METRICS ROW
        users = db.get_all_users()
        logs = db.get_all_logs()
        
        m1, m2, m3 = st.columns(3)
        with m1: st.metric("TOTAL OPERATIVES", len(users) if users else 0)
        with m2: st.metric("TOTAL GENERATIONS", len(logs) if logs else 0)
        with m3: st.metric("SYSTEM STATUS", "ONLINE", delta_color="normal")
        
        st.markdown("<br>", unsafe_allow_html=True)

        # 2. TABS FOR DATA
        tab_users, tab_logs = st.tabs(["OPERATIVE DATABASE", "GENERATION LOGS"])
        
        import pandas as pd

        with tab_users:
            if users:
                # SECURITY NOTE: st.dataframe is 'Safe by Design'. It renders scripts as text, preventing XSS.
                df_users = pd.DataFrame(users, columns=["USERNAME", "EMAIL", "IS ADMIN", "SUB STATUS", "CREATED AT"])
                # Clean up the view
                df_users['IS ADMIN'] = df_users['IS ADMIN'].apply(lambda x: "🛡️ ADMIN" if x else "USER")
                st.dataframe(df_users, use_container_width=True, hide_index=True)
            else:
                st.info("No users found.")

        with tab_logs:
            if logs:
                # FIX: Matched columns to the 4 returned by the Database (Username, Time, Inputs, Cost)
                # This prevents the "Shape mismatch" crash.
                df_logs = pd.DataFrame(logs, columns=["OPERATIVE", "TIMESTAMP", "INPUTS (JSON)", "EST. COST"])
                
                # Filter for readability
                display_cols = ["TIMESTAMP", "OPERATIVE", "EST. COST"]
                selection = st.dataframe(
                    df_logs[display_cols], 
                    use_container_width=True, 
                    hide_index=True,
                    on_select="rerun", 
                    selection_mode="single-row"
                )
                
                # Detail View (The Inspector)
                st.markdown("<h5 style='color: #ab8f59; margin-top: 20px;'>LOG INSPECTOR</h5>", unsafe_allow_html=True)
                if selection and len(selection.selection.rows) > 0:
                    row_idx = selection.selection.rows[0]
                    selected_log = df_logs.iloc[row_idx]
                    
                    st.caption("INPUT DATA")
                    st.json(selected_log["INPUTS (JSON)"])
                    
                else:
                    st.caption("Select a log entry above to inspect payload.")
            else:
                st.info("No logs generated yet.")
# --- FOOTER ---
st.markdown("""<div class="footer">POWERED BY CASTELLAN PR // INTERNAL USE ONLY</div>""", unsafe_allow_html=True)




































